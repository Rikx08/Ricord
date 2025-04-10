from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path("", views.main, name="home"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("profile/", views.profile, name="profile"),
    path("channel/", views.channel, name="channel"),
    path('search-users/', views.search_users, name='search_users'),
]

