from django import forms
from .models import FurnitureProject
from .models import MaterialTexture, MdfColor

class FurnitureProjectForm(forms.ModelForm):
    class Meta:
        model = FurnitureProject
        fields = [
            'title', 
            'furniture_type', 
            'width', 
            'height', 
            'depth', 
            'doors_count', 
            'shelves_count', 
            'material', 
            'thickness', 
            'color', 
            'square_meters',   # <-- Mana bu yerga qo'shildi
            'price_per_unit'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Loyiha nomi...'}),
            'furniture_type': forms.Select(attrs={'class': 'form-select'}),
            'width': forms.NumberInput(attrs={'class': 'form-control', 'id': 'input-width'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'id': 'input-height'}),
            'depth': forms.NumberInput(attrs={'class': 'form-control', 'id': 'input-depth'}),
            'doors_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'shelves_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'material': forms.Select(choices=[('MDF', 'MDF'), ('Laminat', 'Laminat')], attrs={'class': 'form-select'}),
            'thickness': forms.Select(choices=[('16 mm', '16 mm'), ('18 mm', '18 mm')], attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'id': 'input-color'}),
            'square_meters': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 3.5'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: 150000'}),
        }


# Boshqa formalaringiz o'zgarishsiz qoladi:

class MaterialTextureForm(forms.ModelForm):
    class Meta:
        model = MaterialTexture
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Material nomi...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class MdfColorForm(forms.ModelForm):
    class Meta:
        model = MdfColor
        fields = ['name', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rang nomi...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }