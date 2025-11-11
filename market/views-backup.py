from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from .forms import ProductSearchForm
from .models import Category, Product, ProductView, Shop, SearchHistory, SponsoredRequest,ProductImage
from .search import AdvancedProductSearch
from .forms import ProductForm  # ← HAKIKISHA HII IKO
from .recommendations import RecommendationEngine



class ProductSearchView(ListView):
    model = Product
    template_name = 'market/search_results.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        category_slug = self.request.GET.get('category', '')
        
        if query:
            # Use advanced search
            search_engine = AdvancedProductSearch(self.request, query)
            
            # Get filters
            filters = {
                'min_price': self.request.GET.get('min_price'),
                'max_price': self.request.GET.get('max_price'),
            }
            
            return search_engine.search(category_slug, filters)
        else:
            # Fallback to basic filtering
            queryset = Product.objects.filter(
                is_active=True, 
                status='published'
            ).select_related('category', 'shop').prefetch_related('images')
            
            if category_slug:
                category = get_object_or_404(Category, slug=category_slug, is_active=True)
                queryset = queryset.filter(category=category)
            
            return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        category_slug = self.request.GET.get('category', '')
        
        # Get search suggestions
        search_engine = AdvancedProductSearch(self.request, query)
        
        # Get recommendations
        rec_engine = RecommendationEngine(self.request)
        
        context.update({
            'query': query,
            'category_slug': category_slug,
            'suggestions': search_engine.get_search_suggestions(),
            'categories': Category.objects.filter(is_active=True),
            'sponsored_count': self.get_queryset().filter(is_sponsored=True).count(),
            'recommendations': rec_engine.get_recommendations(),
            'trending_products': rec_engine.get_trending_products(),
        })
        return context



def track_sponsored_click(request, sponsored_id):
    """Track clicks on sponsored products"""
    sponsored = get_object_or_404(SponsoredRequest, id=sponsored_id)
    
    if sponsored.is_active():
        sponsored.record_click()
        
        # Redirect to product page
        return redirect(sponsored.product.get_absolute_url())
    
    return redirect('market:home')

