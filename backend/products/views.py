import os
import json
import uuid
import requests
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.contrib import messages
from .models import Product, Order, OrderItem, Address
from .search import search_products

def get_env_credentials():
    env_email = "admin@gmail.com"
    env_pass = "123456"
    
    possible_paths = [
        settings.BASE_DIR / ".env",
        settings.BASE_DIR.parent / ".env",
    ]
    for env_path in possible_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ADMIN_EMAIL="):
                            env_email = line.split("=", 1)[1].strip('"\' ')
                        elif line.startswith("ADMIN_PASSWORD="):
                            env_pass = line.split("=", 1)[1].strip('"\' ')
            except Exception:
                pass
            break
    return env_email, env_pass

def upload_photo_to_supabase(file_obj):
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    bucket = os.getenv("SUPABASE_BUCKET", "products").strip()
    
    if supabase_url and supabase_key:
        ext = file_obj.name.split('.')[-1] if '.' in file_obj.name else 'jpg'
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_url = f"{supabase_url}/storage/v1/object/{bucket}/{filename}"
        
        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "apikey": supabase_key,
            "Content-Type": getattr(file_obj, 'content_type', 'application/octet-stream'),
        }
        try:
            resp = requests.post(upload_url, headers=headers, data=file_obj.read(), timeout=10)
            if resp.status_code in (200, 201):
                return f"{supabase_url}/storage/v1/object/public/{bucket}/{filename}"
        except Exception:
            pass
    return None

def seed_initial_products():
    pass

def login_view(request):
    if request.session.get('is_admin'):
        return redirect('admin_dashboard')
    if request.user.is_authenticated:
        next_url = request.GET.get('next', 'home')
        return redirect(next_url)
        
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        # 1. Check admin credentials first
        env_email, env_pass = get_env_credentials()
        if email == env_email and password == env_pass:
            request.session['is_admin'] = True
            return redirect('admin_dashboard')
            
        # 2. Check regular user credentials — look up by email, then authenticate by username
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            error = "Invalid email or password."
            
    return render(request, 'products/login.html', {'error': error, 'next': request.GET.get('next', '')})

def signup_view(request):
    if request.session.get('is_admin'):
        return redirect('admin_dashboard')
    if request.user.is_authenticated:
        next_url = request.GET.get('next', 'home')
        return redirect(next_url)
        
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        username = request.POST.get('username', '').strip()
        
        if User.objects.filter(email=email).exists():
            error = "A user with that email already exists."
        elif User.objects.filter(username=username).exists():
            error = "That username is already taken."
        elif email and password and username:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            error = "Please fill in all fields."
            
    return render(request, 'products/signup.html', {'error': error, 'next': request.GET.get('next', '')})

def logout_view(request):
    # Preserve cart before flush
    cart = request.session.get('cart', {})
    request.session.flush()
    logout(request)
    # Restore cart for next session
    request.session['cart'] = cart
    request.session.modified = True
    return redirect('home')

def get_cart_data(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    for pk, quantity in cart.items():
        try:
            product = Product.objects.get(pk=pk)
            price = product.discount_price if product.discount_price else product.price
            total_price = price * quantity
            subtotal += total_price
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': total_price
            })
        except Product.DoesNotExist:
            continue
    return cart_items, subtotal

def cart_view(request):
    cart_items, subtotal = get_cart_data(request)
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal
    })

def add_to_cart(request, pk):
    if request.method == 'POST':
        try:
            product = Product.objects.get(pk=pk)
            if product.stock <= 0:
                return redirect('product_detail', pk=pk)
            
            quantity = int(request.POST.get('quantity', 1))
            cart = request.session.get('cart', {})
            cart[str(pk)] = cart.get(str(pk), 0) + quantity
            
            if cart[str(pk)] > product.stock:
                cart[str(pk)] = product.stock
                
            request.session['cart'] = cart
            request.session.modified = True
        except (Product.DoesNotExist, ValueError):
            pass
    return redirect('cart')

def remove_from_cart(request, pk):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if str(pk) in cart:
            del cart[str(pk)]
            request.session['cart'] = cart
            request.session.modified = True
    return redirect('cart')

def update_cart(request, pk):
    if request.method == 'POST':
        try:
            product = Product.objects.get(pk=pk)
            quantity = int(request.POST.get('quantity', 1))
            cart = request.session.get('cart', {})
            
            if quantity <= 0:
                if str(pk) in cart:
                    del cart[str(pk)]
            else:
                cart[str(pk)] = min(quantity, product.stock)
                
            request.session['cart'] = cart
            request.session.modified = True
        except (Product.DoesNotExist, ValueError):
            pass
    return redirect('cart')

