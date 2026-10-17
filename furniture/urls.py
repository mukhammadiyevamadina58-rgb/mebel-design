from django.urls import path
from . import views
from .views import telegram_webhook
from .views import client_catalog_view

urlpatterns = [
    # Asosiy sahifalar
    path('', views.home_view, name='home'),  # Reklama va dizaynchi Bosh sahifa
    path('login/', views.login_view, name='login'),  # Kirish sahifasi
    path('register/', views.register_view, name='register'),  # Ro'yxatdan o'tish
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Loyihalar bilan bog'liq yo'llar (Tartib muhim!)
    path('projects/', views.my_projects_view, name='my_projects'),
    path('create/', views.create_project_view, name='create_project'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:pk>/delete/', views.delete_project_view, name='delete_project'),
    path('edit/<int:pk>/', views.edit_project_view, name='edit_project'),
    
    # Material va Ranglar boshqaruvi
    path('materials/', views.manage_materials, name='manage_materials'),
    path('materials/delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('colors/', views.manage_colors, name='manage_colors'),
    path('colors/delete/<int:pk>/', views.delete_color, name='delete_color'),
    
    # Boshqa xizmatlar
    path('telegram-webhook/', telegram_webhook, name='telegram_webhook'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('logout/', views.logout_view, name='logout'),
    # Katalog sahifasi yo'li
    path('catalog/', client_catalog_view, name='client_catalog'),
    
    path('dashboard/', views.mebelchi_dashboard, name='mebelchi_dashboard'),
]