import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

WAREHOUSE_URL = getattr(settings, 'WAREHOUSE_SERVICE_URL', 'http://127.0.0.1:8001')

class WarehouseServiceError(Exception):
    """Кастомний виняток для помилок сервісу склада"""
    pass

class WarehouseService:
    @staticmethod
    def reserve_stock(book_id: int, quantity: int, order_id: int) -> dict:
        """"Відправляємо запит на резервування книги у ProjectB (Warehouse)"""
        url = f"{WAREHOUSE_URL}/api/v1/reserve/"
        payload = {
            "book_id": book_id,
            "quantity": quantity,
            "order_id": order_id
        }

        try:
            response = requests.post(url, json=payload, timeout=5.0)

            if response.status_code == 200:
                logger.info(f"Успішно зарезервовано book_id={book_id}, qty={quantity} для order_id={order_id}")
                return response.json()

            elif response.status_code == 409:
                data = response.json()
                error_msg = data.get("error", "Недостатньо товару на складі.")
                logger.warning(f"Помилка резервування (409 Conflict): {error_msg}")
                raise WarehouseServiceError(error_msg)

            elif response.status_code == 404:
                logger.warning(f"Товар book_id={book_id} не знайдено на складі")
                raise WarehouseServiceError(f"Товар з ID {book_id} відсутній на складі")

            else:
                logger.error(f"Неочікувана відповідь від Warehouse Service: status={response.status_code}")
                raise WarehouseServiceError("Сервіс склада тимчасово недоступний.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка з'єднання з Warehouse Service: {e}")
            raise WarehouseServiceError("Не вдалося зв'язатис з сервісом склада. Спробуйте пізніше.")

    @staticmethod
    def release_stock(book_id: int, quantity: int, order_id: int) -> dict:
        """"Відправляємо запит на зняття резерву (при скасуванні або помилці)."""
        url = f"{WAREHOUSE_URL}/api/v1/release/"
        payload = {
            "book_id": book_id,
            "quantity": quantity,
            "order_id": order_id
        }

        try:
            response = requests.post(url, json=payload, timeout=5.0)
            if response.status_code == 200:
                logger.info(f"Знято резерв book_id={book_id}, qty={quantity} для order_id={order_id}")
                return response.json()
            else:
                logger.error(f"Помилка зняття резерву: status={response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка з'єднання з Warehouse Service при знятті резерву: {e}")
