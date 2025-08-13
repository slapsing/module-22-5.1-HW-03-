from django.core.management.base import BaseCommand
from apscheduler.schedulers.blocking import BlockingScheduler
from django.utils import timezone

from news.models import Post, Category
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_weekly_posts():
    today = timezone.now()
    last_week = today - timezone.timedelta(days=7)
    categories = Category.objects.all()
    site_url = 'http://127.0.0.1:8000'


    for category in categories:
        posts = Post.objects.filter(category=category, timestamp__gte=last_week)
        if not posts.exists():
            continue

        subscribers = category.subscribers.all()
        for user in subscribers:
            if not user.email:
                continue

            html_content = render_to_string(
                'news/weekly_newsletter.html',
                {
                    'category': category,
                    'posts': posts,
                    'username': user.username,
                    'site_url': site_url,
                }
            )

            subject = f'Новые статьи в категории "{category.name}" за неделю'
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=f'Здравствуйте, {user.username}. Посмотрите новые статьи за неделю.',
                from_email=from_email,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

class Command(BaseCommand):
    help = "Запускает APScheduler для еженедельной рассылки"

    # python manage.py runapscheduler --now  сразу отправляет письма и завершает команду
    def add_arguments(self, parser):
        parser.add_argument(
            '--now',
            action='store_true',
            help='Отправить письма прямо сейчас и выйти'
        )

    def handle(self, *args, **options):
        if options['now']:
            self.stdout.write(self.style.WARNING("Отправка писем прямо сейчас..."))
            send_weekly_posts()
            self.stdout.write(self.style.SUCCESS("Рассылка завершена."))
            return

        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)

        scheduler.add_job(
            send_weekly_posts,
            trigger='interval',
            weeks=1,  # раз в неделю
            id='weekly_posts',
            replace_existing=True
        )

        self.stdout.write(self.style.SUCCESS("Scheduler started. Нажмите CTRL+C для остановки."))

        try:
            scheduler.start()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Остановка планировщика..."))
            scheduler.shutdown(wait=False)
            self.stdout.write(self.style.SUCCESS("Scheduler stopped."))
