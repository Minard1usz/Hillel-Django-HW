from django.contrib import admin
from .models import Category, Book

# Register your models here.
class BookInLine(admin.TabularInline):
    model = Book
    extra = 1

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock', 'category')
    list_filter = ('category', 'author', 'stock')
    search_fields = ('title', 'author', 'description')
    list_editable = ('price', 'stock')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BookInLine]
