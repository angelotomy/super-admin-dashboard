from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Page, Comment, CommentHistory, UserPagePermission
import random
import string

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'role', 'phone', 'date_of_birth')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Email and password are required.')
        
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'phone', 'date_of_birth')
        read_only_fields = ('id', 'email', 'role')

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField()

# NEW SERIALIZERS FOR SECTION 3 - PERMISSION MANAGEMENT

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ('id', 'name', 'description', 'url', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class UserPagePermissionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    page_name = serializers.CharField(source='page.name', read_only=True)
    
    class Meta:
        model = UserPagePermission
        fields = ('id', 'user', 'page', 'can_view', 'can_edit', 'can_create', 'can_delete',
                 'user_email', 'page_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class UserWithPermissionsSerializer(serializers.ModelSerializer):
    permissions = UserPagePermissionSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'permissions')

class BulkPermissionUpdateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    page_id = serializers.IntegerField()
    can_view = serializers.BooleanField(default=False)
    can_edit = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value
    
    def validate_page_id(self, value):
        if not Page.objects.filter(id=value).exists():
            raise serializers.ValidationError("Page does not exist.")
        return value

class UserCreationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'password')
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'date_joined')

class CommentSerializer(serializers.ModelSerializer):
    """
    This converts comment data to/from JSON
    Like a translator between Python and JavaScript
    """
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    page_display_name = serializers.CharField(source='get_page_name_display', read_only=True)
    modified_by_name = serializers.CharField(source='modified_by.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'user_name', 'user_email',
            'page_name', 'page_display_name', 'content',
            'created_at', 'modified_at', 'modified_by', 'modified_by_name',
            'is_deleted'
        ]
        read_only_fields = ['user', 'created_at', 'modified_at', 'modified_by']

class CommentHistorySerializer(serializers.ModelSerializer):
    """For showing the history of changes to super admin"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    formatted_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentHistory
        fields = ['id', 'user', 'user_name', 'user_email', 'user_role', 
                 'action', 'old_content', 'new_content', 'timestamp', 'formatted_timestamp']
    
    def get_formatted_timestamp(self, obj):
        return obj.timestamp.strftime('%B %d, %Y, %I:%M:%S %p')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'is_active')

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField()