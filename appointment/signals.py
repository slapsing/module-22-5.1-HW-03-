from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from news.models import Post


@receiver(post_save, sender=Post)
def send_post_notifications(sender, instance, created, **kwargs):
    if not created:
        return

    notified_users = set()

    def notify(user, subject, message):
        if user.email and user not in notified_users:
            html_content = render_to_string(
                'news/post_notification.html',
                {
                    'post': instance,
                    'username': user.username,
                }
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_content,
            )
            notified_users.add(user)

    for cat in instance.category.all():
        for user in cat.subscribers.all():
            notify(user, subject=instance.title,
                   message=f'Здравствуй, {user.username}. Новая статья в твоём любимом разделе!')

    for user in instance.author.subscribers.all():
        notify(user, subject=f'Новая публикация от {instance.author.user.username}',
               message=f'Здравствуй, {user.username}. Автор {instance.author.user.username} опубликовал новую статью!')