def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    products = Product.objects.all().order_by('-created_at')
    
    # Real sales data from orders
    orders = Order.objects.all()
    completed_orders = orders.filter(status='DELIVERED')
    
    total_revenue = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    total_orders = completed_orders.count()
    pending_orders = orders.filter(status='PENDING').count()
    
    # Best seller: the product with the most ordered quantity
    best_seller_data = OrderItem.objects.filter(
        order__status='DELIVERED'
    ).values('product_name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty').first()
    best_seller = best_seller_data['product_name'] if best_seller_data else 'N/A'
    best_seller_qty = best_seller_data['total_qty'] if best_seller_data else 0
    
    # Monthly sales (last 6 months)
    from django.utils import timezone
    from calendar import monthrange
    
    now = timezone.now()
    monthly_data = []
    
    for i in range(5, -1, -1):
        month_num = now.month - i
        year_offset = 0
        while month_num < 1:
            month_num += 12
            year_offset -= 1
        
        month_start = now.replace(
            year=now.year + year_offset,
            month=month_num,
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        _, last_day = monthrange(month_start.year, month_start.month)
        month_end = month_start.replace(day=last_day, hour=23, minute=59, second=59, microsecond=999999)
        
        month_orders = completed_orders.filter(
            created_at__gte=month_start,
            created_at__lte=month_end
        )
        month_total = month_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        month_name = month_start.strftime('%b')
        monthly_data.append({
            'month': month_name,
            'amount': month_total,
        })
    
    # Calculate max for bar heights
    max_monthly = max((m['amount'] for m in monthly_data), default=0)
    for m in monthly_data:
        if max_monthly > 0:
            pct = (m['amount'] / max_monthly) * 100
            m['height'] = f'{pct:.0f}%'
        else:
            m['height'] = '0%'
    
    # Recent orders for the table
    recent_orders = orders[:10]
    
    sales_data = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'best_seller': best_seller,
        'best_seller_qty': best_seller_qty,
        'monthly_sales': monthly_data,
        'recent_orders': recent_orders,
    }
    
    # All orders for the Orders management tab
    all_orders = Order.objects.all()
    
    return render(request, 'products/admin_dashboard.html', {
        'products': products,
        'sales': sales_data,
        'all_orders': all_orders,
        'admin_email': get_env_credentials()[0]
    })

def update_order_status(request, pk):
    if not request.session.get('is_admin'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Not authenticated'}, status=403)
        return redirect('admin_login')
    
    if request.method == 'POST':
        order = get_object_or_404(Order, pk=pk)
        action = request.POST.get('action', '').strip()
        
        success = False
        message = ''
        
        if action == 'cancel':
            if order.status in ('DELIVERED', 'CANCELLED'):
                message = f'Order #{order.id} cannot be cancelled (status: {order.get_status_display()}).'
            else:
                order.status = 'CANCELLED'
                order.save()
                success = True
                message = f'Order #{order.id} has been cancelled.'
        elif action == 'advance':
            next_status = order.get_next_status_code()
            if next_status:
                order.status = next_status
                order.save()
                success = True
                message = f'Order #{order.id} status advanced to {order.get_status_display()}.'
            else:
                message = f'Order #{order.id} cannot be advanced further (status: {order.get_status_display()}).'
        else:
            message = 'Invalid action.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'order_id': order.id,
                'new_status': order.status,
                'new_status_display': order.get_status_display(),
                'next_status_code': order.get_next_status_code(),
                'next_status_display': order.get_next_status_display(),
            })
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('admin_dashboard')


def add_product(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'INDOORS').strip()
        price = request.POST.get('price', '0').replace(',', '').replace('₹', '').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        photo = request.FILES.get('photo')
        
        saved_url = None
        if photo:
            saved_url = upload_photo_to_supabase(photo)
            
        if name and price:
            if saved_url:
                Product.objects.create(name=name, category=category, price=price, description=description, image_url=saved_url)
            elif photo:
                Product.objects.create(name=name, category=category, price=price, description=description, image_file=photo)
            else:
                if not image_url:
                    image_url = "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"
                Product.objects.create(name=name, category=category, price=price, description=description, image_url=image_url)
                
    return redirect('admin_dashboard')

def delete_product(request, pk):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    if request.method == 'POST':
        Product.objects.filter(pk=pk).delete()
    return redirect('admin_dashboard')

