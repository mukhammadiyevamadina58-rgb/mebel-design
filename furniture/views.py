import json
import random
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import UserProfile, FurnitureProject, MaterialTexture, MdfColor
from .forms import FurnitureProjectForm, MaterialTextureForm, MdfColorForm
from .utils import send_telegram_message
from .models import Project, Material, ProjectImage, MdfColor, Review, ProjectReview

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


# 1. Tizimga kirish (Login)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'userprofile') and user.userprofile.role == 'maker':
                messages.error(request, "Mebelchilar uchun alohida kirish sahifasi mavjud!")
                return redirect('maker_login')
            
            login(request, user)
            
            # Mijoz tizimga kirishi bilan to'g'ridan-to'g'ri Tayyor loyihalar sahifasiga yo'naltiriladi:
            return redirect('client_projects')
        else:
            messages.error(request, "Login yoki parol xato!")
            
    return render(request, 'furniture/login.html')



def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        username = request.POST.get('username')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Xatolik: Parollar bir xil emas!')
            return render(request, 'furniture/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Xatolik: Bu username band, boshqa nom tanlang!')
            return render(request, 'furniture/register.html')

        if phone:
            clean_phone = phone.replace('+', '').strip()
            if UserProfile.objects.filter(phone__icontains=clean_phone[-9:]).exists():
                messages.error(request, "Xatolik: Bu telefon raqam allaqachon ro'yxatdan o'tgan!")
                return render(request, 'furniture/register.html')

        user = User.objects.create_user(
            username=username, 
            password=password, 
            first_name=name
        )
        
        code = str(random.randint(100000, 999999))

        profile = UserProfile.objects.create(
            user=user, 
            phone=phone,
            role='client',
            verification_code=code,
            is_verified=False
        )

        request.session['pending_user_id'] = user.id

        if getattr(profile, 'telegram_id', None):
            send_telegram_message(
                profile.telegram_id, 
                f"Sizning tasdiqlash kodingiz: {code}\nKodni saytga kiriting."
            )
            messages.info(request, "Tasdiqlash kodi Telegram botingizga yuborildi.")
        else:
            messages.warning(
                request, 
                "Tasdiqlash kodini olish uchun iltimos Telegram botimizga kiring!"
            )

        return redirect('verify_code')

    return render(request, 'furniture/register.html')



def maker_login_view(request):
    # Agar foydalanuvchi sahifaga shunchaki kirsa (GET so'rovi),
    # avvalgi eski seansni tozalaymiz (har safar login/parol so'rashi uchun):
    if request.method == 'GET':
        logout(request)
        return render(request, 'furniture/login.html')

    # Login va parol kiritilib, tugma bosilganda (POST so'rovi):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Mebelchi yoki admin ekanligini tekshiramiz
            is_maker = hasattr(user, 'userprofile') and user.userprofile.role == 'maker'
            
            if user.is_superuser or user.is_staff or is_maker:
                login(request, user)
                # Muvaffaqiyatli kirsa, SRAZU create_project sahifasiga yo'naltiramiz:
                return redirect('create_project')
            else:
                messages.error(request, "Xatolik: Bu sahifa faqat mebelchilar uchun!")
        else:
            messages.error(request, "Login yoki parol xato!")
            
    return render(request, 'furniture/login.html')








