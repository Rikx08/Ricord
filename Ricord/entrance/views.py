from django.shortcuts import render

def entrance(request):
    return render(request,"entrance/login.html")