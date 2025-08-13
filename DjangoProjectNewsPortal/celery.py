import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProjectNewsPortal.settings')

app = Celery('DjangoProjectNewsPortal')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()



app.conf.beat_schedule = {
    'send-weekly-newsletter': {
        'task': 'news.tasks.send_weekly_newsletter',
        'schedule':
            crontab(hour=8, minute=0, day_of_week=1),  # понедельник 8:00
    },
}


if __name__ == '__main__':
    app.start()