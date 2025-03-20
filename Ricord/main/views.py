from django.contrib.auth.decorators import login_required
from django.shortcuts import render
def main(request):
    return render(request,"main/main.html")


