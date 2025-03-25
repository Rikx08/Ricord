from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name="home"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("profile/", views.profile, name="profile")
]