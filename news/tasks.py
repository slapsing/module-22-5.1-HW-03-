from datetime import timedelta
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import Post, Category


@shared_task
def send_new_post_notification(post_id):
    post = Post.objects.get(pk=post_id)
    categories = post.category.all()
    subscribers = set()

    for category in categories:
        for user in category.subscribers.all():
            if user.email:
                subscribers.add(user)

    subject = f'Новая статья: {post.title}'
    from_email = settings.DEFAULT_FROM_EMAIL

    for user in subscribers:
        html_content = render_to_string(
            'news/post_notification.html',
            {
                'username': user.username,
                'post': post,
                'post_url': f"http://127.0.0.1:8000{post.get_absolute_url()}",
            }
        )
        text_content = f"Здравствуй, {user.username}. Новая статья: {post.title}\n\n{post.content[:100]}..."

        msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@shared_task
def send_weekly_newsletter():
    today = timezone.now()
    last_week = today - timedelta(days=7)

    for category in Category.objects.all():
        posts = Post.objects.filter(category=category, timestamp__gte=last_week)
        if not posts.exists():
            continue

        for user in category.subscribers.all():
            if not user.email:
                continue

            html_content = render_to_string(
                'news/weekly_newsletter.html',
                {
                    'category': category,
                    'posts': posts,
                    'username': user.username,
                    'site_url': 'http://127.0.0.1:8000'
                }
            )
            subject = f'Новые статьи в категории "{category.name}" за неделю'
            from_email = settings.DEFAULT_FROM_EMAIL

            msg = EmailMultiAlternatives(
                subject=subject,
                body=f'Здравствуйте, {user.username}. Посмотрите новые статьи за неделю.',
                from_email=from_email,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
