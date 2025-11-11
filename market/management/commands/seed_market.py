from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth import get_user_model
import random
from market.models import (
    Category, Shop, Product, ProductImage, ProductView, SponsoredRequest
)
from accounts.models import SellerProfile

class Command(BaseCommand):
    help = "Seeds the database with realistic e-commerce data."

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.WARNING("🧩 Starting realistic data seeding..."))

        # 1️⃣ Create Users
        users = []
        for i in range(5):
            email = f"seller{i}@example.com"
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "password": "12345678",
                    "user_type": "seller",
                    "is_active": True,
                    "is_staff": False,
                },
            )
            users.append(u)
        self.stdout.write(self.style.SUCCESS(f"✅ Created/Found {len(users)} sellers"))

        # 2️⃣ Create Shops
        Shop.objects.all().delete()
        shops = []
        shop_names = ["Tech Hub Tanzania", "Fashion Empire", "Home Essentials", "Sports Gear TZ", "Beauty Paradise"]
        for i in range(5):
            s = Shop.objects.create(
                seller=users[i],
                name=shop_names[i],
                slug=slugify(shop_names[i]),
                description=f"{shop_names[i]} offers the best products in Tanzania with fast delivery and great customer service.",
                phone=f"+25570000{i}00",
                email=f"shop{i}@example.com",
                region="Dar es Salaam",
                district="Ilala",
                ward="Kariakoo",
                street_address="Uhuru Street",
                website=f"https://{slugify(shop_names[i])}.co.tz",
                is_verified=True,
                rating=round(random.uniform(3.5, 5.0), 2),
            )
            shops.append(s)
        self.stdout.write(self.style.SUCCESS("✅ Created 5 shops"))

        # 3️⃣ Real Categories (without icon field)
        Category.objects.all().delete()
        category_data = [
            ("Electronics", "Phones, laptops, and accessories."),
            ("Fashion", "Clothing, shoes, and jewelry."),
            ("Home & Kitchen", "Furniture, appliances, and décor."),
            ("Beauty & Health", "Cosmetics, skincare, and supplements."),
            ("Sports & Outdoors", "Fitness gear, bicycles, and camping tools."),
            ("Toys & Games", "Children's toys and board games."),
        ]

        categories = []
        for name, desc in category_data:
            c = Category.objects.create(
                name=name,
                slug=slugify(name),
                description=desc,
            )
            categories.append(c)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(categories)} categories"))

        # 4️⃣ Real Product Images from Unsplash (ZOTE VALID)
        product_images = {
            "Electronics": [
                "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500&h=500&fit=crop",  # iPhone - ✅
                "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=500&h=500&fit=crop",  # Laptop - ✅
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&h=500&fit=crop",  # Headphones - ✅
                "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500&h=500&fit=crop",  # Camera - ✅
                "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=500&h=500&fit=crop",  # Smartwatch - ✅
            ],
            "Fashion": [
                "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=500&h=500&fit=crop",  # Jacket - ✅
                "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=500&h=500&fit=crop",  # Dress - ✅
                "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500&h=500&fit=crop",  # Shoes - ✅
                "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=500&h=500&fit=crop",  # Bag - ✅
                "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=500&h=500&fit=crop",  # Sunglasses - ✅
            ],
            "Home & Kitchen": [
                "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=500&h=500&fit=crop",  # Blender - ✅
                "https://images.unsplash.com/photo-1594736797933-d0ea3ff8db41?w=500&h=500&fit=crop",  # Microwave - ✅
                "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=500&h=500&fit=crop",  # Pan - ✅
                "https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=500&h=500&fit=crop",  # Vacuum - ✅
                "https://images.unsplash.com/photo-1570211776045-603a8b434cda?w=500&h=500&fit=crop",  # Kettle - ✅
            ],
            "Beauty & Health": [
                "https://images.unsplash.com/photo-1556228578-8c89e6adf883?w=500&h=500&fit=crop",  # Lotion - ✅
                "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=500&h=500&fit=crop",  # Makeup - ✅
                "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?w=500&h=500&fit=crop",  # Perfume - ✅
                "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=500&h=500&fit=crop",  # Skincare - ✅
                "https://images.unsplash.com/photo-1631549916768-4119b2e5f926?w=500&h=500&fit=crop",  # Hair - ✅
            ],
            "Sports & Outdoors": [
                "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=500&h=500&fit=crop",  # Bike - ✅
                "https://images.unsplash.com/photo-1614632537197-38a17061c2bd?w=500&h=500&fit=crop",  # Football - ✅
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop",  # Basketball - ✅
                "https://images.unsplash.com/photo-1504851149312-7a075b496cc7?w=500&h=500&fit=crop",  # Tent - ✅
                "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=500&fit=crop",  # Yoga - ✅
            ],
            "Toys & Games": [
                "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=500&h=500&fit=crop",  # LEGO - ✅
                "https://images.unsplash.com/photo-1550747534-8c4d3a5d8c0a?w=500&h=500&fit=crop",  # RC Car - ✅
                "https://images.unsplash.com/photo-1589878611824-eb3d1e5b4d6a?w=500&h=500&fit=crop",  # Doll - ✅
                "https://images.unsplash.com/photo-1596461404964-483dfa7c5b2e?w=500&h=500&fit=crop",  # Puzzle - ✅
                "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=500&h=500&fit=crop",  # Chess - ✅
            ]
        }

        # Product descriptions and details
        product_details = {
            "Electronics": {
                "brands": ["Apple", "Samsung", "Sony", "HP", "Dell", "Lenovo", "Canon", "Nikon", "Bose", "JBL"],
                "descriptions": [
                    "Latest model with advanced features and premium design",
                    "High-performance device with excellent battery life",
                    "Professional grade equipment for enthusiasts",
                    "Smart technology with innovative features",
                    "Premium quality with warranty included"
                ]
            },
            "Fashion": {
                "brands": ["Nike", "Adidas", "Puma", "Levi's", "Zara", "H&M", "Gucci", "Ray-Ban", "Casio", "Fossil"],
                "descriptions": [
                    "Premium quality materials with comfortable fit",
                    "Trendy design perfect for any occasion",
                    "Durable construction with stylish appearance",
                    "High-fashion item from renowned brand",
                    "Comfortable and versatile for daily wear"
                ]
            },
            "Home & Kitchen": {
                "brands": ["Philips", "Samsung", "LG", "Tefal", "Moulinex", "Kenwood", "IKEA", "HomePro", "KitchenAid", "Breville"],
                "descriptions": [
                    "Efficient and easy to use for everyday tasks",
                    "Durable construction with modern design",
                    "Energy efficient with smart features",
                    "Premium quality for long-lasting performance",
                    "User-friendly design with safety features"
                ]
            },
            "Beauty & Health": {
                "brands": ["Nivea", "L'Oreal", "Maybelline", "CeraVe", "Vaseline", "Oral-B", "Garnier", "Neutrogena", "Dove", "Pantene"],
                "descriptions": [
                    "Premium quality for effective results",
                    "Gentle formula suitable for all skin types",
                    "Professional grade for best performance",
                    "Natural ingredients with no harsh chemicals",
                    "Clinically tested and dermatologist recommended"
                ]
            },
            "Sports & Outdoors": {
                "brands": ["Nike", "Adidas", "Puma", "Under Armour", "Reebok", "Wilson", "Spalding", "Columbia", "The North Face", "Decathlon"],
                "descriptions": [
                    "Professional grade equipment for athletes",
                    "Durable construction for outdoor activities",
                    "Comfortable design with enhanced performance",
                    "Premium materials for long-lasting use",
                    "Innovative features for better results"
                ]
            },
            "Toys & Games": {
                "brands": ["LEGO", "Hasbro", "Mattel", "Nintendo", "Sony", "Fisher-Price", "Barbie", "Hot Wheels", "Play-Doh", "Ravensburger"],
                "descriptions": [
                    "Educational and fun for children development",
                    "High-quality materials for safe play",
                    "Interactive features for engaging experience",
                    "Durable construction for long-lasting fun",
                    "Age-appropriate design with learning benefits"
                ]
            }
        }

        # 4️⃣ Create Real Products
        Product.objects.all().delete()
        ProductImage.objects.all().delete()
        ProductView.objects.all().delete()

        category_products = {
            "Electronics": [
                ("iPhone 14 Pro", 1200000, 1500000),
                ("Samsung Galaxy S23", 850000, 1100000),
                ("MacBook Air M2", 2200000, 2800000),
                ("Dell XPS 13", 1800000, 2300000),
                ("Sony WH-1000XM5 Headphones", 350000, 450000),
            ],
            "Fashion": [
                ("Men's Leather Jacket", 85000, 120000),
                ("Women's Summer Dress", 45000, 65000),
                ("Nike Air Max Shoes", 120000, 160000),
                ("Adidas Ultraboost", 130000, 170000),
                ("Ray-Ban Aviator Sunglasses", 80000, 110000),
            ],
            "Home & Kitchen": [
                ("Electric Blender", 45000, 65000),
                ("Microwave Oven", 120000, 160000),
                ("Non-stick Pan Set", 55000, 80000),
                ("Vacuum Cleaner", 85000, 120000),
                ("Electric Kettle", 35000, 50000),
            ],
            "Beauty & Health": [
                ("Nivea Body Lotion", 12000, 18000),
                ("Maybelline Mascara", 15000, 22000),
                ("Vaseline Lip Balm", 8000, 12000),
                ("Oral-B Toothpaste", 10000, 15000),
                ("CeraVe Moisturizer", 18000, 25000),
            ],
            "Sports & Outdoors": [
                ("Mountain Bike", 250000, 350000),
                ("Football", 25000, 40000),
                ("Basketball", 20000, 35000),
                ("Camping Tent", 80000, 120000),
                ("Yoga Mat", 15000, 25000),
            ],
            "Toys & Games": [
                ("LEGO City Set", 45000, 65000),
                ("Remote Control Car", 30000, 45000),
                ("Barbie Doll", 25000, 40000),
                ("Hot Wheels Track", 35000, 55000),
                ("Puzzle 1000 Pieces", 20000, 35000),
            ],
        }

        products = []
        product_count = 0
        
        for category in categories:
            category_name = category.name
            product_list = category_products[category_name]
            category_images = product_images[category_name]
            category_details = product_details[category_name]
            
            for i, (name, price, compare_price) in enumerate(product_list):
                # Select appropriate image for this product
                image_index = i % len(category_images)
                product_image = category_images[image_index]
                
                # Select brand and description
                brand = random.choice(category_details["brands"])
                description = random.choice(category_details["descriptions"])
                
                p = Product.objects.create(
                    name=name,
                    slug=slugify(f"{name}-{brand}"),
                    description=f"{name} by {brand}. {description} Available now at competitive prices with warranty.",
                    short_description=f"Premium {category_name.lower()} product from {brand}",
                    category=category,
                    shop=random.choice(shops),
                    price=price,
                    compare_price=compare_price,
                    cost_price=int(price * 0.6),  # 60% of selling price
                    stock_quantity=random.randint(10, 100),
                    brand=brand,
                    weight=round(random.uniform(0.1, 5.0), 2),
                    dimensions=f"{random.randint(10,50)}x{random.randint(5,30)}x{random.randint(2,15)} cm",
                    specifications={
                        "color": random.choice(["Black", "White", "Silver", "Red", "Blue", "Green"]),
                        "material": random.choice(["Plastic", "Metal", "Wood", "Fabric", "Leather"]),
                        "warranty": f"{random.randint(1,3)} years"
                    },
                    status="published",
                    is_active=True,
                    is_featured=random.choice([True, False, False, False]),  # 25% chance
                    is_sponsored=random.choice([True, False, False, False, False]),  # 20% chance
                    published_at=timezone.now(),
                )
                
                # Create primary product image
                ProductImage.objects.create(
                    product=p,
                    image=product_image,
                    alt_text=f"{name} - {brand}",
                    is_primary=True,
                )
                
                # Add 1-2 additional images for some products
                if random.choice([True, False]):
                    additional_image_index = (i + 1) % len(category_images)
                    ProductImage.objects.create(
                        product=p,
                        image=category_images[additional_image_index],
                        alt_text=f"{name} - Alternate view",
                        is_primary=False,
                    )
                
                products.append(p)
                product_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Created {product_count} products with real images"))

        # 5️⃣ Product Views (simulate user activity)
        for p in products:
            # Create multiple views for each product
            for _ in range(random.randint(5, 20)):
                ProductView.objects.create(
                    product=p,
                    user=random.choice(users) if random.choice([True, False]) else None,
                    ip_address=f"192.168.1.{random.randint(1,255)}",
                    user_agent=random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                    ]),
                )
        self.stdout.write(self.style.SUCCESS("✅ Added product views"))

        # 6️⃣ Sponsored Requests
        SponsoredRequest.objects.all().delete()
        for i in range(15):
            product = random.choice(products)
            sr = SponsoredRequest.objects.create(
                product=product,
                seller=product.shop.seller,
                title=f"Promote {product.name}",
                description=f"Marketing campaign for {product.name} to reach more customers in Tanzania",
                budget=random.randint(50000, 500000),
                duration_days=random.randint(7, 60),
                status=random.choice(["pending", "approved", "active", "completed"]),
                created_at=timezone.now() - timezone.timedelta(days=random.randint(1, 30))
            )
            # Target relevant categories
            target_categories = [product.category]
            other_categories = [c for c in categories if c != product.category]
            target_categories.extend(random.sample(other_categories, min(2, len(other_categories))))
            sr.target_categories.set(target_categories)
        
        self.stdout.write(self.style.SUCCESS("✅ Created sponsored requests"))

        # 7️⃣ Update seller profiles - FIXED: Using correct fields for SellerProfile
        for user in users:
            profile, created = SellerProfile.objects.get_or_create(
                user=user,
                defaults={
                    # Using only fields that actually exist in your SellerProfile model
                    'bio': f"Professional seller with {random.randint(1, 10)} years of experience in e-commerce",
                    'location': random.choice(['Dar es Salaam', 'Arusha', 'Mwanza', 'Dodoma', 'Mbeya']),
                    'website': f"https://{slugify(user.email.split('@')[0])}.co.tz",
                }
            )
            # If profile already exists, just update it
            if not created:
                profile.bio = f"Professional seller with {random.randint(1, 10)} years of experience in e-commerce"
                profile.location = random.choice(['Dar es Salaam', 'Arusha', 'Mwanza', 'Dodoma', 'Mbeya'])
                profile.website = f"https://{slugify(user.email.split('@')[0])}.co.tz"
                profile.save()
        
        self.stdout.write(self.style.SUCCESS("✅ Updated seller profiles"))

        self.stdout.write(self.style.SUCCESS("🎉 DONE! Database fully seeded with realistic e-commerce data!"))
        self.stdout.write(self.style.SUCCESS("📊 Summary:"))
        self.stdout.write(self.style.SUCCESS(f"   - {len(users)} sellers"))
        self.stdout.write(self.style.SUCCESS(f"   - {len(shops)} shops"))
        self.stdout.write(self.style.SUCCESS(f"   - {len(categories)} categories"))
        self.stdout.write(self.style.SUCCESS(f"   - {len(products)} products"))
        self.stdout.write(self.style.SUCCESS(f"   - {ProductView.objects.count()} product views"))
        self.stdout.write(self.style.SUCCESS(f"   - {SponsoredRequest.objects.count()} sponsored requests"))
#python manage.py seed_market