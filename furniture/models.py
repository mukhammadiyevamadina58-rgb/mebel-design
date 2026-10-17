from django.contrib.auth.models import User
from django.db import models

class FurnitureProject(models.Model):
    FURNITURE_TYPES = [
        ('shkaf', 'Shkaf'),
        ('oshxona', 'Oshxona'),
        ('stol', 'Stol'),
        ('yotoqxona', 'Yotoqxona'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='projects'
    )
    title = models.CharField(max_length=200, default='Yangi mebel loyihasi')
    furniture_type = models.CharField(
        max_length=50, choices=FURNITURE_TYPES, default='shkaf'
    )

    width = models.IntegerField(default=200, verbose_name='Eni')
    height = models.IntegerField(default=240, verbose_name="Bo'yi")
    depth = models.IntegerField(default=60, verbose_name='Chuqurligi')

    doors_count = models.IntegerField(default=4, verbose_name='Eshiklar soni')
    shelves_count = models.IntegerField(default=5, verbose_name='Tokchalar soni')

    material = models.CharField(max_length=50, default='MDF')
    thickness = models.CharField(max_length=20, default='18 mm')
    color = models.CharField(max_length=50, default='Eman')

    square_meters = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Maydoni (kv.m)"
    )
    price_per_unit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="1 kv.m narxi"
    )
    estimated_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=4850000.00
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    # ⭐️ Uzum Market: O'rtacha reyting bali (masalan: 4.8)
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0.0

    # ⭐️ Uzum Market: Jami baholar/sharhlar soni
    @property
    def reviews_count(self):
        return self.reviews.count()

    # ⭐️ Uzum Market: Har bir yulduzchaning foizdagi ulushini hisoblash
    @property
    def rating_percentages(self):
        total = self.reviews_count
        if total == 0:
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        counts = {i: 0 for i in range(1, 6)}
        for review in self.reviews.all():
            counts[review.rating] = counts.get(review.rating, 0) + 1
            
        return {star: round((count / total) * 100) for star, count in counts.items()}


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('maker', 'Mebelchi'),
        ('client', 'Mijoz'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    
    # Telegram tasdiqlash uchun yangi maydonlar:
    telegram_id = models.CharField(max_length=50, blank=True, null=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    
    
    
class MaterialTexture(models.Model):
    name = models.CharField(max_length=100, verbose_name="Material nomi")
    image = models.ImageField(upload_to='textures/', verbose_name="Tekstura rasmi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MdfColor(models.Model):
    name = models.CharField(max_length=100, verbose_name="Rang nomi")
    image = models.ImageField(upload_to='colors/', verbose_name="Rang rasmi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ProjectReview(models.Model):
    project = models.ForeignKey(FurnitureProject, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5, verbose_name="Baho (1-5)")
    comment = models.TextField(verbose_name="Kommentariya")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")

    def __str__(self):
        return f"{self.user.username} - {self.project.title} ({self.rating} yulduz)"