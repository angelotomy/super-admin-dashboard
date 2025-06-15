from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import (
    User,
    Page,
    UserPagePermission,
    CommentHistory,
    Comment,
)
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    OTPVerificationSerializer,
    PasswordResetConfirmSerializer,
    PageSerializer,
    UserPagePermissionSerializer,
    UserWithPermissionsSerializer,
    BulkPermissionUpdateSerializer,
    UserCreationSerializer,
    UserTableSerializer,
    CommentHistorySerializer,
    CommentSerializer,
    UserSerializer,
    LoginSerializer,
    PasswordResetSerializer,
)
from django.core.mail import send_mail
from django.conf import settings
import random
import string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from rest_framework.permissions import IsAuthenticated, IsAdminUser

User = get_user_model()

def get_user_permissions_cached(user_id):
    """Cache user permissions for 5 minutes to improve performance"""
    cache_key = f"user_permissions_{user_id}"
    permissions = cache.get(cache_key)
    
    if permissions is None:
        permissions = UserPagePermission.objects.filter(user_id=user_id).select_related('user', 'page')
        cache.set(cache_key, permissions, 300)  # 5 minutes
    
    return permissions

# Enhanced permission validation
def validate_permission_edge_cases(user, page, action):
    """Handle edge cases in permission validation"""
    # Case 1: Super admin always has access
    if user.is_superuser:
        return True
    
    # Case 2: User account disabled/inactive
    if not user.is_active:
        return False
    
    # Case 3: Permission exists but user role changed
    permission = UserPagePermission.objects.filter(
        user=user, 
        page=page
    ).first()
    
    if not permission:
        return False
    
    # Case 4: Hierarchical permissions (Edit includes View, Delete includes Edit)
    if action == 'view':
        return permission.can_view or permission.can_edit or permission.can_create or permission.can_delete
    elif action == 'create':
        return permission.can_create
    elif action == 'edit':
        return permission.can_edit or permission.can_delete
    elif action == 'delete':
        return permission.can_delete
    
    return False

def user_has_permission(user, page_name, permission_type):
    """
    Check if user has specific permission for a page
    Like checking if someone has the right key for a room
    """
    if user.is_superuser:
        return True  # Super admin can do everything

    try:
        page = Page.objects.get(name=page_name)
        permission = UserPagePermission.objects.get(user=user, page=page)
        
        if permission_type == 'view':
            return permission.can_view
        elif permission_type == 'edit':
            return permission.can_edit
        elif permission_type == 'create':
            return permission.can_create
        elif permission_type == 'delete':
            return permission.can_delete
            
        return False
    except (Page.DoesNotExist, UserPagePermission.DoesNotExist):
        return False



