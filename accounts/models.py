# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('election_creator', 'Election Creator'),
        ('voter', 'Voter'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='voter')

    def is_admin(self):
        return self.role == 'admin'

    def is_moderator(self):
        return self.role == 'moderator'

    def is_creator(self):
        return self.role == 'election_creator'

