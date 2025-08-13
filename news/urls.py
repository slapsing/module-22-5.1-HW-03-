from django.urls import path

from .views import *

urlpatterns = [
    path('', NewsListView.as_view(), name='news_list'),
    path('<int:pk>', NewsDetailView.as_view(), name='post_detail'),
    path('search/', NewsSearchView.as_view(), name='news_search'),
    # path('news/create/', NewsCreateView.as_view(), name='news_create'),
    path('news/<int:pk>/edit/', NewsEditView.as_view(), name='news_edit'),
    path('news/<int:pk>/delete/', NewsDeleteView.as_view(), name='news_delete'),
    # path('articles/create/', ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/edit/', ArticlesEditView.as_view(), name='articles_edit'),
    path('articles/<int:pk>/delete/', ArticlesDeleteView.as_view(), name='articles_delete'),
    path('create/', CreatePostView.as_view(), name='news_create'),
    path('category/<int:category_id>/', CategoryDetailView.as_view(), name='category_posts'),
    path('categories/', CategoryListView.as_view(), name='categories_list'),
    path('authors/', AuthorListView.as_view(), name='authors_list'),
    path('authors/<int:pk>/', AuthorDetailView.as_view(), name='author_detail'),
    path('<str:action>/<str:model_type>/<int:object_id>/', SubscriptionView.as_view(), name='subscription'),

]



