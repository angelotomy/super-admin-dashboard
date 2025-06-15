#!/usr/bin/env python
"""
Script to create sample users for testing the Super Admin Dashboard
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User, Page, UserPermissionSummary
from django.contrib.auth.hashers import make_password
import random
import string

def generate_strong_password():
    """Generate a strong password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(12))

def create_sample_users():
    """Create sample users for testing"""
    
    # Sample users data
    sample_users = [
        {
            'email': 'john.doe@example.com',
            'username': 'johndoe',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'user',
            'phone': '+1234567890',
            'date_of_birth': '1990-05-15'
        },
        {
            'email': 'jane.smith@example.com',
            'username': 'janesmith',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'user',
            'phone': '+1234567891',
            'date_of_birth': '1988-12-20'
        },
        {
            'email': 'mike.wilson@example.com',
            'username': 'mikewilson',
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'role': 'user',
            'phone': '+1234567892',
            'date_of_birth': '1992-08-10'
        },
        {
            'email': 'sarah.johnson@example.com',
            'username': 'sarahjohnson',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'role': 'user',
            'phone': '+1234567893',
            'date_of_birth': '1985-03-25'
        },
        {
            'email': 'david.brown@example.com',
            'username': 'davidbrown',
            'first_name': 'David',
            'last_name': 'Brown',
            'role': 'user',
            'phone': '+1234567894',
            'date_of_birth': '1995-11-08'
        }
    ]
    
    created_users = []
    
    for user_data in sample_users:
        # Check if user already exists
        if User.objects.filter(email=user_data['email']).exists():
            print(f"User {user_data['email']} already exists, skipping...")
            continue
            
        # Generate password
        password = generate_strong_password()
        
        # Create user
        user = User.objects.create(
            email=user_data['email'],
            username=user_data['username'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            role=user_data['role'],
            phone=user_data['phone'],
            date_of_birth=user_data['date_of_birth'],
            password=make_password(password)
        )
        
        # Assign some random permissions
        pages = Page.objects.all()
        for page in pages:
            # Randomly assign permissions (70% chance of having some access)
            if random.random() < 0.7:
                permission_level = random.choice(['view', 'edit', 'create', 'delete'])
                
                summary = UserPermissionSummary.objects.create(
                    user=user,
                    page=page,
                    can_view=permission_level in ['view', 'edit', 'create', 'delete'],
                    can_edit=permission_level in ['edit', 'create', 'delete'],
                    can_create=permission_level in ['create', 'delete'],
                    can_delete=permission_level == 'delete'
                )
        
        created_users.append({
            'user': user,
            'password': password
        })
        
        print(f"✅ Created user: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Password: {password}")
        print(f"   Role: {user.get_role_display()}")
        print()
    
    return created_users

def main():
    print("🚀 Creating sample users for Super Admin Dashboard...")
    print("=" * 50)
    
    try:
        created_users = create_sample_users()
        
        if created_users:
            print("🎉 Successfully created sample users!")
            print("\n📋 Login Credentials:")
            print("=" * 30)
            
            for i, user_data in enumerate(created_users, 1):
                user = user_data['user']
                password = user_data['password']
                print(f"{i}. {user.email}")
                print(f"   Username: {user.username}")
                print(f"   Password: {password}")
                print()
            
            print("💡 You can now login with any of these credentials!")
            print("🔗 Frontend URL: http://localhost:3000")
            print("🔗 Backend URL: http://localhost:8000")
            
        else:
            print("ℹ️  No new users were created (they may already exist)")
            
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 