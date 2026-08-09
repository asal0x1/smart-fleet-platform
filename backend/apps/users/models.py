from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.uploads import avatar_upload_to, validate_image_file


class UserRole(models.TextChoices):
    CLIENT = "client", "Mijoz"
    DRIVER = "driver", "Haydovchi"
    ADMIN = "admin", "Administrator"


class UserManager(BaseUserManager):
    """phone asosida user yaratuvchi manager."""

    use_in_migrations = True

    def _create_user(self, phone, password, **extra):
        if not phone:
            raise ValueError("Telefon raqam majburiy")
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone, password=None, **extra):
        extra.setdefault("role", UserRole.CLIENT)
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault("role", UserRole.ADMIN)
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_verified", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi shart")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi shart")
        return self._create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    phone = models.CharField("Telefon", max_length=20, unique=True, db_index=True)
    full_name = models.CharField("F.I.O", max_length=100, blank=True)
    email = models.EmailField("Email", max_length=100, blank=True)
    avatar_url = models.URLField("Avatar (tashqi havola)", max_length=255, blank=True)
    avatar = models.ImageField(
        "Avatar rasmi", upload_to=avatar_upload_to, blank=True, null=True,
        validators=[validate_image_file],
    )
    role = models.CharField(
        "Rol", max_length=20, choices=UserRole.choices, default=UserRole.CLIENT
    )
    is_verified = models.BooleanField("Tasdiqlangan", default=False)
    is_active = models.BooleanField("Faol", default=True)
    is_staff = models.BooleanField("Xodim", default=False)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.phone} ({self.role})"
