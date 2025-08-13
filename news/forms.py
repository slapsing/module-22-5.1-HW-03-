from django import forms

from .models import Post


class BasePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['category', 'title', 'content']
        labels = {
            'author': 'Автор',
            'category': 'Категория:',
            'title': 'Заголовок',

        }
        widgets = {
            'author': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    post_type_value = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.post_type_value:
            self.instance.post_type = self.post_type_value


class NewsForm(BasePostForm):
    post_type_value = Post.NEWS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = 'Текст новости:'


class ArticleForm(BasePostForm):
    post_type_value = Post.ARTICLE

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].label = 'Текст статьи:'


class BaseEditPostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.content_label:
            self.fields['content'].label = self.content_label

    class Meta:
        model = Post
        fields = ['category', 'title', 'content']
        labels = {
            'title': 'Заголовок',
            'category': 'Категория:',

        }
        widgets = {
            'category': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    content_label = None


class NewsEditForm(BaseEditPostForm):
    content_label = 'Текст новости:'


class ArticlesEditForm(BaseEditPostForm):
    content_label = 'Текст статьи:'


class SubscribeForm(forms.Form):
    subscribe = forms.BooleanField(required=False, label='Подписаться на категорию')