#!/usr/bin/env python
"""
Script to remove any users with roles other than 'superadmin' or 'user'.
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User

def cleanup_invalid_roles():
    valid_roles = ['superadmin', 'user']
    invalid_users = User.objects.exclude(role__in=valid_roles)
    count = invalid_users.count()
    for user in invalid_users:
        print(f"Deleting user: {user.email} (role: {user.role})")
        user.delete()
    print(f"Deleted {count} user(s) with invalid roles.")

if __name__ == "__main__":
    cleanup_invalid_roles() 