def verify_code_view(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
        profile = user.userprofile
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return redirect('register')

    if request.method == 'POST':
        input_code = request.POST.get('code')

        if profile.verification_code and profile.verification_code == input_code:
            profile.is_verified = True
            profile.verification_code = None  # Kod bir marta ishlatilgach o'chiriladi
            profile.save()

            # Tizimga muvaffaqiyatli kirgizamiz
            login(request, user)
            del request.session['pending_user_id']

            messages.success(request, f"Xush kelibsiz, {user.first_name}! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.")
            return redirect('client_projects')
        else:
            messages.error(request, "Xatolik: Tasdiqlash kodi xato!")

    context = {
        'phone': profile.phone,
        'bot_username': 'Master_MebelBot'  # Botning username-i
    }
    return render(request, 'furniture/verify_code.html', context)


@login_required
def mebelchi_dashboard(request):
    # Faqat tizimga kirgan mebelchining loyihalarini olamiz
    projects = FurnitureProject.objects.filter(user=request.user)
    
    context = {
        'projects': projects
    }
    # Agar shablon 'seller' papkasi ichida bo'lsa:
    return render(request, 'furniture/seller/mebelchi_dashboard.html', context)

TELEGRAM_BOT_TOKEN = "8761510532:AAH-jWXX7gIXXh1aB6_OCzXciHJzHc5AMms"  # Tokeningiz to'g'ri yozildi

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram yuborishda xatolik: {e}")


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                text = message.get('text', '')
                contact = message.get('contact', None)

                # 1. /start buyrug'i
                if text == '/start':
                    send_telegram_message(
                        chat_id,
                        "Assalomu alaykum! MebelDesign botiga xush kelibsiz.\n"
                        "Telefon raqamingizni ulashish uchun pastdagi tugmani bosing:",
                        reply_markup={
                            'keyboard': [[{
                                'text': '📞 Telefon raqamni ulashish',
                                'request_contact': True,
                            }]],
                            'resize_keyboard': True,
                            'one_time_keyboard': True,
                        },
                    )

                # 2. Kontakt ulashilganda
                elif contact:
                    phone_number = contact['phone_number'].replace('+', '')
                    clean_phone = phone_number[-9:]  # Oxirgi 9 ta raqam bo'yicha qidiramiz

                    try:
                        profile = UserProfile.objects.get(phone__icontains=clean_phone)
                        profile.telegram_id = str(chat_id)
                        profile.save()

                        # Agar profilda kutilayotgan tasdiqlash kodi bo'lsa, darhol yuboramiz
                        if profile.verification_code:
                            send_telegram_message(
                                chat_id,
                                f"🔑 Sizning tasdiqlash kodingiz: {profile.verification_code}\n"
                                "Ushbu kodni saytdagi tasdiqlash oynasiga kiriting."
                            )
                        else:
                            send_telegram_message(
                                chat_id,
                                f"Tabriklayman, {profile.user.first_name or profile.user.username}! "
                                "Akkauntingiz Telegramga muvaffaqiyatli ulandi."
                            )
                    except UserProfile.DoesNotExist:
                        send_telegram_message(
                            chat_id,
                            "Kechirasiz, bu telefon raqam tizimda topilmadi. "
                            "Iltimos, avval saytdan roʻyxatdan oʻting."
                        )

            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'invalid method'}, status=405)

def password_reset_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        
        try:
            # 1. Telefon raqam bo'yicha userni (profilni) topamiz
            profile = UserProfile.objects.get(phone__icontains=phone[-9:])
            user = profile.user
            
            # 2. Tasodifiy yangi parol generatsiya qilamiz
            new_password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
            user.set_password(new_password)
            user.save()
            
            # 3. Agar foydalanuvchi botga ulangan bo'lsa (telegram_id bo'lsa), Telegramga yuboramiz
            if profile.telegram_id:
                send_telegram_message(
                    profile.telegram_id,
                    f"Assalomu alaykum! Sizning yangi parolingiz: {new_password}\nIltimos, tizimga kirib parolni o'zgartiring."
                )
                messages.success(request, "Yangi parol Telegram botingizga yuborildi!")
            else:
                messages.error(request, "Bu raqam egasi Telegram botimizga ulanmagan!")
                
        except UserProfile.DoesNotExist:
            messages.error(request, "Bu telefon raqam tizimda topilmadi!")
            
        return redirect('password_reset')
        
    return render(request, 'furniture/password_reset.html')





# 8. Tizimdan chiqish (Logout)
def logout_view(request):
    logout(request)
    messages.success(request, "Tizimdan muvaffaqiyatli chiqdingiz!")
    return redirect('login')


def my_view(request):
    return render(request, 'chap_nav.html')

# 3. Asosiy sahifa (Dashboard)
@login_required
def dashboard_view(request):
    return render(request, 'furniture/dashboard.html')


# 4. Yangi loyiha yaratish

@login_required
def create_project_view(request):
    if request.method == 'POST':
        data = request.POST.copy()
        
        # HTML dagi nomlarni Django formasi kutyaptgan nomlarga moslaymiz
        if 'name' in data and not data.get('title'):
            data['title'] = data['name']
        if 'area' in data and not data.get('square_meters'):
            data['square_meters'] = data['area']
        if 'price_per_sqm' in data and not data.get('price_per_unit'):
            data['price_per_unit'] = data['price_per_sqm']
            
        if not data.get('material'):
            data['material'] = 'MDF'
        if not data.get('thickness'):
            data['thickness'] = '18 mm'
            
        form = FurnitureProjectForm(data, request.FILES)
        
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user  # Foydalanuvchini biriktiramiz
            
            # Narxni hisoblash
            board_count = float(data.get('board_count') or 1)
            single_price = float(data.get('single_board_price') or 250000)
            project.estimated_price = board_count * single_price
            
            sq_m = float(data.get('square_meters') or data.get('area') or 0)
            if hasattr(project, 'square_meters'):
                project.square_meters = sq_m
                
            project.save()
            
            return redirect('my_projects') 
        else:
            print("  ")
            print(form.errors)
            print("  ")
    else:
        form = FurnitureProjectForm()
        
    available_colors = MdfColor.objects.all().order_by('-id')
    return render(request, 'furniture/create_project.html', {'form': form, 'available_colors': available_colors})


