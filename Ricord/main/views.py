from django.contrib.auth.decorators import login_required
from django.shortcuts import render
def main(request):
    return render(request,"main/main.html")

@login_required
def profile(request):
    return render(request,"main/profile.html")

def channel(request):
    return render(request,"main/main_channel.html")