def search_analytics(request):
    """Get search analytics for admin/sellers"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Get popular search terms
    popular_searches = SearchHistory.objects.values('query').annotate(
        search_count=Count('query'),
        avg_results=Count('results_count')
    ).order_by('-search_count')[:10]
    
    # Get search trends
    recent_searches = SearchHistory.objects.filter(
        created_at__gte=timezone.now()-timezone.timedelta(days=30)
    ).extra({'date': "date(created_at)"}).values('date').annotate(
        daily_searches=Count('id')
    ).order_by('date')
    
    return JsonResponse({
        'popular_searches': list(popular_searches),
        'search_trends': list(recent_searches)
    })




def track_product_view(product, request):
    """Track product views for analytics"""
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    ProductView.objects.create(
        product=product,
        user=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

class CategoryListView(ListView):
    model = Category
    template_name = 'market/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(
            is_active=True, 
            parent__isnull=True
        ).prefetch_related('children').annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        )

class ProductListView(ListView):
    model = Product
    template_name = 'market/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True, 
            status='published'
        ).select_related('category', 'shop').prefetch_related('images')
        
        # Filter by category if provided
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            queryset = queryset.filter(category=category)
        
        # Search functionality
        search_form = ProductSearchForm(self.request.GET)
        if search_form.is_valid():
            query = search_form.cleaned_data.get('q')
            category = search_form.cleaned_data.get('category')
            min_price = search_form.cleaned_data.get('min_price')
            max_price = search_form.cleaned_data.get('max_price')
            
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(short_description__icontains=query) |
                    Q(brand__icontains=query)
                )
            
            if category:
                queryset = queryset.filter(category=category)
            
            if min_price:
                queryset = queryset.filter(price__gte=min_price)
            
            if max_price:
                queryset = queryset.filter(price__lte=max_price)
        
        # Ordering
        ordering = self.request.GET.get('ordering', '-created_at')
        if ordering in ['price', '-price', 'name', '-name', '-created_at', '-view_count']:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = ProductSearchForm(self.request.GET)
        context['categories'] = Category.objects.filter(is_active=True)
        
        # Get current category if exists
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(Category, slug=category_slug)
        
        return context

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'shop')
                       .prefetch_related('images', 'views'),
        slug=slug, 
        is_active=True,
        status='published'
    )
    
    # Track view with caching
    track_product_view(product, request)
    product.increment_views()  # ADD THIS LINE
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        status='published'
    ).exclude(id=product.id).select_related('shop').prefetch_related('images')[:8]
    
    # Get recommendations
    rec_engine = RecommendationEngine(request)
    recommendations = rec_engine.get_recommendations(product)
    
    # Get primary image and other images
    primary_image = product.images.filter(is_primary=True).first()
    other_images = product.images.exclude(id=primary_image.id if primary_image else None)[:3]
    
    context = {
        'product': product,
        'related_products': related_products,
        'recommendations': recommendations,
        'primary_image': primary_image,
        'other_images': other_images,
        'view_count': product.view_count,
    }
    
    return render(request, 'market/product_detail.html', context)



def shop_detail(request, slug):
    shop = get_object_or_404(
        Shop.objects.select_related('seller')
                    .prefetch_related('products'),
        slug=slug, 
        is_active=True
    )
    
    # Get all products for this shop
    products = shop.products.filter(
        is_active=True, 
        status='published'
    ).select_related('category').prefetch_related('images')
    
    # Check if user is the shop owner
    is_owner = request.user.is_authenticated and request.user == shop.seller
    
    # Get owner's products (including drafts if owner)
    owner_products = products
    if is_owner:
        owner_products = shop.products.filter(is_active=True).select_related('category').prefetch_related('images')
    
    # Handle filtering for owners
    status_filter = request.GET.get('status')
    if is_owner and status_filter:
        owner_products = owner_products.filter(status=status_filter)
    
    # Pagination for public products
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get product statistics
    product_stats = {
        'total': products.count(),
        'published': products.filter(status='published').count(),
        'draft': products.filter(status='draft').count() if is_owner else 0,
        'out_of_stock': products.filter(status='out_of_stock').count(),
    }
    
    context = {
        'shop': shop,
        'products': page_obj,
        'owner_products': owner_products,
        'is_owner': is_owner,
        'product_count': products.count(),
        'product_stats': product_stats,
        'form': ProductForm() if is_owner else None,
    }
    
    return render(request, 'market/shop_detail.html', context)
@login_required
def add_product(request, shop_slug):
    shop = get_object_or_404(Shop, slug=shop_slug, is_active=True)
    
    if request.user != shop.seller:
        return JsonResponse({
            'success': False, 
            'message': 'You are not authorized to add products to this shop'
        }, status=403)
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.shop = shop
                product.seller = request.user
                product.save()
                
                # Handle multiple images from request.FILES directly
                images = request.FILES.getlist('images')
                for i, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=(i == 0),
                        order=i
                    )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Product added successfully!',
                    'product_id': product.id
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error saving product: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': form.errors
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

def categories_json(request):
    categories = Category.objects.filter(is_active=True).values('id', 'name')
    return JsonResponse({'categories': list(categories)})




# def shop_detail(request, slug):
#     shop = get_object_or_404(
#         Shop.objects.select_related('seller')
#                     .prefetch_related('products'),
#         slug=slug, 
#         is_active=True
#     )
    
#     products = shop.products.filter(
#         is_active=True, 
#         status='published'
#     ).select_related('category').prefetch_related('images')
    
#     # Pagination
#     paginator = Paginator(products, 12)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     context = {
#         'shop': shop,
#         'products': page_obj,
#         'product_count': products.count(),
#     }
    
#     return render(request, 'market/shop_detail.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []
    
    if len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query),
            is_active=True,
            status='published'
        )[:10]
        
        categories = Category.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]
        
        suggestions = [
            {
                'type': 'product',
                'name': product.name,
                'url': product.get_absolute_url(),
                'price': str(product.price),
                'image': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else ''
            }
            for product in products
        ]
        
        suggestions.extend([
            {
                'type': 'category',
                'name': category.name,
                'url': category.get_absolute_url(),
                'product_count': category.product_count
            }
            for category in categories
        ])
    
    return JsonResponse({'suggestions': suggestions})

def featured_products(request):
    products = Product.objects.filter(
        is_active=True,
        status='published',
        is_featured=True
    ).select_related('category', 'shop').prefetch_related('images')[:8]
    
    context = {
        'featured_products': products,
        'title': _('Featured Products')
    }
    
    return render(request, 'market/featured_products.html', context)

def sponsored_products(request):
    products = Product.objects.filter(
        is_active=True,
        status='published',
        is_sponsored=True
    ).select_related('category', 'shop').prefetch_related('images')[:12]
    
    context = {
        'sponsored_products': products,
        'title': _('Sponsored Products')
    }
    
    return render(request, 'market/sponsored_products.html', context)




from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def create_shop(request):
    """Create a new shop for the seller"""
    # Check if user already has a shop
    if hasattr(request.user, 'shop'):
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = ShopForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # FIX: Let the model handle unique slug generation
                shop = form.save(commit=False)
                shop.seller = request.user
                
                # Update user type to seller
                if request.user.user_type == 'buyer':
                    request.user.user_type = 'both'
                    request.user.save()
                
                shop.save()
                messages.success(request, _('Shop created successfully!'))
                return redirect('dashboard:dashboard')
                
            except IntegrityError:
                # Handle slug conflict
                messages.error(request, _('Shop name already exists. Please choose a different name.'))
                return render(request, 'market/create_shop.html', {'form': form})
                
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = ShopForm()
    
    return render(request, 'market/create_shop.html', {'form': form})

@login_required
def shop_dashboard(request):
    """Shop management dashboard"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji kufikia ukurasa huu!')
        return redirect('accounts:upgrade_seller')
    
    try:
        shop = Shop.objects.get(user=request.user)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    products = Product.objects.filter(shop=shop)
    
    context = {
        'shop': shop,
        'products': products,
    }
    return render(request, 'market/shop_dashboard.html', context)




    
