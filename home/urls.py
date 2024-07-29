from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.sign_up, name='sign_up'),
    path('signup/code/<int:telegram_id>@<str:username>/', views.index, name='code'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_page, name='home_page'),
    path('create/', views.create, name='create'),
    path('home/room<str:invite_link>/', views.room, name='room'),
    path('home/send/', views.send, name='send')
]
