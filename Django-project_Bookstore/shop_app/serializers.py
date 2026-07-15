from rest_framework import serializers
from .models import Category, Book

class CategorySerializer(serializers.ModelSerializer):
    """Серіалізатор для моделі Category"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class BookSerializer(serializers.ModelSerializer):
    """Серіалізатор для моделі Book. Використовує вкладений (nested) серіалізатор для відображення категорії на GET-запитах."""
    # Виведення об'єкта категорії
    category_detail = CategorySerializer(source='category', read_only=True)

    # PrimaryKeyRelatedField очікує ID категорії
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'description', 'price', 'stock', 'cover', 'category', 'category_detail'
        ]

    def validate_price(self, value):
        """Валідація, щоб ціна не була від'ємною або нульовою."""
        if value <= 0:
            raise serializers.ValidationError("Ціна книги повинна бути більшою за 0.")
        return value