def home_view(request):
    featured_products = Product.objects.filter(stock__gt=0).order_by('-created_at')[:6]
    return render(request, 'products/home.html', {'featured_products': featured_products})

def category_listing(request, cat_code, template_name):
    q = request.GET.get('q', '').strip()
    if q:
        products = search_products(q, category=cat_code)
    else:
        products = Product.objects.filter(category=cat_code, stock__gt=0).order_by('-created_at')
    return render(request, template_name, {'products': products})

def indoors_view(request):
    return category_listing(request, 'INDOORS', 'products/listing.html')

def outdoors_view(request):
    return category_listing(request, 'OUTDOORS', 'products/outdoors.html')

def parts_view(request):
    return category_listing(request, 'PARTS', 'products/parts.html')

def mrsports_view(request):
    return category_listing(request, 'MRSPORTS', 'products/mrsports.html')

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)
        
    # Determine the back link based on product category
    category_url_map = {
        'INDOORS': ('indoors', 'Indoor Equipment'),
        'OUTDOORS': ('outdoors', 'Outdoor Equipment'),
        'PARTS': ('parts', 'Spare Parts'),
        'MRSPORTS': ('mrsports', 'MR Sports'),
    }
    back_url_name, back_label = category_url_map.get(product.category, ('home', 'Home'))
    
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk).exclude(stock__lte=0).order_by('-created_at')[:3]
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products,
        'back_url_name': back_url_name,
        'back_label': back_label,
    })

def search_view(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    
    if category.lower() == 'all' or not category:
        category = None
        
    products_list = search_products(q, category)
    
    paginator = Paginator(products_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/search_results.html', {
        'page_obj': page_obj,
        'q': q,
        'category': category,
    })
def profile_view(request):
    """User profile with address management (max 3 addresses)."""
    if not request.user.is_authenticated:
        return redirect(reverse('admin_login') + '?next=' + request.path)

    addresses = Address.objects.filter(user=request.user)
    error = None
    success = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_profile':
            email = request.POST.get('email', '').strip()
            new_username = request.POST.get('username', '').strip()

            if email:
                if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                    error = 'This email is already taken.'
                else:
                    request.user.email = email
                    request.user.save()
                    success = 'Profile updated successfully!'

        elif action == 'add_address':
            if addresses.count() >= 3:
                error = 'You can only save up to 3 addresses.'
            else:
                label = request.POST.get('label', 'Home').strip()
                full_address = request.POST.get('full_address', '').strip()
                city = request.POST.get('city', '').strip()
                state = request.POST.get('state', '').strip()
                pincode = request.POST.get('pincode', '').strip()
                phone = request.POST.get('phone', '').strip()
                is_default = request.POST.get('is_default') == 'on'

                if full_address and city and state and pincode:
                    # If setting as default, unset other defaults
                    if is_default:
                        addresses.filter(is_default=True).update(is_default=False)
                    Address.objects.create(
                        user=request.user,
                        label=label,
                        full_address=full_address,
                        city=city,
                        state=state,
                        pincode=pincode,
                        phone=phone,
                        is_default=is_default,
                    )
                    success = f'Address "{label}" added successfully!'
                else:
                    error = 'Please fill in all required address fields.'

        elif action == 'edit_address':
            addr_id = request.POST.get('address_id')
            try:
                addr = Address.objects.get(pk=addr_id, user=request.user)
                addr.label = request.POST.get('label', addr.label).strip()
                addr.full_address = request.POST.get('full_address', '').strip() or addr.full_address
                addr.city = request.POST.get('city', '').strip() or addr.city
                addr.state = request.POST.get('state', '').strip() or addr.state
                addr.pincode = request.POST.get('pincode', '').strip() or addr.pincode
                addr.phone = request.POST.get('phone', '').strip()
                is_default = request.POST.get('is_default') == 'on'
                if is_default:
                    addresses.filter(is_default=True).update(is_default=False)
                addr.is_default = is_default
                addr.save()
                success = f'Address "{addr.label}" updated!'
            except Address.DoesNotExist:
                error = 'Address not found.'

        elif action == 'delete_address':
            addr_id = request.POST.get('address_id')
            try:
                addr = Address.objects.get(pk=addr_id, user=request.user)
                addr.delete()
                success = f'Address "{addr.label}" deleted.'
            except Address.DoesNotExist:
                error = 'Address not found.'

        # Re-fetch after changes
        addresses = Address.objects.filter(user=request.user)

    return render(request, 'products/profile.html', {
        'addresses': addresses,
        'error': error,
        'success': success,
        'address_limit': 3,
        'addresses_remaining': max(0, 3 - addresses.count()),
    })


