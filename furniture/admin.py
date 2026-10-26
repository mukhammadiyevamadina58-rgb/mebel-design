from django.contrib import admin
from .models import FurnitureProject, ProjectImage
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 3  # Bir vaqtning o'zida yuklash uchun qo'shimcha 3 ta rasm maydoni

@admin.register(FurnitureProject)
class FurnitureProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectImageInline]
# Register your models here.
