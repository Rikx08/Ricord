from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import subprocess
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_GET

def main(request):
    return render(request,"main/main.html")


@login_required
def profile(request):
    return render(request,"main/profile.html")


def channel(request):
    return render(request,"main/main_channel.html")


def start_chat_server():
    subprocess.Popen(["python", "chat_server.py"])


@require_GET
def search_users(request):
    query = request.GET.get('q', '')
    print("ПРИШЁЛ ЗАПРОС НА ПОИСК:", query)
    users = User.objects.filter(username__icontains=query)[:10]  # Ограничение до 10
    results = [{'username': user.username} for user in users]
    return JsonResponse({'users': results})


start_chat_server()