def checkout_view(request):
    cart_items, subtotal = get_cart_data(request)
    
    if not cart_items:
        messages.error(request, 'Your cart is empty!')
        return redirect('cart')
    
    # Get saved addresses for logged-in users
    saved_addresses = []
    if request.user.is_authenticated:
        saved_addresses = Address.objects.filter(user=request.user)
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        shipping_address = request.POST.get('shipping_address', '').strip()
        
        # For logged-in users, use their info
        if request.user.is_authenticated:
            if not customer_name:
                customer_name = request.user.username
            if not customer_email:
                customer_email = request.user.email
        
        if not customer_name or not customer_email:
            messages.error(request, 'Please provide your name and email.')
            return render(request, 'products/checkout.html', {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'total': subtotal,
            })
        
        # Validate stock availability before creating order
        for item in cart_items:
            product = item['product']
            if product.stock < item['quantity']:
                messages.error(request, f'Insufficient stock for "{product.name}". Only {product.stock} available.')
                return redirect('cart')
        
        # Create the order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            total_amount=subtotal,
            status='PENDING',
            payment_status='PENDING',
        )
        
        # Create order items and deduct stock
        for item in cart_items:
            product = item['product']
            price = float(product.discount_price) if product.discount_price else float(product.price)
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku or '',
                quantity=item['quantity'],
                price=price,
                total_price=float(item['total_price']),
            )
            # Deduct stock
            if product.stock:
                product.stock -= item['quantity']
                if product.stock < 0:
                    product.stock = 0
                product.save()
        
        # Clear the cart
        request.session['cart'] = {}
        request.session.modified = True
        
        messages.success(request, 'Order placed successfully!')
        return redirect('order_confirmation', pk=order.pk)
    
    return render(request, 'products/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'saved_addresses': saved_addresses,
    })


def order_confirmation_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'products/order_confirmation.html', {
        'order': order
    })


def search_suggestions_api(request):
    """Return JSON autocomplete suggestions for products."""
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    if len(q) < 1:
        return JsonResponse({'results': []})

    products = Product.objects.filter(
        Q(name__icontains=q) | Q(sku__icontains=q)
    )
    if category:
        products = products.filter(category=category)

    products = products.order_by('-created_at')[:8]

    results = []
    for p in products:
        results.append({
            'id': p.pk,
            'name': p.name,
            'price': str(p.discount_price) if p.discount_price else str(p.price),
            'image': p.display_image,
            'url': reverse('product_detail', args=[p.pk]),
        })

    return JsonResponse({'results': results})


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get("message", "").strip()
        history = data.get("history", [])
    except Exception:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    api_key = os.getenv("GROQ_API_KEY", "")
    
    system_prompt = (
        "You are Mohanlal, the friendly, enthusiastic, and knowledgeable AI assistant and mascot for Little Fingers India / Mohanlal website. "
        "We specialize in premium children's playground equipment, indoor & outdoor toys, MR sports gear, educational furniture, and spare parts. "
        "Your goal is to engage warmly with customers, give them expert advice on playground products, answer their queries with enthusiasm, and help them find the right equipment. "
        "CRITICAL INSTRUCTION: For larger queries with more gravity, complex installations, bulk orders, complaints, safety concerns, or urgent matters, you MUST prompt and advise the user to call our direct hotline at: 9924343003. "
        "Keep your tone upbeat, helpful, and concise. Format your advice clearly using markdown if appropriate."
    )

    messages = [{"role": "system", "content": system_prompt}]
    
    for h in history[-6:]:
        if isinstance(h, dict) and "role" in h and "content" in h:
            if h["role"] in ("user", "assistant"):
                messages.append({"role": h["role"], "content": str(h["content"])})
                
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            res_json = resp.json()
            bot_reply = res_json["choices"][0]["message"]["content"]
            return JsonResponse({"reply": bot_reply})
        else:
            payload["model"] = "llama-3.1-8b-instant"
            resp2 = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if resp2.status_code == 200:
                res_json = resp2.json()
                bot_reply = res_json["choices"][0]["message"]["content"]
                return JsonResponse({"reply": bot_reply})
            return JsonResponse({"reply": "Namaste! I'm Mohanlal. I'm having a little trouble connecting right now, but for any urgent queries or larger requirements, please feel free to call us directly at 9924343003!"}, status=200)
    except Exception:
        return JsonResponse({"reply": "Namaste! I'm Mohanlal. I encountered a momentary connection glitch. For any important queries or immediate advice, please call us at 9924343003!"}, status=200)