# EXISTING AUTHENTICATION VIEWS (keeping them unchanged)
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def page_comments(request, page_name):
    """
    GET: Get all comments for a page (if user has view permission)
    POST: Create a new comment (if user has create permission)
    """

    # Check if user can view this page
    if not user_has_permission(request.user, page_name, "view"):
        return Response(
            {"error": "You do not have permission to view this page"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == "GET":
        # Get all non-deleted comments for this page
        comments = Comment.objects.filter(page_name=page_name, is_deleted=False)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        # Check if user can create comments
        if not user_has_permission(request.user, page_name, "create"):
            return Response(
                {"error": "You do not have permission to create comments on this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, page_name=page_name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "DELETE"])
@permission_classes([permissions.IsAuthenticated])
def comment_detail(request, comment_id):
    """
    PUT: Update a comment (if user has edit permission)
    DELETE: Delete a comment (if user has delete permission)
    """
    comment = get_object_or_404(Comment, id=comment_id, is_deleted=False)

    if request.method == "PUT":
        # Check if user can edit comments on this page
        if not user_has_permission(request.user, comment.page_name, "edit"):
            return Response(
                {"error": "You do not have permission to edit comments on this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(modified_by=request.user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        # Check if user can delete comments on this page
        if not user_has_permission(request.user, comment.page_name, "delete"):
            return Response(
                {"error": "You do not have permission to delete comments on this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Soft delete - mark as deleted but keep in database
        comment.is_deleted = True
        comment.save()

        # Track deletion in history
        CommentHistory.objects.create(
            comment=comment,
            user=request.user,
            action="DELETE",
            old_content=comment.content,
        )

        return Response({"message": "Comment deleted successfully"})


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def comment_history(request, comment_id):
    """
    GET: Get the history of a comment (if user has view permission or is superadmin)
    """
    comment = get_object_or_404(Comment, id=comment_id)

    # Check if user can view this page or is superadmin
    if not (user_has_permission(request.user, comment.page_name, "view") or request.user.is_superadmin):
        return Response(
            {"error": "You do not have permission to view this comment's history"},
            status=status.HTTP_403_FORBIDDEN,
        )

    history = CommentHistory.objects.filter(comment=comment).select_related('user')
    serializer = CommentHistorySerializer(history, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_accessible_pages(request):
    """Get all pages accessible to the current user with their permissions"""
    user = request.user
    
    # If superadmin, return all pages with full access
    if user.role == 'superadmin':
        pages = Page.objects.all()
        data = []
        for page in pages:
            data.append({
                'id': page.id,
                'name': page.name,
                'url': page.url,
                'permissions': {
                    'can_view': True,
                    'can_edit': True,
                    'can_create': True,
                    'can_delete': True
                }
            })
        return Response(data)
    
    # For regular users, get their specific permissions
    user_permissions = UserPagePermission.objects.filter(user=user).select_related('page')
    data = []
    
    for permission in user_permissions:
        data.append({
            'id': permission.page.id,
            'name': permission.page.name,
            'url': permission.page.url,
            'permissions': {
                'can_view': permission.can_view,
                'can_edit': permission.can_edit,
                'can_create': permission.can_create,
                'can_delete': permission.can_delete
            }
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def pages_list(request):
    """Get all available pages"""
    pages = Page.objects.all()
    serializer = PageSerializer(pages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserProfileSerializer(user).data,
            }
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get("refresh_token")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([permissions.IsAuthenticated])
def profile_update_view(request):
    serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_request_view(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)
        otp_code = user.generate_otp()
        # In a real app, send email with OTP
        return Response(
            {
                "message": "OTP sent to email",
                "otp": otp_code,  # Remove this in production
            }
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def verify_otp_view(request):
    serializer = OTPVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        user = User.objects.get(email=email)

        if user.verify_otp(otp):
            return Response({"message": "OTP verified successfully"})
        else:
            return Response(
                {"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.get(email=email)
        if user.otp_verified and user.verify_otp(otp):
            user.set_password(new_password)
            user.otp_code = None
            user.otp_verified = False
            user.save()
            return Response({"message": "Password reset successful"})
        else:
            return Response(
                {"error": "Invalid OTP or OTP not verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# SUPER ADMIN ONLY VIEWS


class IsSuperAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'superadmin'


class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superadmin


class IsManagerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class CanManageUsersPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_users


class CanAssignPermissionsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_assign_permissions


@api_view(['GET'])
@permission_classes([IsSuperAdminPermission])
def users_list(request):
    users = User.objects.all().order_by('-date_joined')
    serializer = UserProfileSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsSuperAdminPermission])
def create_user(request):
    try:
        serializer = UserCreationSerializer(data=request.data)
        if serializer.is_valid():
            # Create the user with the provided password
            user = serializer.save()
            
            # Return success response with user data
            return Response({
                'message': 'User created successfully',
                'user': UserProfileSerializer(user).data,
                'password': request.data.get('password')  # Return the password for display
            }, status=status.HTTP_201_CREATED)
        else:
            # Return validation errors
            return Response({
                'error': 'Invalid data provided',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        # Log the error for debugging
        print(f"Error creating user: {str(e)}")
        return Response({
            'error': 'Failed to create user. Please try again.'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsSuperAdminPermission])
def update_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([IsSuperAdminPermission])
def delete_user(request, user_id):
    try:
        with transaction.atomic():
            user = User.objects.get(id=user_id)
            
            # Don't allow deleting superadmin users
            if user.role == 'superadmin':
                return Response(
                    {'error': 'Cannot delete super admin user'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Delete related UserPagePermission objects first
            UserPagePermission.objects.filter(user=user).delete()
            
            # Delete any comments by the user (if they exist)
            Comment.objects.filter(user=user).delete()
            
            # Delete the user
            user.delete()
            
            return Response(
                {'message': 'User and related data deleted successfully'}, 
                status=status.HTTP_200_OK
            )
            
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error deleting user: {str(e)}")
        return Response(
            {'error': 'An error occurred while deleting the user. Please try again.'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsSuperAdminPermission])
def update_user_permissions(request):
    serializer = BulkPermissionUpdateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = User.objects.get(id=serializer.validated_data['user_id'])
                page = Page.objects.get(id=serializer.validated_data['page_id'])
                
                # Don't update permissions for superadmin
                if user.role == 'superadmin':
                    return Response({
                        'message': 'Super admin permissions cannot be modified'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                permission, created = UserPagePermission.objects.get_or_create(
                    user=user,
                    page=page,
                    defaults={
                        'can_view': serializer.validated_data.get('can_view', False),
                        'can_edit': serializer.validated_data.get('can_edit', False),
                        'can_create': serializer.validated_data.get('can_create', False),
                        'can_delete': serializer.validated_data.get('can_delete', False)
                    }
                )
                
                if not created:
                    permission.can_view = serializer.validated_data.get('can_view', False)
                    permission.can_edit = serializer.validated_data.get('can_edit', False)
                    permission.can_create = serializer.validated_data.get('can_create', False)
                    permission.can_delete = serializer.validated_data.get('can_delete', False)
                    permission.save()
                
                return Response({
                    'message': 'Permissions updated successfully',
                    'permissions': {
                        'can_view': permission.can_view,
                        'can_edit': permission.can_edit,
                        'can_create': permission.can_create,
                        'can_delete': permission.can_delete
                    }
                })
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Page.DoesNotExist:
            return Response({'error': 'Page not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsSuperAdminPermission])
def get_user_permissions(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        permissions = UserPagePermission.objects.filter(user=user).select_related('page')
        data = {}
        for permission in permissions:
            data[permission.page.id] = {
                'can_view': permission.can_view,
                'can_edit': permission.can_edit,
                'can_create': permission.can_create,
                'can_delete': permission.can_delete
            }
        return Response(data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# NEW VIEWS FOR SECTION 3 - PERMISSION MANAGEMENT


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def pages_list_view(request):
    """List all available pages"""
    pages = Page.objects.all()
    serializer = PageSerializer(pages, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsSuperAdminPermission])
def user_permissions_view(request, user_id):
    """Get all permissions for a specific user"""
    user = get_object_or_404(User, id=user_id)
    permissions = UserPagePermission.objects.filter(user=user).select_related("page").all()
    serializer = UserPagePermissionSerializer(permissions, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsSuperAdminPermission])
def users_table_view(request):
    """Get users with their permissions in table format"""
    users = User.objects.prefetch_related("permission_summaries__page").all()
    serializer = UserTableSerializer(users, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_permissions_view(request):
    """Get current user's permissions"""
    if request.user.is_superadmin:
        # Super admin has all permissions
        pages = Page.objects.all()
        permissions_data = []
        for page in pages:
            permissions_data.append(
                {
                    "page_id": page.id,
                    "page_name": page.name,
                    "can_view": True,
                    "can_edit": True,
                    "can_create": True,
                    "can_delete": True,
                }
            )
        return Response(permissions_data)
    else:
        summaries = request.user.permission_summaries.select_related("page").all()
        serializer = UserPermissionSummarySerializer(summaries, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsSuperAdminPermission])
def reset_user_password_view(request, user_id):
    """Reset user password and generate new one (super admin only)"""
    user = get_object_or_404(User, id=user_id)

    # Generate new password
    serializer = UserCreationSerializer()
    new_password = serializer.generate_strong_password()

    user.set_password(new_password)
    user.save()

    return Response(
        {"message": "Password reset successfully", "new_password": new_password}
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def check_page_permission_view(request, page_id, permission_type):
    """Check if user has specific permission for a page"""
    if request.user.is_superadmin:
        return Response({"has_permission": True})

    try:
        page = Page.objects.get(id=page_id)
        permission = UserPagePermission.objects.get(
            user=request.user, page=page, can_view=True, can_edit=True, can_create=True, can_delete=True
        )
        return Response({"has_permission": True})
    except (Page.DoesNotExist, UserPagePermission.DoesNotExist):
        return Response({"has_permission": False})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreationSerializer
    permission_classes = [IsSuperAdminPermission]
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({
                    'message': 'User created successfully',
                    'user': UserProfileSerializer(user).data,
                    'password': request.data.get('password')  # Return the password for display
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(f"Error creating user: {str(e)}")
                return Response({
                    'error': 'Failed to create user. Please try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'error': 'Invalid data provided',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserProfileSerializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserProfileSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        
        if user.role == 'superadmin':
            return Response(
                {'error': 'Cannot delete super admin user'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Delete related permissions first
            UserPagePermission.objects.filter(user=user).delete()
            
            # Delete any comments by the user
            Comment.objects.filter(user=user).delete()
            
            # Delete the user
            user.delete()
            
            return Response(
                {'message': 'User and related data deleted successfully'}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            return Response(
                {'error': 'An error occurred while deleting the user. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]

    def list(self, request):
        pages = self.get_queryset()
        data = [{
            'id': page.id,
            'name': page.name,
            'description': page.description,
            'url': page.url
        } for page in pages]
        return Response(data)

@api_view(['POST'])
@permission_classes([])
def login_superadmin(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role != 'superadmin':
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([])
def login_user(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(email=email)
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == 'superadmin':
            return Response({'error': 'Please use super admin login'}, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@api_view(['POST'])
@permission_classes([])
def request_password_reset(request):
    email = request.data.get('email')
    
    try:
        user = User.objects.get(email=email)
        otp = generate_otp()
        user.otp = otp
        user.save()
        
        # Send OTP via email
        send_mail(
            'Password Reset OTP',
            f'Your OTP for password reset is: {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        return Response({'message': 'OTP sent successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    
    try:
        user = User.objects.get(email=email)
        if user.otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'OTP verified successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([])
def reset_password(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    new_password = request.data.get('new_password')
    
    try:
        user = User.objects.get(email=email)
        if user.otp != otp:
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.otp = None  # Clear OTP after successful reset
        user.save()
        
        return Response({'message': 'Password reset successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
