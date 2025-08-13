from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path, include

from .views import SignUpView, ProfileView, become_author, profile_view

urlpatterns = [
    path('', include('allauth.urls')),
    path('login/', LoginView.as_view(template_name='sign/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(template_name='sign/signup.html'), name='signup'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('become-author/', become_author, name='become_author'),

]
