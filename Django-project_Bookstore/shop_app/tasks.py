import logging
from celery import shared_task
from django.core.mail import send_mail
from django.core.management import call_command
from django.conf import settings

logger = logging.getLogger(__name__)


# 1. Асинхронна відправка email
@shared_task
def send_welcome_email_task(user_email, subject, message):
    logger.info(f"Sending email to {user_email}")
    send_mail(
        subject=subject,
        message=message,
        from_email=(
            settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, "DEFAULT_FROM_EMAIL")
            else "noreply@bookstore.com"
        ),
        recipient_list=[user_email],
        fail_silently=False,
    )
    return f"Email sent to {user_email}"


# 2. Генерація звітів (симуляція важкої фонової генерації)
@shared_task
def generate_report_task():
    logger.info(f"Starting report generation...")
    # місце для логіки звітів у CSV/PDF / підрахунку статистики
    import time

    time.sleep(5)  # імітація тривалої роботи
    logger.info("Report generation completed successfully.")
    return "Report generated"


# 3. Очищення застарілих сесій (для Celery Beat)
@shared_task
def clear_expired_sessions_task():
    logger.info(f"Clearing expired sessions...")
    call_command("clearsessions")
    logger.info("Expired sessions cleared.")
    return "Sessions cleared"
