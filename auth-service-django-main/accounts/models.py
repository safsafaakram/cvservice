from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UtilisateurManager(BaseUserManager):
    def create_user(self, email, nom, prenom, role, password=None):
        if not email:
            raise ValueError('Email obligatoire')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nom=nom,
            prenom=prenom,
            role=role,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, nom, prenom, password=None):
        user = self.create_user(
            email=email,
            nom=nom,
            prenom=prenom,
            role='RECRUTEUR',
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Utilisateur(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('CANDIDAT', 'Candidat'),
        ('RECRUTEUR', 'Recruteur'),
    ]
    
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CANDIDAT')
    telephone = models.CharField(max_length=20, blank=True, null=True)
    entreprise = models.CharField(max_length=200, blank=True, null=True)
        # حقول التحقق من البريد وإعادة تعيين كلمة المرور
    email_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_created_at = models.DateTimeField(blank=True, null=True)
    
    reset_password_code = models.CharField(max_length=6, blank=True, null=True)
    reset_password_code_created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = UtilisateurManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom}"