import os
import json
import requests
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from .models import Product, Inquiry, Order, OrderItem, STATUS_TRANSITIONS, InquiryLineItem, UserProfile
from .search import search_products
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from .pdf_generator import generate_invoice_pdf



COMPANY_PAGES = {
    'about': {
        'title': 'About A kids',
        'eyebrow': 'Quality play environments',
        'intro': 'A kids India creates purposeful spaces where children can learn, move, imagine, and grow with confidence.',
        'sections': [
            ('Built for everyday learning and play', 'Our range brings together kindergarten furniture, indoor learning essentials, outdoor playground equipment, and MR Sports products for schools, daycare centres, and homes.'),
            ('Designed around growing minds', 'We focus on colourful, practical products that support active play, collaborative learning, and independent exploration. Our team can help you select a range that suits your space, age group, and requirements.'),
            ('From enquiry to environment', 'Whether you are furnishing a classroom or planning a larger play area, we make it simple to explore products, request a quote, and get guidance for your project.'),
        ],
    },
    'safety': {
        'title': 'Safety Standards',
        'eyebrow': 'Safety in every play space',
        'intro': 'Children deserve environments that invite play while giving adults confidence. Safety is considered throughout our product selection and project conversations.',
        'sections': [
            ('Thoughtful product selection', 'We prioritise child-friendly designs, practical materials, and finishes suited to regular use in learning and play environments.'),
            ('The right fit for the space', 'A safe play area depends on the product, the available space, age group, placement, and supervision. Share your requirements with us before ordering so we can help you make suitable choices.'),
            ('Care and supervision', 'Please follow product-specific assembly, use, and maintenance guidance. Inspect equipment regularly, keep play areas clear, and ensure children use products with appropriate adult supervision.'),
        ],
    },
    'testimonials': {
        'title': 'What our customers value',
        'eyebrow': 'A trusted partner for play',
        'intro': 'Schools, daycare centres, and families come to A kids for practical products and helpful guidance—not just a catalogue.',
        'sections': [
            ('Spaces that work harder', 'Customers look for furniture and play equipment that helps them create organised, welcoming settings for learning, movement, and imagination.'),
            ('Support for bigger ideas', 'For new classrooms, activity zones, and playground projects, our team helps customers narrow down options and build a solution around their needs.'),
            ('A conversation starts with your plan', 'Tell us about your space, age group, and priorities. We will help you explore the right products and prepare a quote for your requirements.'),
        ],
    },
    'contact': {
        'title': 'Contact A kids',
        'eyebrow': 'Let’s build a better play space',
        'intro': 'Talk to us about products, project requirements, availability, or a quote for your school, daycare centre, home, or sports space.',
        'sections': [
            ('Call us', 'For larger requirements, installation discussions, safety concerns, or urgent assistance, call our team on +91 9924343003.'),
            ('Email us', 'Send product and quote enquiries to hello@littlefingersindia.com. Including the product name, quantity, and your location helps us respond more effectively.'),
            ('Request a quote online', 'You can also use the enquiry option on a product page to share your requirements directly with our team.'),
        ],
    },
    'privacy': {
        'title': 'Privacy Policy',
        'eyebrow': 'Your information, handled with care',
        'intro': 'This policy explains how A kids India uses information collected through this website and product enquiries.',
        'sections': [
            ('Information we collect', 'We may collect the details you provide when you create an account, submit an enquiry, use the cart, contact us, or communicate with our support team. This may include your name, contact details, product interest, quantity, and message.'),
            ('How we use it', 'We use this information to respond to enquiries, prepare quotes, provide support, manage accounts and carts, improve our website, and meet legal or operational requirements. We do not sell your personal information.'),
            ('Sharing and retention', 'We share information only with service providers or authorities where needed to operate the website, deliver requested services, or comply with law. We keep information only for as long as reasonably necessary for these purposes.'),
            ('Your choices', 'To ask about or update the personal information you have shared with us, contact hello@littlefingersindia.com. Please do not send sensitive personal information through product enquiry forms.'),
        ],
    },
    'terms': {
        'title': 'Terms of Service',
        'eyebrow': 'Using the A kids website',
        'intro': 'These terms apply when you browse the A kids India website, create an account, add products to a cart, or submit an enquiry.',
        'sections': [
            ('Product information and enquiries', 'Product images, descriptions, availability, and prices are provided for general information and may change. A cart or enquiry is a request for information or a quote; it does not create an order or guarantee availability.'),
            ('Quotes and orders', 'Final product selection, pricing, delivery, installation, and payment terms are confirmed directly with our team before an order is accepted. Please review your quote carefully and share accurate contact and project details.'),
            ('Safe and appropriate use', 'Products must be assembled, used, maintained, and supervised in line with the applicable product guidance. Buyers are responsible for confirming that a product is appropriate for their space, intended users, and local requirements.'),
            ('Website use', 'Please use this website lawfully and do not interfere with its operation, submit misleading information, or attempt unauthorised access. For questions about these terms, contact hello@littlefingersindia.com.'),
        ],
    },
}


def company_page(request, page):
    return render(request, 'products/company_page.html', COMPANY_PAGES[page])

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

def login_view(request):
    if request.session.get('is_admin'):
        return redirect('admin_dashboard')
    if request.user.is_authenticated:
        return redirect('cart')
        
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        # 1. Check admin credentials first
        env_email, env_pass = get_env_credentials()
        if email == env_email and password == env_pass:
            request.session['is_admin'] = True
            return redirect('admin_dashboard')
            
        # 2. Check regular user credentials
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('cart')
            if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                next_url = reverse('cart')
            return redirect(next_url)
        else:
            error = "Invalid email or password."
            
    return render(request, 'products/login.html', {'error': error, 'next': request.GET.get('next', '')})


def signup_view(request):
    if request.session.get('is_admin'):
        return redirect('admin_dashboard')
    if request.user.is_authenticated:
        return redirect('cart')
        
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
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('cart')
            if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                next_url = reverse('cart')
            return redirect(next_url)
        else:
            error = "Please fill in all fields."
            
    return render(request, 'products/signup.html', {'error': error, 'next': request.GET.get('next', '')})

def logout_view(request):
    request.session.flush()
    logout(request)
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
                'total_price': total_price,
                'is_available': product.stock > 0,
            })
        except Product.DoesNotExist:
            continue
    return cart_items, subtotal

def cart_view(request):
    cart_items, subtotal = get_cart_data(request)
    has_unavailable_items = any(not item['is_available'] for item in cart_items)
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'has_unavailable_items': has_unavailable_items,
    })

def add_to_cart(request, pk):
    if request.method == 'POST':
        try:
            product = Product.objects.get(pk=pk)
            if product.stock <= 0:
                return redirect(f"{reverse('product_detail', args=[pk])}?toast=out-of-stock")
            
            quantity = int(request.POST.get('quantity', 1))
            cart = request.session.get('cart', {})
            cart[str(pk)] = cart.get(str(pk), 0) + quantity
            
            if cart[str(pk)] > product.stock:
                cart[str(pk)] = product.stock
                
            request.session['cart'] = cart
            request.session.modified = True
        except (Product.DoesNotExist, ValueError):
            pass

    next_param = request.GET.get('next', '')
    if next_param == 'checkout':
        if not request.user.is_authenticated:
            login_url = reverse('admin_login')
            return redirect(f"{login_url}?next={reverse('cart')}&toast=login-required")
        return redirect(reverse('checkout'))
    elif next_param == 'stay':
        referer = request.META.get('HTTP_REFERER', '/')
        # Append toast param to referer
        separator = '&' if '?' in referer else '?'
        return redirect(f'{referer}{separator}toast=added')
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
            elif product.stock > 0:
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
    
    # Handle sorting and filtering for inquiries
    status_filter = request.GET.get('status', '').strip().upper()
    inquiries = Inquiry.objects.all()
    if status_filter in ['NEW', 'CONTACTED', 'CLOSED']:
        inquiries = inquiries.filter(status=status_filter)
    inquiries = inquiries.order_by('-created_at')
    
    orders_count = Order.objects.count()
    
    sales_data = {
        'total_revenue': '₹28,45,000',
        'total_orders': 142,
        'active_quotes': Inquiry.objects.filter(status='NEW').count(),
        'best_seller': 'The Everest Slide',
        'monthly_sales': [
            {'month': 'Jan', 'amount': '₹1,80,000', 'height': '45%'},
            {'month': 'Feb', 'amount': '₹2,20,000', 'height': '55%'},
            {'month': 'Mar', 'amount': '₹3,10,000', 'height': '78%'},
            {'month': 'Apr', 'amount': '₹2,90,000', 'height': '72%'},
            {'month': 'May', 'amount': '₹3,80,000', 'height': '95%'},
            {'month': 'Jun', 'amount': '₹4,10,000', 'height': '100%'},
        ]
    }
    
    return render(request, 'products/admin_dashboard.html', {
        'products': products,
        'inquiries': inquiries,
        'current_status_filter': status_filter,
        'sales': sales_data,
        'orders_count': orders_count,
        'admin_email': get_env_credentials()[0]
    })

