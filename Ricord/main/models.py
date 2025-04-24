from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    image = models.BinaryField(blank=True, null=True)  # Для хранения бинарных данных
    image_type = models.CharField(max_length=50, blank=True, null=True)  # Например 'image/jpeg'
    room = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)