import time
import logging

logger = logging.getLogger('shop_logger')

class PerformanceTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        logger.info(f"Запит до {request.path} зайняв {duration:.4f} секунд.")
        return response