def add_product(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'INDOORS').strip()
        price = request.POST.get('price', '0').replace(',', '').replace('₹', '').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
            
        if name and price:
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
        # Show top 8 products on the splash page
        products = Product.objects.filter(category=cat_code).order_by('-created_at')[:8]
    return render(request, template_name, {
        'products': products,
        'category_code': cat_code
    })

def indoors_view(request):
    return category_listing(request, 'INDOORS', 'products/listing.html')

def outdoors_view(request):
    return category_listing(request, 'OUTDOORS', 'products/outdoors.html')


def mrsports_view(request):
    return category_listing(request, 'MRSPORTS', 'products/mrsports.html')

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)

    # Determine which listing page to go back to based on category
    from django.urls import reverse
    category_lower = (product.category or '').lower()
    if 'outdoor' in category_lower:
        back_url = reverse('outdoors')
        back_label = 'Outdoors'
    elif 'mr' in category_lower or 'sports' in category_lower:
        back_url = reverse('mrsports')
        back_label = 'MR Sports'
    else:
        back_url = reverse('indoors')
        back_label = 'Indoors'

    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk).exclude(stock__lte=0).order_by('-created_at')[:3]
    return render(request, 'products/product_detail.html', {
        'product': product,
        'selected_variant': product,
        'variant_pk': product.pk,
        'related_products': related_products,
        'back_url': back_url,
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



def update_inquiry_status(request, pk):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    if request.method == 'POST':
        inquiry = get_object_or_404(Inquiry, pk=pk)
        new_status = request.POST.get('status', '').strip().upper()
        if new_status in ['NEW', 'CONTACTED', 'CLOSED']:
            inquiry.status = new_status
            inquiry.save()
            
    return redirect('admin_dashboard')


def delete_inquiry(request, pk):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
        
    if request.method == 'POST':
        Inquiry.objects.filter(pk=pk).delete()
        
    return redirect('admin_dashboard')


# --- STOREFRONT ORDER VIEWS ---

def checkout_view(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('admin_login')}?next={reverse('cart')}&toast=login-required")

    cart_items, subtotal = get_cart_data(request)
    if not cart_items:
        return redirect('cart')

    if any(not item['is_available'] for item in cart_items):
        return redirect(f"{reverse('cart')}?toast=unavailable")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip() or request.user.username
        shipping_address = request.POST.get('shipping_address', '').strip()
        if not shipping_address:
            return render(request, 'products/checkout.html', {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'total': subtotal,
                'profile': profile,
                'error': 'Please enter your delivery address.',
            })

        # Save to profile if missing
        if not profile.shipping_address and shipping_address:
            profile.shipping_address = shipping_address
            profile.save()

        # TODO: Replace this test-mode order creation with Razorpay payment confirmation.
        # This intentionally creates a real order so the admin tracking flow can be tested end to end.
        try:
            with transaction.atomic():
                locked_items = []
                for item in cart_items:
                    product = Product.objects.select_for_update().get(pk=item['product'].pk)
                    if product.stock < item['quantity']:
                        raise ValueError(f"{product.name} no longer has enough stock.")
                    locked_items.append((product, item['quantity']))

                order = Order.objects.create(
                    user=request.user,
                    customer_name=customer_name,
                    shipping_address=shipping_address,
                    order_status='PLACED',
                )
                for product, quantity in locked_items:
                    unit_price = product.discount_price or product.price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                    product.stock -= quantity
                    product.save(update_fields=['stock'])
        except ValueError as error:
            return redirect(f"{reverse('cart')}?toast=unavailable")

        request.session['cart'] = {}
        request.session.modified = True
        return redirect('order_success', order_id=order.pk)

    return render(request, 'products/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'profile': profile,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'products/order_success.html', {'order': order})


# --- ADMIN API ENDPOINTS (Protected) ---

def api_admin_orders(request):
    if not request.session.get('is_admin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    orders_qs = Order.objects.select_related('user').prefetch_related('items', 'items__product').all()
    
    # Filtering
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter:
        orders_qs = orders_qs.filter(order_status=status_filter)
        
    date_start = request.GET.get('date_start', '').strip()
    if date_start:
        orders_qs = orders_qs.filter(created_at__date__gte=date_start)
        
    date_end = request.GET.get('date_end', '').strip()
    if date_end:
        orders_qs = orders_qs.filter(created_at__date__lte=date_end)
        
    customer_name = request.GET.get('customer_name', '').strip()
    if customer_name:
        orders_qs = orders_qs.filter(customer_name__icontains=customer_name)
        
    order_no = request.GET.get('order_no', '').strip()
    if order_no:
        orders_qs = orders_qs.filter(order_no__icontains=order_no)
        
    orders_qs = orders_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    orders_list = []
    for order in page_obj:
        items_summary = ", ".join([f"{item.product_name} x {item.quantity}" for item in order.items.all()])
        orders_list.append({
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'shipping_address': order.shipping_address,
            'order_status': order.order_status,
            'order_status_display': order.get_order_status_display(),
            'total_amount': float(order.total_amount),
            'created_at_str': order.created_at.strftime('%d %b %Y, %I:%M %p'),
            'items_summary': items_summary
        })
        
    return JsonResponse({
        'orders': orders_list,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'total_count': paginator.count
    })


def api_admin_order_detail(request, order_id):
    if not request.session.get('is_admin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    order = get_object_or_404(Order.objects.prefetch_related('items', 'items__product'), pk=order_id)
    
    items_list = []
    for item in order.items.all():
        display_image = item.product.display_image if item.product else "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"
        items_list.append({
            'product_name': item.product_name,
            'sku': item.product.sku if item.product else '',
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),
            'subtotal': float(item.subtotal),
            'display_image': display_image
        })
        
    return JsonResponse({
        'id': order.id,
        'order_no': order.order_no,
        'customer_name': order.customer_name,
        'shipping_address': order.shipping_address,
        'order_status': order.order_status,
        'order_status_display': order.get_order_status_display(),
        'total_amount': float(order.total_amount),
        'created_at_str': order.created_at.strftime('%d %b %Y, %I:%M %p'),
        'items': items_list
    })


@csrf_exempt
@require_http_methods(["PATCH"])
def api_admin_order_status_update(request, order_id):
    if not request.session.get('is_admin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    order = get_object_or_404(Order, pk=order_id)
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '').strip().upper()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    current_status = order.order_status
    allowed_next_states = STATUS_TRANSITIONS.get(current_status, [])
    
    if new_status not in allowed_next_states:
        return JsonResponse({
            'error': f"Status transition from '{current_status}' to '{new_status}' is not allowed."
        }, status=400)
        
    order.order_status = new_status
    order.save()
    
    return JsonResponse({
        'success': True,
        'order_status': order.order_status,
        'order_status_display': order.get_order_status_display()
    })


def api_admin_order_invoice(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=order_id)
    if not (request.session.get('is_admin') or (request.user.is_authenticated and order.user == request.user)):
        return HttpResponse('Unauthorized', status=403)
    try:
        is_admin = bool(request.session.get('is_admin'))
        pdf_content = generate_invoice_pdf(order, is_admin=is_admin)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{order.order_no}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Invoice generation failed: {str(e)}", status=500)


# ==========================================
# Catalog "View All Products" & Inquiries
# ==========================================

CATALOGUE_CONFIG = {
    'indoor': '/static/catalogues/indoor-catalogue-march-2026.pdf',
    'outdoor': '/static/catalogues/outdoor-catalogue-march-2026.pdf',
    'mr_sports': None
}

def view_all_products(request, module_type):
    module_type = module_type.lower()
    if module_type not in ['indoor', 'outdoor']:
        return render(request, '404.html', status=404)
        
    pdf_url = CATALOGUE_CONFIG.get(module_type)
    
    category_map = {
        'indoor': 'INDOORS',
        'outdoor': 'OUTDOORS'
    }
    db_category = category_map[module_type]
    
    products = Product.objects.filter(category=db_category).order_by('sku')
    product_codes = []
    for p in products:
        if p.sku:
            product_codes.append({
                'code': p.sku,
                'name': p.name
            })
            
    module_labels = {
        'indoor': 'Indoor',
        'outdoor': 'Outdoor'
    }
    
    # Pre-fill inquiry form for logged-in users
    prefill_name = ''
    prefill_email = ''
    prefill_phone = ''
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        prefill_name = request.user.username
        prefill_email = request.user.email
        prefill_phone = profile.phone_number

    return render(request, 'products/view_all.html', {
        'module_type': module_type,
        'module_label': module_labels[module_type],
        'pdf_url': pdf_url,
        'product_codes': product_codes,
        'product_codes_json': json.dumps(product_codes),
        'prefill_name': prefill_name,
        'prefill_email': prefill_email,
        'prefill_phone': prefill_phone,
    })


@csrf_exempt
def submit_catalog_inquiry(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST requests allowed.'}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON payload.'}, status=400)
        
    name = data.get('name', '').strip()
    phone_number = data.get('phone_number', '').strip()
    email = data.get('email', '').strip()
    module = data.get('module', '').strip().lower()
    line_items_data = data.get('line_items', [])
    
    if not name or not phone_number or not email or not module:
        return JsonResponse({'success': False, 'error': 'Name, Phone, Email, and Module are required.'}, status=400)
        
    if module not in ['indoor', 'outdoor', 'mr_sports']:
        return JsonResponse({'success': False, 'error': 'Invalid module type.'}, status=400)
        
    if not line_items_data or len(line_items_data) == 0:
        return JsonResponse({'success': False, 'error': 'At least one product line item is required.'}, status=400)
        
    try:
        with transaction.atomic():
            inquiry = Inquiry.objects.create(
                name=name,
                contact_number=phone_number,
                email=email,
                module=module,
                status='NEW'
            )
            for item in line_items_data:
                product_code = item.get('product_code', '').strip()
                try:
                    qty = int(item.get('quantity', 1))
                except (ValueError, TypeError):
                    qty = 1
                if not product_code:
                    raise Exception('Product code cannot be empty.')
                if qty < 1:
                    raise Exception('Quantity must be at least 1.')
                    
                InquiryLineItem.objects.create(
                    inquiry=inquiry,
                    product_code=product_code,
                    quantity=qty
                )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
    return JsonResponse({'success': True, 'inquiry_id': inquiry.pk})


def api_admin_inquiries(request):
    if not request.session.get('is_admin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    module_filter = request.GET.get('module', '').strip().lower()
    date_start = request.GET.get('date_start', '').strip()
    date_end = request.GET.get('date_end', '').strip()
    
    inquiries = Inquiry.objects.all().prefetch_related('line_items')
    
    if module_filter in ['indoor', 'outdoor', 'mr_sports']:
        inquiries = inquiries.filter(module=module_filter)
        
    if date_start:
        inquiries = inquiries.filter(created_at__gte=date_start)
    if date_end:
        inquiries = inquiries.filter(created_at__lte=date_end)
        
    inquiries = inquiries.order_by('-created_at')
    
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
        
    paginator = Paginator(inquiries, 10)
    current_page = paginator.get_page(page)
    
    data = {
        'inquiries': [],
        'has_next': current_page.has_next(),
        'has_previous': current_page.has_previous(),
        'current_page': current_page.number,
        'num_pages': paginator.num_pages,
        'total_count': paginator.count
    }
    
    for inq in current_page:
        items_summary = ", ".join([f"{item.product_code} ({item.quantity})" for item in inq.line_items.all()])
        data['inquiries'].append({
            'id': inq.id,
            'module': inq.module,
            'module_display': inq.get_module_display() if inq.module else 'Single Product',
            'customer_name': inq.name,
            'phone_number': inq.contact_number,
            'email': inq.email or 'N/A',
            'items_summary': items_summary or 'No items',
            'created_at_str': inq.created_at.strftime('%Y-%m-%d %H:%M'),
            'status': inq.status,
            'status_display': inq.get_status_display()
        })
        
    return JsonResponse(data)


def api_admin_inquiry_detail(request, pk):
    if not request.session.get('is_admin'):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    inq = get_object_or_404(Inquiry.objects.prefetch_related('line_items'), pk=pk)
    
    items = []
    for item in inq.line_items.all():
        items.append({
            'product_code': item.product_code,
            'quantity': item.quantity
        })
        
    data = {
        'id': inq.id,
        'module': inq.module,
        'module_display': inq.get_module_display() if inq.module else 'Single Product',
        'customer_name': inq.name,
        'phone_number': inq.contact_number,
        'email': inq.email or 'N/A',
        'status': inq.status,
        'status_display': inq.get_status_display(),
        'created_at_str': inq.created_at.strftime('%Y-%m-%d %H:%M'),
        'items': items
    }
    return JsonResponse(data)


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('admin_login')}?next={reverse('profile')}")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        profile.phone_number = request.POST.get('phone_number', '').strip()
        profile.shipping_address = request.POST.get('shipping_address', '').strip()
        profile.save()
        return redirect(f"{reverse('profile')}?toast=saved")

    orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
    return render(request, 'products/profile.html', {
        'profile': profile,
        'orders': orders,
    })
