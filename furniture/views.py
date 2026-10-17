import json
import random

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

# 1. Tizimga kirish (Login)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Foydalanuvchining rolini tekshiramiz
            try:
                profile = user.userprofile
                if profile.role == 'maker':
                    # Mebelchi bo'lsa, uning shaxsiy kabinetiga yo'naltiramiz
                    return redirect('mebelchi_dashboard')
                else:
                    # Agar mijoz bo'lsa, tayyor loyihalar katalogiga
                    return redirect('client_catalog')
            except UserProfile.DoesNotExist:
                # Agar profili topilmasa, oddiy mijoz deb hisoblaymiz
                return redirect('client_catalog')
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

        # 1. Parollar mos kelishini tekshirish
        if password != confirm_password:
            messages.error(request, 'Xatolik: Parollar bir xil emas!')
            return render(request, 'furniture/register.html')

        # 2. Username bandligini tekshirish
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Xatolik: Bu username band, boshqa nom tanlang!')
            return render(request, 'furniture/register.html')

        # 3. Telefon raqami tekshirish
        clean_phone = phone.replace('+', '').strip()
        if UserProfile.objects.filter(phone__icontains=clean_phone[-9:]).exists():
            messages.error(request, "Xatolik: Bu telefon raqam allaqachon ro'yxatdan o'tgan!")
            return render(request, 'furniture/register.html')

        # 4. Foydalanuvchini yaratamiz
        user = User.objects.create_user(
            username=username, 
            password=password, 
            first_name=name
        )
        
        # 5. 6 xonali OTP tasdiqlash kodini generatsiya qilish
        code = str(random.randint(100000, 999999))

        # 6. Profil yaratamiz (avtomatik 'client' roli bilan)
        profile = UserProfile.objects.create(
            user=user, 
            phone=phone,
            role='client',
            verification_code=code,
            is_verified=False
        )

        # 7. Sessiyaga foydalanuvchi ID-sini saqlaymiz
        request.session['pending_user_id'] = user.id

        # 8. Telegram ID bor bo'lsa, kodni bot orqali yuboramiz
        if profile.telegram_id:
            send_telegram_message(
                profile.telegram_id, 
                f"🔑 Sizning tasdiqlash kodingiz: {code}\nKodni saytga kiriting."
            )
            messages.info(request, "Tasdiqlash kodi Telegram botingizga yuborildi.")
        else:
            messages.warning(
                request, 
                "Tasdiqlash kodini olish uchun iltimos Telegram botimizga kiring va 'Telefon raqamni ulashish' tugmasini bosing!"
            )

        return redirect('verify_code')

    return render(request, 'furniture/register.html')


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
            return redirect('client_catalog')
        else:
            messages.error(request, "Xatolik: Tasdiqlash kodi xato!")

    context = {
        'phone': profile.phone,
        'bot_username': 'MebelDesignBot'  # O'zingizning botingiz username-ini yozing
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

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Bot tokeningizni yozing

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
        # 1. request.POST ni nusxalab olamiz
        data = request.POST.copy()
        
        # 2. HTML dagi nomlarni Django formasi kutyaptgan nomlarga moslaymiz
        if 'name' in data and not data.get('title'):
            data['title'] = data['name']
        if 'area' in data and not data.get('square_meters'):
            data['square_meters'] = data['area']
        if 'price_per_sqm' in data and not data.get('price_per_unit'):
            data['price_per_unit'] = data['price_per_sqm']
            
        # Agar material va qalinlik tanlanmagan bo'lsa, default qiymat beramiz
        if not data.get('material'):
            data['material'] = 'MDF'
        if not data.get('thickness'):
            data['thickness'] = '18 mm'
            
        # Narxni hisoblab olamiz
        board_count = float(data.get('board_count') or 1)
        single_price = float(data.get('single_board_price') or 250000)
        
        # Tayyorlangan 'data' ni formaga uzatamiz
        form = FurnitureProjectForm(data, request.FILES)
        
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user # Loyihani hozirgi mebelchiga biriktiramiz
            
            # Narxni yozamiz
            project.estimated_price = board_count * single_price
            
            sq_m = float(data.get('square_meters') or 0)
            if hasattr(project, 'square_meters'):
                project.square_meters = sq_m
                
            project.save()
            
            # Mebelchi loyihani saqlagach, to'g'ridan-to'g'ri o'z kabinetiga o'tadi:
            return redirect('mebelchi_dashboard') 
        else:
            print("CREATE FORM ERRORS:", form.errors)
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
    textures = MaterialTexture.objects.all().order_by('-id')
    form = MaterialTextureForm()
    
    if request.method == 'POST':
        form = MaterialTextureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_materials')
            
    return render(request, 'furniture/materials.html', {'textures': textures, 'form': form})

@login_required
def manage_colors(request):
    colors = MdfColor.objects.all().order_by('-id')
    form = MdfColorForm()
    
    if request.method == 'POST':
        form = MdfColorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('manage_colors')
            
    return render(request, 'furniture/colors.html', {'colors': colors, 'form': form})

@login_required
def delete_material(request, pk):
    material = MaterialTexture.objects.get(pk=pk)
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
    projects = FurnitureProject.objects.filter(user=request.user)
    return render(request, 'furniture/projects.html', {'projects': projects})

def home_view(request):
    return render(request, 'furniture/home.html')


@login_required
def client_catalog_view(request):
    # Faqat shu tizimga kirgan mijozning o'z loyihalarini bazadan olib kelamiz
    projects = FurnitureProject.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'projects': projects,
    }
    return render(request, 'furniture/client_catalog.html', context)