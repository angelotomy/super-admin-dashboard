from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'pages', views.PageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/table/', views.UserViewSet.as_view({'get': 'table'}), name='user-table'),
    
    # Authentication endpoints
    path('login/', views.login_view, name='login'),
    path('login/superadmin/', views.login_superadmin, name='login_superadmin'),
    path('login/user/', views.login_user, name='login_user'),
    path('profile/', views.profile_view, name='profile'),
    
    # User management endpoints
    path('users/', views.users_list, name='users_list'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/', views.update_user, name='update_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Permission management endpoints
    path('permissions/update/', views.update_user_permissions, name='update_permissions'),
    path('users/<int:user_id>/permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('user-accessible-pages/', views.user_accessible_pages, name='user_accessible_pages'),
    
    # Password management endpoints
    path('password/reset/request/', views.password_reset_request_view, name='password_reset_request'),
    path('password/reset/verify/', views.verify_otp_view, name='verify_otp'),
    path('password/reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Pages endpoints
    path('pages/', views.pages_list_view, name='pages_list'),
    
    # Comment-related endpoints
    path('pages/<str:page_name>/comments/', views.page_comments, name='page-comments'),
    path('comments/<int:comment_id>/', views.comment_detail, name='comment-detail'),
    path('comments/<int:comment_id>/history/', views.comment_history, name='comment-history'),
    path('pages/<str:page_name>/permissions/', views.check_page_permission_view, name='page-permissions'),
]