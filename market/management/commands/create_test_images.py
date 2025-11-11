# management/commands/create_test_images.py
from django.core.management.base import BaseCommand
from market.models import Product, ProductImage
import random

class Command(BaseCommand):
    help = 'Create test product images'
    
    def handle(self, *args, **options):
        products = Product.objects.all()[:10]  # First 10 products
        
        # Sample Uploadcare UUIDs (these are fake - replace with real ones)
        sample_uuids = [
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "b2c3d4e5-f6g7-8901-bcde-f23456789012", 
            "c3d4e5f6-g7h8-9012-cdef-345678901234",
            "d4e5f6g7-h8i9-0123-defg-456789012345",
        ]
        
        created_count = 0
        
        for product in products:
            # Delete existing images
            product.images.all().delete()
            
            # Create 2-4 images per product
            num_images = random.randint(2, 4)
            
            for i in range(num_images):
                uuid = random.choice(sample_uuids) + f"-{i}"
                ProductImage.objects.create(
                    product=product,
                    image=uuid,
                    alt_text=f"Test image {i+1} for {product.name}",
                    is_primary=(i == 0),
                    order=i
                )
                created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Created {num_images} images for {product.name}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully created {created_count} test images!')
        )