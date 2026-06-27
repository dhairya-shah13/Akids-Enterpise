import os
import json
import uuid
import requests
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Product

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
        # We will use email as the username for regular authentication
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'cart')
            return redirect(next_url)
        else:
            error = "Invalid email or password."
            
    return render(request, 'products/login.html', {'error': error})

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
            return redirect('cart')
        else:
            error = "Please fill in all fields."
            
    return render(request, 'products/signup.html', {'error': error})

def logout_view(request):
    request.session.flush() # Flush admin session
    logout(request) # Log out regular user
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
    
    sales_data = {
        'total_revenue': '₹28,45,000',
        'total_orders': 142,
        'active_quotes': 38,
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
        'sales': sales_data,
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
    featured_products = Product.objects.all().order_by('-created_at')[:6]
    return render(request, 'products/home.html', {'featured_products': featured_products})

def category_listing(request, cat_code, template_name):
    products = Product.objects.filter(category=cat_code).order_by('-created_at')
    return render(request, template_name, {'products': products})

def indoors_view(request):
    return category_listing(request, 'INDOORS', 'products/listing.html')

def outdoors_view(request):
    return category_listing(request, 'OUTDOORS', 'products/outdoors.html')

def parts_view(request):
    return category_listing(request, 'PARTS', 'products/parts.html')

def rfsports_view(request):
    return category_listing(request, 'RFSPORTS', 'products/rfsports.html')

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)
        
    related_products = Product.objects.filter(category=product.category).exclude(pk=product.pk).order_by('-created_at')[:3]
    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related_products
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
        "We specialize in premium children's playground equipment, indoor & outdoor toys, RF sports gear, educational furniture, and spare parts. "
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

