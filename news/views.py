from datetime import datetime, timezone, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.core.mail import get_connection, EmailMultiAlternatives
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from .filters import NewsFilter
from .forms import NewsForm, ArticleForm, NewsEditForm, ArticlesEditForm
from .models import Post, Author, Category
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NewsListView(ListView):
    model = Post
    ordering = ['-timestamp']
    template_name = 'news/news.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = NewsFilter(self.request.GET, queryset)

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.now(timezone.utc)
        context['next_sale'] = None
        return context


class NewsDetailView(DetailView):
    model = Post
    context_object_name = 'post'
    template_name = 'news/new.html'


class NewsSearchView(ListView):
    model = Post
    ordering = ['-timestamp']
    template_name = 'news/news_search.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = NewsFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filterset'] = self.filterset
        return context


class NewsEditView(PermissionRequiredMixin, UpdateView):
    permission_required = 'news.change_post'
    form_class = NewsEditForm
    model = Post
    template_name = 'news/news_edit.html'
    context_object_name = 'post'

    def get_success_url(self):
        return reverse('post_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS, author__user=self.request.user)


class NewsDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    template_name = 'news/news_delete.html'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.NEWS, author__user=self.request.user)

    def get_success_url(self):
        return reverse('news_list')


class ArticlesEditView(PermissionRequiredMixin, UpdateView):
    permission_required = 'news.change_post'
    form_class = ArticlesEditForm
    model = Post
    template_name = 'news/articles_edit.html'
    context_object_name = 'post'

    def get_success_url(self):
        return reverse('post_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE, author__user=self.request.user)


class ArticlesDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'news.delete_post'
    model = Post
    template_name = 'news/articles_delete.html'

    def get_queryset(self):
        return Post.objects.filter(post_type=Post.ARTICLE, author__user=self.request.user)

    def get_success_url(self):
        return reverse('news_list')


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('news.add_post', raise_exception=True), name='dispatch')
class CreatePostView(View):
    template_name = 'news/create_post.html'

    def is_author(self):
        return self.request.user.groups.filter(name='authors').exists()

    def get(self, request):
        post_type = request.GET.get('type')
        author = Author.objects.filter(user=request.user).first()
        posts_last_24h = 0
        if author:
            from django.utils.timezone import now
            since = now() - timedelta(days=1)
            posts_last_24h = Post.objects.filter(author=author, timestamp__gte=since).count()

        can_create = posts_last_24h < 3

        if post_type == 'news':
            form = NewsForm()
        elif post_type == 'article':
            form = ArticleForm()
        else:
            form = None

        return render(request, self.template_name, {
            'form': form,
            'post_type': post_type,
            'can_create': can_create,
            'posts_last_24h': posts_last_24h,
        })

    def post(self, request):
        post_type = request.POST.get('post_type')
        author = Author.objects.filter(user=request.user).first()
        from django.utils.timezone import now
        from datetime import timedelta

        if not author:
            return HttpResponse("Вы не зарегистрированы как автор.", status=403)

        since = now() - timedelta(days=1)
        posts_last_24h = Post.objects.filter(author=author, timestamp__gte=since).count()

        if posts_last_24h >= 3:
            from django.contrib import messages
            messages.error(request, 'Вы не можете публиковать более 3 новостей в сутки.')
            return redirect(f"{reverse('news_create')}?type={post_type}")

        if post_type == 'news':
            form = NewsForm(request.POST)
        elif post_type == 'article':
            form = ArticleForm(request.POST)
        else:
            form = None

        if form and form.is_valid():
            post = form.save(commit=False)
            post.author = author
            post.save()
            form.save_m2m()

            try:
                categories = list(post.category.all())
            except Exception:
                try:
                    categories = [pc.category for pc in post.post_categories.all()]
                except Exception:
                    categories = []

            subscribers_dict = {}
            for cat in categories:
                for u in cat.subscribers.all():
                    if u.email:
                        subscribers_dict[u.id] = u
            subscribers = list(subscribers_dict.values())

            if subscribers:
                subject = post.title
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
                connection = get_connection(fail_silently=False)
                messages = []

                for user in subscribers:
                    post_url = request.build_absolute_uri(reverse('post_detail', kwargs={'pk': post.pk}))
                    html_content = render_to_string('news/post_notification.html', {
                        'post': post,
                        'post_url': post_url,
                        'username': user.username,
                    })

                    text = f'Здравствуй, {user.username}. Новая статья в твоём любимом разделе!\n{post.content[:50]}'

                    msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text,
                        from_email=from_email,
                        to=[user.email],
                        connection=connection,
                    )
                    msg.attach_alternative(html_content, "text/html")
                    messages.append(msg)

                try:
                    connection.send_messages(messages)
                except Exception as e:
                    logger.exception("Ошибка при отправке рассылки о посте %s: %s", post.pk, e)

            return redirect(reverse('post_detail', kwargs={'pk': post.pk}))

        return render(request, self.template_name, {'form': form, 'post_type': post_type})


class CategoryDetailView(ListView):
    model = Post
    template_name = 'news/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 5
    ordering = ['-timestamp']

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        self.category = get_object_or_404(Category, id=category_id)
        return Post.objects.filter(category__id=category_id).order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = getattr(self, 'category', None)
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'news/categories.html'
    context_object_name = 'categories'


class AuthorListView(ListView):
    model = Author
    template_name = 'news/authors.html'
    context_object_name = 'authors'


class AuthorDetailView(DetailView):
    model = Author
    template_name = 'news/author_page.html'
    context_object_name = 'author_page'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = Post.objects.filter(author=self.object).order_by('-timestamp')
        context['posts'] = posts
        context['post_count'] = posts.count()
        context['author_rating'] = self.object.rating

        return context


class SubscriptionView(LoginRequiredMixin, View):
    model = {
        'category': Category,
        'author': Author,
    }
    template_name = 'news/subscribe.html'

    def post(self, request, model_type, object_id, action):
        obj = self.get_object(model_type, object_id)
        if not obj:
            return redirect('profile')

        if action == 'subscribe':
            obj.subscribers.add(request.user)
            if model_type == 'category':
                messages.success(request, f'Вы подписались на категорию "{obj}"')
            elif model_type == 'author':
                messages.success(request, f'Вы подписались на автора "{obj}"')
        elif action == 'unsubscribe':
            obj.subscribers.remove(request.user)
            if model_type == 'category':
                messages.info(request, f'Вы отписались от категории "{obj}"')
            elif model_type == 'author':
                messages.info(request, f'Вы отписались от автора "{obj}"')

        return redirect(self.get_redirect_url(model_type, object_id))

    def get_object(self, model_type, object_id):
        model = SubscriptionView.model.get(model_type)
        return get_object_or_404(model, pk=object_id) if model else None

    def get_redirect_url(self, model_type, object_id):
        if model_type == 'category':
            return reverse('category_posts', args=[object_id])
        elif model_type == 'author':
            return reverse('author_detail', args=[object_id])
        return reverse('profile')
