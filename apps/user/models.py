from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from apps.user.config import get_role_key_value, ROLE_DICT, ROLE_CHOICES
from apps.trip_management.models import SalesPoint


class SimpleUserManager(UserManager):
    def _create_user(self, username, password, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.is_active = True
        user.is_staff = False
        user.role = ROLE_DICT['Admin']
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_salesmanager(self, username, password, **extra_fields):
        salespoint = extra_fields.get('salespoint', None)
        if salespoint is None:
            raise ValidationError(message='Showroom Required')
        user = self.model(username=username, **extra_fields)
        user.is_active = True
        user.is_staff = True
        user.role = ROLE_DICT['SalesManager']
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=16)
    designation = models.CharField(max_length=30, null=True, blank=True)

    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    role = models.PositiveSmallIntegerField(default=ROLE_DICT['Manager'], choices=ROLE_CHOICES)
    salespoint = models.ForeignKey(SalesPoint, on_delete=models.DO_NOTHING, blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = SimpleUserManager()

    def get_full_name(self):
        return f'{self.first_name or ""} {self.last_name or ""}'

    @property
    def full_name(self):
        return f'{self.first_name or ""} {self.last_name or ""}'

    def get_short_name(self):
        return self.first_name

    @property
    def get_role_display(self):
        return get_role_key_value(self.role)

    def __str__(self):
        return self.username