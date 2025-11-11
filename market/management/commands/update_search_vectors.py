from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from market.models import Product

class Command(BaseCommand):
    help = 'Update PostgreSQL search vectors for products'
    
    def handle(self, *args, **options):
        self.stdout.write('Updating search vectors...')
        
        # Update search vectors for published products
        products = Product.objects.filter(status='published', is_active=True)
        
        with transaction.atomic():
            for product in products:
                product.search_vector = (
                    SearchVector('name', weight='A') +
                    SearchVector('description', weight='B') +
                    SearchVector('short_description', weight='B') +
                    SearchVector('brand', weight='C') +
                    SearchVector('tags', weight='C')
                )
                product.save(update_fields=['search_vector'])
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated search vectors for {products.count()} products')
        )