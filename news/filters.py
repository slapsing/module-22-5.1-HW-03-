from django.forms import DateInput
from django_filters import FilterSet, DateFilter, CharFilter

from .models import Post


class NewsFilter(FilterSet):
    date_after = DateFilter(
        field_name='timestamp',
        lookup_expr='gte',
        label='Опубликовано после:',
        widget=DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d.%m.%Y']
    )
    title = CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Заголовок:'
    )
    author = CharFilter(
        field_name='author__user__username',
        lookup_expr='icontains',
        label='Имя автора:'
    )

    class Meta:
        model = Post
        fields = {
        }


