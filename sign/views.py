from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView

from news.models import Author, Post
from .forms import BaseRegisterForm


class SignUpView(CreateView):
    form_class = BaseRegisterForm
    template_name = 'sign/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        common_group, created = Group.objects.get_or_create(name='common')
        user.groups.add(common_group)
        return response


class CustomLoginView(LoginView):
    template_name = 'sign/login.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'sign/profile.html'

    def get(self, request, *args, **kwargs):
        editing_profile = request.GET.get('editing') == '1'

        user = request.user
        if not user.first_name and not user.last_name:
            editing_profile = True

        context = self.get_context_data(editing_profile=editing_profile, **kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        return redirect('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['is_author'] = user.groups.filter(name='authors').exists()

        posts_qs = Post.objects.filter(author__user=user).select_related('author').order_by('-timestamp')

        paginator = Paginator(posts_qs, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'page_obj': page_obj,
            'posts': page_obj.object_list,
            'total_posts': posts_qs.count(),
        })

        context['editing_profile'] = kwargs.get('editing_profile', False)

        return context


@login_required
@require_POST
def become_author(request):
    user = request.user

    group, _ = Group.objects.get_or_create(name='authors')

    with transaction.atomic():
        group.user_set.add(user)
        Author.objects.get_or_create(user=user)

    return redirect('profile')


@login_required
def profile_view(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.save()
        messages.success(request, "Профиль обновлён!")
        return redirect('profile')

    if hasattr(request.user, 'author'):
        posts = request.user.author.post_set.all()
    else:
        posts = []
    return render(request, 'sign/profile.html', {
        'posts': posts,
        'total_posts': posts.count(),
        'is_author': hasattr(request.user, 'author'),
    })
