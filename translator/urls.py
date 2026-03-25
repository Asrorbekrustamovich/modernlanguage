from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('history/', views.history, name='history'),
    path('result/<int:pk>/', views.result_detail, name='result_detail'),
    path('result/<int:pk>/delete/', views.delete_result, name='delete_result'),
    path('download_pdf/<int:pk>/', views.download_pdf, name='download_pdf'),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