@login_required
def edit_project_view(request, pk):
    project = get_object_or_404(FurnitureProject, pk=pk, user=request.user)
    
    if request.method == 'POST':
        data = request.POST.copy()
        
        if 'name' in data and not data.get('title'):
            data['title'] = data['name']
        if 'area' in data and not data.get('square_meters'):
            data['square_meters'] = data['area']
        if 'price_per_sqm' in data and not data.get('price_per_unit'):
            data['price_per_unit'] = data['price_per_sqm']
            
        if not data.get('material'):
            data['material'] = 'MDF'
        if not data.get('thickness'):
            data['thickness'] = '18 mm'

        form = FurnitureProjectForm(data, request.FILES, instance=project)
        if form.is_valid():  
            project = form.save(commit=False)
            
            board_count = float(data.get('board_count') or 1)
            single_price = float(data.get('single_board_price') or 250000)
            project.estimated_price = board_count * single_price
            
            sq_m = float(data.get('square_meters') or 0)
            if hasattr(project, 'square_meters'):
                project.square_meters = sq_m

            project.save()
            return redirect('my_projects')
        else:
            print("EDIT FORM ERRORS:", form.errors)
    else:
        form = FurnitureProjectForm(instance=project)
        
    available_colors = MdfColor.objects.all().order_by('-id')
    return render(
        request, 'furniture/form.html', {'form': form, 'edit_mode': True, 'project': project, 'available_colors': available_colors}
    )
    
    
# 7. Loyihani o'chirish (Delete)
@login_required
def delete_project_view(request, pk):
  project = get_object_or_404(FurnitureProject, pk=pk, user=request.user)
  if request.method == 'POST':
    project.delete()
    return redirect('my_projects')
  return render(request, 'furniture/delete_confirm.html', {'project': project})



@login_required
def manage_materials(request):
    query = request.GET.get('q', '').strip()
    textures = MaterialTexture.objects.all().order_by('-id')
    
    if query:
        textures = textures.filter(name__icontains=query)
        
    form = MaterialTextureForm()
    
    if request.method == 'POST':
        form = MaterialTextureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_materials')
            
    return render(request, 'furniture/materials.html', {'textures': textures, 'form': form, 'query': query})

@login_required
def manage_colors(request):
    query = request.GET.get('q', '').strip()
    colors = MdfColor.objects.all().order_by('-id')
    
    if query:
        colors = colors.filter(name__icontains=query)
        
    form = MdfColorForm()
    
    if request.method == 'POST':
        form = MdfColorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_colors')
            
    return render(request, 'furniture/colors.html', {'colors': colors, 'form': form, 'query': query})



@login_required
def delete_material(request, pk):
    material = get_object_or_404(MaterialTexture, pk=pk) # yoki Material model nomi
    material.delete()
    return redirect('manage_materials')




@login_required
def delete_color(request, pk):
    color = MdfColor.objects.get(pk=pk)
    color.delete()
    return redirect('manage_colors')

@login_required
def project_detail_view(request, pk):
    # Faqat shu foydalanuvchiga tegishli loyihani qidirib topamiz
    project = get_object_or_404(FurnitureProject, pk=pk, user=request.user)
    
    context = {
        'project': project
    }
    return render(request, 'furniture/project_detail.html', context)

@login_required
def my_projects_view(request):
    query = request.GET.get('q', '').strip()
    projects = FurnitureProject.objects.filter(user=request.user)
    
    if query:
        projects = projects.filter(
            Q(title__icontains=query) | Q(furniture_type__icontains=query) | Q(material__icontains=query)
        )
        
    return render(request, 'furniture/projects.html', {'projects': projects, 'query': query})




def home_view(request):
    projects = FurnitureProject.objects.all().order_by('-created_at')[:4]
    return render(request, 'furniture/home.html', {'projects': projects})


@login_required
def client_catalog_view(request):
    # Bazadagi BARCHA mebelchilar qo'shgan loyihalarni olamiz:
    projects = FurnitureProject.objects.all().order_by('-id')
    
    context = {
        'projects': projects,
    }
    return render(request, 'catalog_base.html', context)


