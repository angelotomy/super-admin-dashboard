from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('superadmin', 'Super Admin'),
        ('user', 'Regular User'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # OTP fields for password recovery
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_verified = models.BooleanField(default=False)
    
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_valid_until = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return self.email
    
    def generate_otp(self):
        """Generate a 6-digit OTP code"""
        self.otp_code = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.otp_verified = False
        self.save()
        return self.otp_code
    
    def verify_otp(self, otp):
        """Verify OTP and check if it's still valid (10 minutes)"""
        if not self.otp_code or not self.otp_created_at:
            return False
        
        # Check if OTP is expired (10 minutes)
        time_diff = timezone.now() - self.otp_created_at
        if time_diff.total_seconds() > 600:  # 10 minutes
            return False
        
        if self.otp_code == otp:
            self.otp_verified = True
            self.save()
            return True
        return False

class Page(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    url = models.CharField(max_length=200, default='/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class UserPagePermission(models.Model):
    PERMISSION_CHOICES = (
        ('view', 'View'),
        ('edit', 'Edit'),
        ('create', 'Create'),
        ('delete', 'Delete'),
    )

    user = models.ForeignKey(User, related_name='page_permissions', on_delete=models.CASCADE)
    page = models.ForeignKey(Page, related_name='user_permissions', on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'page')
        ordering = ['user', 'page']

    def __str__(self):
        permissions = []
        if self.can_view:
            permissions.append('View')
        if self.can_edit:
            permissions.append('Edit')
        if self.can_create:
            permissions.append('Create')
        if self.can_delete:
            permissions.append('Delete')
        return f"{self.user.email} - {self.page.name} ({', '.join(permissions)})"

    @property
    def permission_level(self):
        if self.can_delete:
            return 'delete'
        elif self.can_create:
            return 'create'
        elif self.can_edit:
            return 'edit'
        elif self.can_view:
            return 'view'
        return 'none'

    @permission_level.setter
    def permission_level(self, level):
        self.can_view = level in ['view', 'edit', 'create', 'delete']
        self.can_edit = level in ['edit', 'create', 'delete']
        self.can_create = level in ['create', 'delete']
        self.can_delete = level == 'delete'

class Comment(models.Model):
    PAGE_CHOICES = (
        ('products_list', 'Products List'),
        ('marketing_list', 'Marketing List'),
        ('order_list', 'Order List'),
        ('media_plans', 'Media Plans'),
        ('offer_pricing_skus', 'Offer Pricing SKUs'),
        ('clients', 'Clients'),
        ('suppliers', 'Suppliers'),
        ('customer_support', 'Customer Support'),
        ('sales_reports', 'Sales Reports'),
        ('finance_accounting', 'Finance & Accounting'),
    )

    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    page_name = models.CharField(max_length=50, choices=PAGE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, related_name='modified_comments', on_delete=models.SET_NULL, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_page_name_display()} - {self.created_at}"

class CommentHistory(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Created'),
        ('EDIT', 'Edited'),
        ('DELETE', 'Deleted'),
    )

    comment = models.ForeignKey(Comment, related_name='history', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_content = models.TextField(null=True, blank=True)
    new_content = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.email} {self.action} comment on {self.timestamp}"