@login_required
def shop_dashboard(request):
    """Shop management dashboard"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji kufikia ukurasa huu!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    products = Product.objects.filter(shop=shop)
    
    context = {
        'shop': shop,
        'products': products,
    }
    return render(request, 'market/shop_dashboard.html', context)

@login_required
def product_list(request):
    """List all products for the seller"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji kufikia ukurasa huu!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
        products = Product.objects.filter(shop=shop)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    context = {
        'products': products,
        'shop': shop,
    }
    return render(request, 'market/product_list.html', context)



@login_required
def create_shop(request):
    """Create a new shop"""
    if not request.user.is_seller:
        messages.error(request, 'Unahitaji kuwa muuzaji kuanza duka!')
        return redirect('accounts:upgrade_seller')
    
    # Check if user already has a shop
    if Shop.objects.filter(seller=request.user).exists():
        messages.info(request, 'Tayari una duka!')
        return redirect('market:shop_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        region = request.POST.get('region', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        district = request.POST.get('district', '')
        ward = request.POST.get('ward', '')
        street_address = request.POST.get('street_address', '')
        
        if name:
            shop = Shop.objects.create(
                seller=request.user,
                name=name,
                description=description,
                region=region,
                email=email or request.user.email,
                phone=phone or request.user.phone_number,
                district=district,
                ward=ward,
                street_address=street_address,
            )
            messages.success(request, f'Duka "{name}" limeundwa kikamilifu! Sasa unaweza kuongeza bidhaa.')
            return redirect('market:shop_dashboard')
        else:
            messages.error(request, 'Jina la duka linahitajika!')
    
    return render(request, 'market/create_shop.html')

@login_required
def shop_edit(request):
    """Edit shop details"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    if request.method == 'POST':
        shop.name = request.POST.get('name', shop.name)
        shop.description = request.POST.get('description', shop.description)
        shop.location = request.POST.get('location', shop.location)
        shop.contact_email = request.POST.get('contact_email', shop.contact_email)
        shop.contact_phone = request.POST.get('contact_phone', shop.contact_phone)
        shop.save()
        
        messages.success(request, 'Maelezo ya duka yamebadilishwa!')
        return redirect('market:shop_dashboard')
    
    context = {
        'shop': shop,
    }
    return render(request, 'market/shop_edit.html', context)

@login_required
def product_create(request):
    """Create a new product"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
    except Shop.DoesNotExist:
        messages.error(request, 'Unahtaji kuwa na duka kwanza!')
        return redirect('market:create_shop')
    
    # Add your product creation logic here
    return render(request, 'market/product_create.html', {'shop': shop})

@login_required
def product_edit(request, pk):
    """Edit a product"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
        product = get_object_or_404(Product, pk=pk, shop=shop)
    except Shop.DoesNotExist:
        messages.error(request, 'Unahtaji kuwa na duka kwanza!')
        return redirect('market:create_shop')
    
    # Add your product editing logic here
    context = {
        'product': product,
        'shop': shop,
    }
    return render(request, 'market/product_edit.html', context)

@login_required
def product_delete(request, pk):
    """Delete a product"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user
        shop = Shop.objects.get(seller=request.user)
        product = get_object_or_404(Product, pk=pk, shop=shop)
    except Shop.DoesNotExist:
        messages.error(request, 'Unahtaji kuwa na duka kwanza!')
        return redirect('market:create_shop')
    
    # Add your product deletion logic here
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Bidhaa imefutwa!')
        return redirect('market:product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'market/product_delete.html', context)