@login_required
def project_detail_view(request, pk):
    project = get_object_or_404(FurnitureProject, pk=pk)
    reviews = project.reviews.all().order_by('-created_at')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        # Baho yoki izoh kiritilgan bo'lsa, ProjectReview modeliga saqlaymiz
        if rating or comment:
            ProjectReview.objects.create(
                project=project,
                user=request.user,
                rating=int(rating) if rating else 5,
                comment=comment if comment else "Izoh qoldirilmadi"
            )
            messages.success(request, "Sharhingiz muvaffaqiyatli saqlandi!")
            return redirect('project_detail', pk=project.pk)

    context = {
        'project': project,
        'reviews': reviews,
    }
    return render(request, 'furniture/project_detail.html', context)

@login_required
def craftsman_project_detail_view(request, pk):
    project = get_object_or_404(FurnitureProject, pk=pk)
    reviews = project.reviews.all().order_by('-created_at')

    if request.method == 'POST':
        images = request.FILES.getlist('images')
        if images:
            for img in images:
                ProjectImage.objects.create(project=project, image=img)
            messages.success(request, f"{len(images)} ta rasm muvaffaqiyatli yuklandi!")
            return redirect('craftsman_project_detail', pk=project.pk)
        else:
            messages.error(request, "Iltimos, kamida bitta rasm tanlang.")

    context = {
        'project': project,
        'reviews': reviews,
    }
    return render(request, 'furniture/craftsman_project_detail.html', context)


def client_mdf_colors_view(request):
    query = request.GET.get('q', '').strip()
    
    # Tartiblash va barcha ranglarni olish
    try:
        colors = MdfColor.objects.all().order_by('-created_at')
    except:
        colors = MdfColor.objects.all().order_by('-id')
    
    # Qidiruv mantigi
    if query:
        colors = colors.filter(name__icontains=query)
        
    return render(request, 'furniture/mdf_colors_list.html', {
        'colors': colors,
        'query': query
    })


def client_materials_view(request):
    query = request.GET.get('q', '').strip()
    
    # Materiallar va teksturalarni olish
    try:
        materials_qs = Material.objects.all().order_by('-created_at')
        textures_qs = MaterialTexture.objects.all().order_by('-created_at')
    except:
        materials_qs = Material.objects.all().order_by('-id')
        textures_qs = MaterialTexture.objects.all().order_by('-id')
        
    # Qidiruv mantigi
    if query:
        materials_qs = materials_qs.filter(name__icontains=query)
        textures_qs = textures_qs.filter(name__icontains=query)
        
    materials_list = list(materials_qs)
    textures_list = list(textures_qs)
    all_materials = materials_list + textures_list
    
    return render(request, 'furniture/materials_list.html', {
        'materials': all_materials,
        'query': query
    })


def client_projects_view(request):
    query = request.GET.get('q', '').strip()
    
    # Tayyor loyihalarni olish
    try:
        projects = FurnitureProject.objects.all().order_by('-created_at')
    except:
        projects = FurnitureProject.objects.all().order_by('-id')
        
    # Qidiruv mantigi (sarlavha yoki nom bo'yicha)
    if query:
        # Loyiha modelida sarlavha 'title' yoki 'name' bo'lishiga qarab ikkalasini ham qidiradi
        projects = projects.filter(
            Q(title__icontains=query) | Q(name__icontains=query)
        ) if hasattr(FurnitureProject, 'title') and hasattr(FurnitureProject, 'name') else (
            projects.filter(title__icontains=query) if hasattr(FurnitureProject, 'title') else projects.filter(name__icontains=query)
        )
        
    return render(request, 'furniture/client_projects.html', {
        'projects': projects,
        'query': query
    })


@login_required
def toggle_favorite_view(request, pk):
    project = get_object_or_404(FurnitureProject, pk=pk)
    if request.user in project.favorites.all():
        project.favorites.remove(request.user)
    else:
        project.favorites.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', 'client_projects'))

@login_required
def favorite_projects_view(request):
    projects = request.user.favorite_projects.all().order_by('-created_at')
    return render(request, 'furniture/client_projects.html', {'projects': projects, 'is_favorites_page': True})



@login_required
def profile_edit_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, "Profil ma'lumotlari muvaffaqiyatli yangilandi!")
        return redirect('profile_edit')
    return render(request, 'profile_edit.html')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Parol muvaffaqiyatli o'zgartirildi!")
            return redirect('password_change')
        else:
            messages.error(request, "Xatolik! Ma'lumotlarni tekshirib qaytadan kiriting.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'password_change.html', {'form': form})

@login_required
def system_parameters_view(request):
    return render(request, 'system_parameters.html')