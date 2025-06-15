from django.db import migrations

def create_initial_pages(apps, schema_editor):
    Page = apps.get_model('accounts', 'Page')
    pages = [
        {
            'name': 'products_list',
            'description': 'List and manage products',
            'url': '/products'
        },
        {
            'name': 'marketing_list',
            'description': 'Marketing campaigns and initiatives',
            'url': '/marketing'
        },
        {
            'name': 'order_list',
            'description': 'View and manage orders',
            'url': '/orders'
        },
        {
            'name': 'media_plans',
            'description': 'Media planning and scheduling',
            'url': '/media-plans'
        },
        {
            'name': 'offer_pricing_skus',
            'description': 'Manage offers, pricing, and SKUs',
            'url': '/offers'
        },
        {
            'name': 'clients',
            'description': 'Client management and information',
            'url': '/clients'
        },
        {
            'name': 'suppliers',
            'description': 'Supplier management and details',
            'url': '/suppliers'
        },
        {
            'name': 'customer_support',
            'description': 'Customer support and ticket management',
            'url': '/support'
        },
        {
            'name': 'sales_reports',
            'description': 'Sales analytics and reporting',
            'url': '/sales'
        },
        {
            'name': 'finance_accounting',
            'description': 'Financial management and accounting',
            'url': '/finance'
        }
    ]
    
    for page_data in pages:
        Page.objects.create(**page_data)

def reverse_migration(apps, schema_editor):
    Page = apps.get_model('accounts', 'Page')
    Page.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_initial_pages, reverse_migration),
    ] 