from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
            return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='books')
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)

    def __str__(self):
        return f"{self.title} by {self.author}"


