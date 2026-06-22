from django.db import models
from shop_app.models import Book

class Order(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Ім'я")
    last_name = models.CharField(max_length=100, verbose_name="Прізвище")
    email = models.EmailField(verbose_name="E-mail")
    address = models.CharField(max_length=250, verbose_name="Адреса поставки")
    postal_code = models.CharField(max_length=20, verbose_name="Поштовий індекс")
    city = models.CharField(max_length=100, verbose_name="Місто")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    paid = models.BooleanField(default=False, verbose_name="Сплачено")
    stripe_id = models.CharField(max_length=250, blank=True, verbose_name="ID транзакції Stripe")

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['created']),
        ]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def __str__(self):
        return f"Замовлення № {self.id}"

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.PROTECT)
    book = models.ForeignKey(Book, related_name='order_items', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна на момент покупки")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")

    def _str_(self):
        return f"Елемент {self.id} для замовлення № {self.order.id}"

    def get_cost(self):
        return self.price * self.quantity
