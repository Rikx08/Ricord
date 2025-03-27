from django.contrib.auth.decorators import login_required
from django.shortcuts import render
def main(request):
    return render(request,"main/main.html")

# @login_required
# def profile(request):
#     return render(request,"main/profile.html")
from django.shortcuts import render
from account.models import Profile

def profile(request):
    user_profile = Profile.objects.get(user=request.user)  # Получаем профиль текущего пользователя
    return render(request, "profile.html", {"profile": user_profile})