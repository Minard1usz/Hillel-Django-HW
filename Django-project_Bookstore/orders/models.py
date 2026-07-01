from django.db import models
from django.utils.translation import gettext_lazy as _
from shop_app.models import Book

class Order(models.Model):
    first_name = models.CharField(max_length=100, verbose_name=_("Ім'я"))
    last_name = models.CharField(max_length=100, verbose_name=_("Прізвище"))
    email = models.EmailField(verbose_name=_("E-mail"))
    address = models.CharField(max_length=250, verbose_name=_("Адреса поставки"))
    postal_code = models.CharField(max_length=20, verbose_name=_("Поштовий індекс"))
    city = models.CharField(max_length=100, verbose_name=_("Місто"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Створено"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Оновлено"))
    paid = models.BooleanField(default=False, verbose_name=_("Сплачено"))
    stripe_id = models.CharField(max_length=250, blank=True, verbose_name=_("ID транзакції Stripe"))

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['created']),
        ]
        verbose_name = _("Замовлення")
        verbose_name_plural = _("Замовлення")

    def __str__(self):
        return str(_("Замовлення № %(id)d") % {'id': self.id})

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.PROTECT, verbose_name=_("Замовлення"))
    book = models.ForeignKey(Book, related_name='order_items', on_delete=models.PROTECT, verbose_name=_("Книга"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Ціна на момент покупки"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("Кількість"))

    class Meta:
        verbose_name = _("Елемент замовлення")
        verbose_name_plural = _("Елементи замовлення")

    def __str__(self):
        return str(_("Елемент %(id)d для замовлення № %(order_id)d") % {'id': self.id, 'order_id': self.order.id})

    def get_cost(self):
        return self.price * self.quantity
