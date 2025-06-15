from django.core.management.base import BaseCommand
from accounts.models import User
import random
import string

class Command(BaseCommand):
    help = 'Create a new user with auto-generated password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('--first-name', type=str, default='', help='First name')
        parser.add_argument('--last-name', type=str, default='', help='Last name')
        parser.add_argument('--role', type=str, default='user', choices=['user', 'superadmin'], help='User role')
        parser.add_argument('--phone', type=str, default='', help='Phone number')

    def handle(self, *args, **options):
        try:
            # Generate strong password
            password = self.generate_strong_password()
            
            # Create user
            user = User.objects.create_user(
                email=options['email'],
                username=options['username'],
                first_name=options['first_name'],
                last_name=options['last_name'],
                role=options['role'],
                phone=options['phone'],
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'User created successfully!\n'
                    f'Email: {user.email}\n'
                    f'Username: {user.username}\n'
                    f'Password: {password}\n'
                    f'Role: {user.role}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating user: {str(e)}')
            )

    def generate_strong_password(self):
        """Generate a strong 12-character password"""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choices(chars, k=12))
        # Ensure at least one of each type
        password = random.choice(string.ascii_uppercase) + random.choice(string.ascii_lowercase) + random.choice(string.digits) + random.choice("!@#$%^&*") + password[4:]
        return password 