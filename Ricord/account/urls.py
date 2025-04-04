from django.urls import path
from .views import register_view, login_view, logout_view
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
