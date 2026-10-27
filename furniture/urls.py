from django.urls import path
from . import views
from .views import telegram_webhook
from .views import client_catalog_view

urlpatterns = [
    # Asosiy sahifalar
    path('', views.home_view, name='home'),  # Reklama va dizaynchi Bosh sahifa
    path('admin/', views.maker_login_view, name='maker_login'),
    path('login/', views.login_view, name='login'),  # Kirish sahifasi
    path('register/', views.register_view, name='register'),  # Ro'yxatdan o'tish
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('verify/', views.verify_code_view, name='verify_code'),
    
    # Loyihalar bilan bog'liq yo'llar (Tartib muhim!)
    path('projects/', views.my_projects_view, name='my_projects'),
    path('create/', views.create_project_view, name='create_project'),
    path('projects/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:pk>/delete/', views.delete_project_view, name='delete_project'),
    path('edit/<int:pk>/', views.edit_project_view, name='edit_project'),
    
    # Material va Ranglar boshqaruvi
    path('maker/materials/', views.manage_materials, name='manage_materials'),
    path('materials/delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('colors/', views.manage_colors, name='manage_colors'),
    path('colors/delete/<int:pk>/', views.delete_color, name='delete_color'),
    
    # Boshqa xizmatlar
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('password/change/', views.password_change_view, name='password_change'),
    path('system/parameters/', views.system_parameters_view, name='system_parameters'),
    path('telegram-webhook/', telegram_webhook, name='telegram_webhook'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('logout/', views.logout_view, name='logout'),
    # Katalog sahifasi yo'li
    path('catalog/', client_catalog_view, name='client_catalog'),
    path('craftsman/projects/<int:pk>/', views.craftsman_project_detail_view, name='craftsman_project_detail'),
    
    path('dashboard/', views.mebelchi_dashboard, name='mebelchi_dashboard'),
    path('mdf-colors/', views.client_mdf_colors_view, name='client_mdf_colors'),

    # MEBELCHINING ishchi paneli (rang qo'shish, o'chirish va saqlash sahifasi)
    path('manage/mdf-colors/', views. client_mdf_colors_view, name='manage_mdf_colors'),
    path('materials/', views.client_materials_view, name='client_materials'), 
    path('client/projects/', views.client_projects_view, name='client_projects'),
    
        
    path('project/<int:pk>/favorite/', views.toggle_favorite_view, name='toggle_favorite'),
    path('client/favorites/', views.favorite_projects_view, name='favorite_projects'),
]