import factory
from factory.django import DjangoModelFactory
from shop_app.models import Category, Book

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"Category {n}")

class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f"Book Title {n}")
    author = factory.Faker("name")
    description = factory.Faker("text")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True, min_value=50, max_value=999)
    stock = factory.Faker("random_int", min=1, max=50)

    category = factory.SubFactory(CategoryFactory)

    cover = None