from django.db import models
from django.contrib.auth.models import User

class Provider(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="provider")
    cin = models.CharField(max_length=20, unique=True, null=True)
    service = models.ForeignKey('service.Service', on_delete=models.CASCADE)
    location = models.CharField(max_length=150)
    proof_document = models.FileField(upload_to="proofs/")
    is_approved = models.BooleanField(default=False)  # Validation par l'admin

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service} "

