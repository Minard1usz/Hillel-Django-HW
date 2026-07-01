from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Назва'))
    slug = models.SlugField(unique=True, max_length=100, verbose_name=_('Слаг'))

    class Meta:
        verbose_name = _('Категорія')
        verbose_name_plural = _('Категорії')

    def __str__(self):
            return self.name

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name=_('Назва книги'))
    author = models.CharField(max_length=100, verbose_name=_('Автор'))
    description = models.TextField(blank=True, verbose_name=_('Опис'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Ціна'))
    stock = models.PositiveIntegerField(default=0, verbose_name=_('Кількість на складі'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books', verbose_name=_('Категорія'))
    cover = models.ImageField(upload_to='covers/', null=True, blank=True, verbose_name=_('Обкладинка'))

    class Meta:
        verbose_name = _('Книга')
        verbose_name_plural = _('Книги')

    def __str__(self):
        return f"{self.title} by {self.author}"
