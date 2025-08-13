from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Sum
from django.template.loader import render_to_string
from django.urls import reverse

from DjangoProjectNewsPortal import settings


class Author(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='author_profile'
    )
    rating = models.FloatField(default=0)
    subscribers = models.ManyToManyField(User, related_name='author_subscribers', blank=True)

    def __str__(self):
        return self.user.username

    def update_rating(self):
        post_rating = self.posts.aggregate(pr=Sum('rating'))['pr'] or 0
        post_rating *= 3
        comment_rating = self.user.comments.aggregate(cr=Sum('rating'))['cr'] or 0
        post_comments_rating = Comment.objects.filter(post__author=self).aggregate(pcr=Sum('rating'))['pcr'] or 0
        self.rating = post_rating + comment_rating + post_comments_rating
        self.save()


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    subscribers = models.ManyToManyField(User, blank=True, related_name='category_subscribers')

    def __str__(self):
        return self.name


class Post(models.Model):
    ARTICLE = 'AR'
    NEWS = 'NW'
    POST_TYPES = [
        (ARTICLE, 'Статья'),
        (NEWS, 'Новость'),
    ]  # поле с выбором — «статья» или «новость»;

    author = models.ForeignKey('Author',
                               on_delete=models.CASCADE,
                               related_name='posts')  # связь «один ко многим» с моделью Author, доступ через author.posts
    post_type = models.CharField(max_length=2, choices=POST_TYPES, default=ARTICLE)
    title = models.CharField(max_length=100)  # заголовок статьи/новости;
    content = models.TextField()  # текст статьи/новости;
    rating = models.FloatField(default=0)  # рейтинг статьи/новости.
    category = models.ManyToManyField(Category, through='PostCategory')  # связь «многие ко многим» с моделью Category
    timestamp = models.DateTimeField(auto_now_add=True)  # автоматически добавляемая дата и время создания

    def __str__(self):
        return self.title

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()

    def preview(self):
        return f"{self.content[:150]}..." if len(self.content) > 150 else self.content

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.id)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)



class PostCategory(models.Model):
    """Промежуточная модель для связи «многие ко многим»:
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_posts')

    class Meta:
        unique_together = ('post', 'category')

    def __str__(self):
        return f'{self.post.title} - {self.category.name}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')  # связь «один ко многим» с моделью Post; доступ через post.comments
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')  # доступ через user.comments
    text = models.TextField()  # текст комментария;
    timestamp = models.DateTimeField(auto_now_add=True)  # дата и время создания комментария;
    rating = models.FloatField(default=0)  # рейтинг комментария.

    def __str__(self):
        return f'Комментарий от {self.user.username}'

    def like(self):
        self.rating += 1
        self.save()

    def dislike(self):
        self.rating -= 1
        self.save()
