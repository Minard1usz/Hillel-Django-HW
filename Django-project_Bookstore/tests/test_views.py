import pytest
from django.urls import reverse
from .factories import BookFactory, CategoryFactory
#-----------
# Тест асинхронних в'вюх
# Тест асинхроннох гол. сторінки
@pytest.mark.django_db(transaction=True)
async def test_store_view_async(async_client):
    from asgiref.sync import sync_to_async
    await sync_to_async(BookFactory.create)()

    url = reverse('shop_app:store')
    response = await async_client.get(url)

    assert response.status_code == 200
    assert 'special_offers' in response.context

# Тест асинхронного списку книг
@pytest.mark.django_db(transaction=True)
async def test_book_list_view_async(async_client):
    from asgiref.sync import sync_to_async
    await sync_to_async(BookFactory.create_batch)(3)

    url = reverse('shop_app:book_list')
    response = await async_client.get(url)

    assert response.status_code == 200
    assert 'object_list' in response.context
    assert len(response.context['object_list']) == 3

# Тест асинхронної детальної сторінки книги
@pytest.mark.django_db(transaction=True)
async def test_book_detail_view_async(async_client):
    from asgiref.sync import sync_to_async
    book = await sync_to_async(BookFactory.create)()

    url = reverse('shop_app:book_detail', kwargs={'pk': book.pk})
    response = await async_client.get(url)

    assert response.status_code == 200
    assert response.context['book'] == book
    assert 'cart_book_form' in response.context

# Тест асинхроннох сторінки кошика
@pytest.mark.django_db(transaction=True)
async def test_cart_detail_view_async(async_client):
    try:
        url = reverse('orders:cart_detail')
    except Exception:
        url = reverse('shop_app:cart_detail')

    response = await async_client.get(url)

    assert response.status_code == 200
    assert 'cart_items' in response.context

#-------------------
# Тест синхронних / стандартних в'юх
# Тест get запиту на сторінку створення замовлення
@pytest.mark.django_db
def test_order_create_get_request(client):
    url = reverse('orders:order_create')
    response = client.get(url)

    assert response.status_code == 200
    assert 'form' in response.context

# перевірка, що детальна сторінка повертає 404, якщо книг немає
@pytest.mark.django_db(transaction=True)
async def test_book_detail_view_404_async(async_client):
    url = reverse('shop_app:book_detail', kwargs={'pk': 9999})
    response = await async_client.get(url)
    assert response.status_code == 404

# перевірка, що сторінка каталогу працює коректно, навіть якщо в базі немає книг
@pytest.mark.django_db(transaction=True)
async def test_book_list_view_empty_catalog_async(async_client):
    url = reverse('shop_app:book_list')
    response = await async_client.get(url)

    assert response.status_code == 200
    assert 'object_list' in response.context
    assert len(response.context['object_list']) == 0