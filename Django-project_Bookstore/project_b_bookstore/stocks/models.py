from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    book_id = models.IntegerField(db_index=True, help_text="ID книги з ProjectA (Bookstore)")
    quantity = models.PositiveIntegerField(default=0, help_text="Загальна кількість на складі")
    reserved_quantity = models.PositiveIntegerField(default=0, help_text="Зарезервовано під замовлення")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('warehouse', 'book_id')

    @property
    def available_quantity(self):
        """Кількість, яка доступна для резерку / купівлі"""
        return self.quantity - self.reserved_quantity

    def __str__(self):
        return f"Book ID {self.book_id} @ {self.warehouse.name}: {self.quantity} (Reserved: {self.reserved_quantity})"

class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        INCOMING = 'INCOMING', 'Надходження'
        RESERVE = 'RESERVE', 'Резервуванння'
        RELEASE = 'RELEASE', 'Зняття резерву'
        DEDUCT = 'DEDUCT', 'Списання (Продаж)'

    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    order_id = models.IntegerField(null=True, blank=True, help_text="ID замовлення з ProjectA")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movement_type} - {self.quantity} pcs (Book ID: {self.stock.book_id})"
