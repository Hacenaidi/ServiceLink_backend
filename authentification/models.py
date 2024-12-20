from django.db import models
from django.contrib.auth.models import User

class ProfileUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='profile/', null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    nom = models.CharField(max_length=150, null=True, blank=True)
    prenom = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=150, null=True, blank=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    def __str__(self):
        return f"{self.user.username} - {self.nom} - {self.prenom} "