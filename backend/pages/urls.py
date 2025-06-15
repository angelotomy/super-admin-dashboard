from django.urls import path
from . import views

urlpatterns = [
    path('', views.pages_list, name='pages_list'),
    path('<str:page_name>/', views.page_detail, name='page_detail'),
    path('<str:page_name>/comments/', views.add_comment, name='add_comment'),
    path('<str:page_name>/comments/<int:comment_id>/', views.comment_detail, name='comment_detail'),
]