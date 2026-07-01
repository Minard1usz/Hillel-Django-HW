from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
class CustomUser(AbstractUser):
    username = models.CharField(
        _("Ім'я користувача"),
        max_length=150,
        unique=True,
        help_text=_("Обов'язкове поле. Не більше 150 символів."),
    )
    email = models.EmailField(_("Електронна пошта"), unique=True)

    class Meta:
        verbose_name = _("Користувач")
        verbose_name_plural = _("Користувачі")

    def __str__(self):
        return self.username