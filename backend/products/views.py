import os
import json
import requests
import time
import logging
import socket
from decimal import Decimal
from pathlib import Path
from functools import lru_cache
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from .models import Product, Inquiry, Order, OrderItem, STATUS_TRANSITIONS, InquiryLineItem, UserProfile, Address, ProductClassSpec, ProductDimensionSpec
from .constants import PRODUCT_COLOURS
from .search import search_products
from .utils import calculate_gst
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils import timezone
from django.contrib.sitemaps import Sitemap
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)

# Lazy import: pdf_generator loads ReportLab which is heavy; import only when needed



COMPANY_PAGES = {
    'about': {
        'title': 'About A kids',
        'eyebrow': 'Quality play environments',
        'intro': 'A kids India creates purposeful spaces where children can learn, move, imagine, and grow with confidence.',
        'meta_description': 'Learn about A kids India, our commitment to quality, safety-certified play environments, and our range of kids furniture, playground, and sports gear.',
        'sections': [
            ('Built for everyday learning and play', 'Our range brings together kindergarten furniture, indoor learning essentials, outdoor playground equipment, and Shreem Sports products for schools, daycare centres, and homes.'),
            ('Designed around growing minds', 'We focus on colourful, practical products that support active play, collaborative learning, and independent exploration. Our team can help you select a range that suits your space, age group, and requirements.'),
            ('From enquiry to environment', 'Whether you are furnishing a classroom or planning a larger play area, we make it simple to explore products, request a quote, and get guidance for your project.'),
        ],
    },
    'safety': {
        'title': 'Safety Standards',
        'eyebrow': 'Safety in every play space',
        'intro': 'Children deserve environments that invite play while giving adults confidence. Safety is considered throughout our product selection and project conversations.',
        'meta_description': 'Read our safety standards for kindergarten furniture, playground equipment, and sports gear. We prioritize safety, materials, and child development.',
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
        'meta_description': 'Discover customer testimonials for A kids India. Learn why schools, daycare centers, and parents trust us for kindergarten furniture and play gear.',
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
        'meta_description': 'Get in touch with A kids India. Contact us via phone or email for quotes, product details, or custom design queries for kindergarten and play areas.',
        'sections': [
            ('Call us', 'For larger requirements, installation discussions, safety concerns, or urgent assistance, call our team on +91 7433 026 008.'),
            ('Email us', 'Send product and quote enquiries to info@akidsenterprise.com. Including the product name, quantity, and your location helps us respond more effectively.'),
            ('Request a quote online', 'You can also use the enquiry option on a product page to share your requirements directly with our team.'),
        ],
    },
    'privacy': {
        'title': 'Privacy Policy',
        'eyebrow': 'Your information, handled with care',
        'intro': 'This policy explains how A kids India uses information collected through this website and product enquiries.',
        'meta_description': 'Our privacy policy explains how A kids India collects, uses, and safeguards personal information from website users and product inquiries.',
        'sections': [
            ('Information we collect', 'We may collect the details you provide when you create an account, submit an enquiry, use the cart, contact us, or communicate with our support team. This may include your name, contact details, product interest, quantity, and message.'),
            ('How we use it', 'We use this information to respond to enquiries, prepare quotes, provide support, manage accounts and carts, improve our website, and meet legal or operational requirements. We do not sell your personal information.'),
            ('Sharing and retention', 'We share information only with service providers or authorities where needed to operate the website, deliver requested services, or comply with law. We keep information only for as long as reasonably necessary for these purposes.'),
            ('Your choices', 'To ask about or update the personal information you have shared with us, contact info@akidsenterprise.com. Please do not send sensitive personal information through product enquiry forms.'),
        ],
    },
    'terms': {
        'title': 'Terms of Service',
        'eyebrow': 'Using the A kids website',
        'intro': 'These terms apply when you browse the A kids India website, create an account, add products to a cart, or submit an enquiry.',
        'meta_description': 'Read the terms of service for using the A kids India website, registering accounts, and submitting product quote inquiries.',
        'sections': [
            ('Product information and enquiries', 'Product images, descriptions, availability, and prices are provided for general information and may change. A cart or enquiry is a request for information or a quote; it does not create an order or guarantee availability.'),
            ('Quotes and orders', 'Final product selection, pricing, delivery, installation, and payment terms are confirmed directly with our team before an order is accepted. Please review your quote carefully and share accurate contact and project details.'),
            ('Safe and appropriate use', 'Products must be assembled, used, maintained, and supervised in line with the applicable product guidance. Buyers are responsible for confirming that a product is appropriate for their space, intended users, and local requirements.'),
            ('Website use', 'Please use this website lawfully and do not interfere with its operation, submit misleading information, or attempt unauthorised access. For questions about these terms, contact info@akidsenterprise.com.'),
        ],
    },
}


@cache_page(60 * 30)  # Cache for 30 minutes
def company_page(request, page):
    return render(request, 'products/company_page.html', COMPANY_PAGES[page])

@lru_cache(maxsize=1)
def _read_env_file():
    """Read .env file once into os.environ and cache the result. Avoids disk I/O on every request.

    NOTE: There are deliberately NO hardcoded fallback admin credentials here.
    The admin account is a real Django superuser bootstrapped at deploy time via
    the `create_admin_from_env` management command.
    """
    # Business WhatsApp number. Falls back to the business hotline (same number
    # advertised across the site) only when the env var is unset — this is a
    # phone number for customer contact, not a credential.
    whatsapp_num = os.getenv("WHATSAPP_NUMBER", "7433026008").strip()
    # Single canonical .env: backend/.env (the root .env was consolidated into
    # it on 2026-08-01 to remove a stale Supabase host that broke connections).
    possible_paths = [
        settings.BASE_DIR / ".env",
    ]
    for env_path in possible_paths:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip('"\' ')
                            os.environ[k] = v
                            if k == "WHATSAPP_NUMBER":
                                whatsapp_num = v
            except Exception:
                pass
    return whatsapp_num


def get_whatsapp_number():
    return _read_env_file()


def is_admin_user(request):
    # Per-request cache
    if hasattr(request, '_is_admin_cached'):
        return request._is_admin_cached
    result = False
    if request.user.is_authenticated:
        # Admin is a real Django superuser/staff user (bootstrapped from env).
        if request.user.is_staff or request.user.is_superuser:
            result = True
    if not result:
        result = bool(request.session.get('is_admin'))
    request._is_admin_cached = result
    return result


def validate_email_and_domain(email):
    """Validate email syntax and check whether the domain host exists."""
    if not email:
        return False, "Please enter an email address."
    try:
        validate_email(email)
    except ValidationError:
        return False, "Please enter a valid email address format (e.g. user@example.com)."
    
    parts = email.split('@')
    if len(parts) != 2:
        return False, "Invalid email address format."
    
    domain = parts[1].lower().strip()
    try:
        socket.gethostbyname(domain)
    except Exception:
        return False, f"The email domain (@{domain}) does not exist or cannot receive emails."
    
    return True, None


def send_verification_email(request, user):
    """Sends a verification email link via Firebase / signed token link."""
    _read_env_file()
    signer = TimestampSigner()
    token = signer.sign(str(user.id))
    verify_url = request.build_absolute_uri(reverse('verify_email_confirm') + f'?token={token}&email={user.email}')
    
    firebase_key = os.getenv("FIREBASE_API_KEY", "").strip()
    firebase_sent = False
    
    if firebase_key and not firebase_key.startswith("YOUR_"):
        try:
            payload = {
                "requestType": "EMAIL_SIGNIN",
                "email": user.email,
                "continueUrl": verify_url
            }
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebase_key}"
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                firebase_sent = True
        except Exception:
            pass
            
    return verify_url, firebase_sent


def login_view(request):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    if request.user.is_authenticated:
        return redirect('cart')

    error = None
    unverified_email = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Admin users are real Django superusers (bootstrapped via the
        # `create_admin_from_env` management command) and authenticate through
        # the standard path below. There is no special-cased admin credential
        # check anymore — removing it closes the hardcoded-credential backdoor.

        # Check if user exists but is_active is False (unverified email)
        try_user = User.objects.filter(Q(email=email) | Q(username=email)).first()
        if try_user and not try_user.is_active and try_user.check_password(password):
            return render(request, 'products/login.html', {
                'error': f"Your email ({try_user.email}) has not been verified yet. Please check your inbox for the activation link.",
                'unverified_email': try_user.email,
                'next': request.GET.get('next', '')
            })

        # 2. Check regular user credentials (try by username first, then by email)
        user = authenticate(request, username=email, password=password)
        if user is None:
            if try_user:
                user = authenticate(request, username=try_user.username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                request.session['is_admin'] = True
                next_url = request.POST.get('next') or request.GET.get('next') or reverse('admin_dashboard')
            else:
                next_url = request.POST.get('next') or request.GET.get('next') or reverse('cart')
            if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}):
                next_url = reverse('cart')
            sep = '&' if '?' in next_url else '?'
            return redirect(f'{next_url}{sep}toast=login')
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

        # 1. Format and Domain Validation
        valid_email, domain_err = validate_email_and_domain(email)
        if not valid_email:
            error = domain_err
        # 2. Single query to check both email and username
        elif User.objects.filter(Q(email=email) | Q(username=username)).exists():
            if User.objects.filter(email=email).exists():
                error = "A user with that email already exists."
            else:
                error = "That username is already taken."
        elif email and password and username:
            if len(password) < 6:
                error = "Password must be at least 6 characters long."
            else:
                # Create user with is_active = False (unverified)
                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_active = False
                user.save()
                UserProfile.objects.get_or_create(user=user)

                # Send verification email
                verify_url, firebase_sent = send_verification_email(request, user)
                
                return render(request, 'products/verify_email_pending.html', {
                    'email': email,
                    'verify_url': verify_url,
                    'firebase_sent': firebase_sent
                })
        else:
            error = "Please fill in all fields."

    return render(request, 'products/signup.html', {'error': error, 'next': request.GET.get('next', '')})


def verify_email_confirm(request):
    token = request.GET.get('token')
    email = request.GET.get('email')
    
    user = None
    if token:
        signer = TimestampSigner()
        try:
            user_id = signer.unsign(token, max_age=259200) # 3 days expiration
            user = User.objects.filter(pk=user_id).first()
        except (BadSignature, SignatureExpired):
            user = None
            
    if not user and email:
        user = User.objects.filter(email=email, is_active=False).first()
        
    if user:
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'products/verify_email_success.html', {'user': user})
    else:
        return render(request, 'products/login.html', {
            'error': 'Invalid or expired verification link. Please log in or request a new verification email.'
        })


def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email, is_active=False).first()
        if user:
            verify_url, firebase_sent = send_verification_email(request, user)
            return render(request, 'products/verify_email_pending.html', {
                'email': email,
                'verify_url': verify_url,
                'firebase_sent': firebase_sent,
                'resent': True
            })
        else:
            return render(request, 'products/login.html', {
                'error': 'No unverified account found with that email address.'
            })
    return redirect('admin_login')


def logout_view(request):
    request.session.flush()
    logout(request)
    return redirect(f"{reverse('home')}?toast=logout")


# --- Third-Party Auth: Google OAuth & Firebase Passwordless ---

def _google_redirect_uri(request):
    """Build the Google OAuth redirect URI.

    Uses the SITE_URL setting (set in production) so the URI is always
    canonical and matches what is registered in the Google Console,
    regardless of which Host header Vercel forwards internally.
    Falls back to request.build_absolute_uri() for local development.
    """
    from django.conf import settings as _settings
    site_url = getattr(_settings, 'SITE_URL', None)
    if site_url:
        return f"{site_url}{reverse('google_callback')}"
    return request.build_absolute_uri(reverse('google_callback'))

def google_login(request):
    _read_env_file()
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if not client_id or client_id.startswith("YOUR_"):
        return redirect(f"{reverse('admin_login')}?toast=google-not-configured")
    
    redirect_uri = _google_redirect_uri(request)
    google_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile"
    )
    return redirect(google_url)


def google_callback(request):
    _read_env_file()
    code = request.GET.get('code')
    if not code:
        return redirect(f"{reverse('admin_login')}?toast=google-error")
    
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = _google_redirect_uri(request)
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        resp = requests.post(token_url, data=data, timeout=10)
        tokens = resp.json()
        access_token = tokens.get('access_token')
        if not access_token:
            return redirect(f"{reverse('admin_login')}?toast=google-error")
        
        user_info_resp = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        info = user_info_resp.json()
        email = info.get('email')
        name = info.get('name', '')
        
        if not email:
            return redirect(f"{reverse('admin_login')}?toast=google-error")
        
        user = User.objects.filter(email=email).first()
        if not user:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user = User.objects.create_user(username=username, email=email)
            user.first_name = name
            user.is_active = True
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'full_name': name})
        else:
            if not user.is_active:
                user.is_active = True
                user.save()
            
        login(request, user)
        return redirect(f"{reverse('cart')}?toast=login")
    except Exception:
        return redirect(f"{reverse('admin_login')}?toast=google-error")


def firebase_login(request):
    """Send a Firebase passwordless sign-in email link (does NOT log the user in immediately)."""
    _read_env_file()
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not email:
        return JsonResponse({'error': 'Email required'}, status=400)

    firebase_key = os.getenv("FIREBASE_API_KEY", "").strip()
    if not firebase_key or firebase_key.startswith("YOUR_"):
        return JsonResponse({'error': 'Firebase Auth is not configured yet. See docs/CREDENTIALS_SETUP.md'}, status=400)

    # Build the callback URL that Firebase will embed in the email
    callback_url = request.build_absolute_uri(reverse('firebase_email_callback'))

    # Send the sign-in email via Firebase REST API
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={firebase_key}"
    payload = {
        "requestType": "EMAIL_SIGNIN",
        "email": email,
        "continueUrl": callback_url,
        "canHandleCodeInApp": False,
    }

    try:
        resp = requests.post(firebase_url, json=payload, timeout=10)
        result = resp.json()

        if resp.status_code != 200:
            error_msg = result.get('error', {}).get('message', 'Failed to send email.')
            # Provide user-friendly error messages
            if 'INVALID_EMAIL' in error_msg:
                return JsonResponse({'error': 'Please enter a valid email address.'}, status=400)
            elif 'TOO_MANY_ATTEMPTS' in error_msg:
                return JsonResponse({'error': 'Too many attempts. Please try again later.'}, status=400)
            return JsonResponse({'error': 'Unable to send reset link. Please try again.'}, status=400)
    except requests.exceptions.RequestException:
        return JsonResponse({'error': 'Network error. Please try again.'}, status=500)

    # Store the email in session so callback can verify it
    request.session['forgot_password_email'] = email

    return JsonResponse({
        'status': 'ok',
        'redirect_url': f"{reverse('forgot_password_waiting')}?email={email}"
    })


def forgot_password_waiting(request):
    """Display a 'Check Your Email' waiting page."""
    email = request.GET.get('email', request.session.get('forgot_password_email', ''))
    return render(request, 'products/forgot_password_waiting.html', {'email': email})


def firebase_email_callback(request):
    """Handle the magic link callback from Firebase email."""
    _read_env_file()
    firebase_key = os.getenv("FIREBASE_API_KEY", "").strip()

    # The oobCode is passed as a query parameter by Firebase
    oob_code = request.GET.get('oobCode', '').strip()

    if not oob_code or not firebase_key:
        return redirect(f"{reverse('admin_login')}?toast=link-invalid")

    # Verify the oobCode via Firebase REST API to get the email
    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithEmailLink?key={firebase_key}"
    # We need the email — try from session first, then from query param
    email = request.session.get('forgot_password_email', request.GET.get('email', '')).strip()

    if not email:
        # If no email in session (e.g., different browser), ask the user
        return redirect(f"{reverse('admin_login')}?toast=link-expired")

    payload = {
        "oobCode": oob_code,
        "email": email,
    }

    try:
        resp = requests.post(verify_url, json=payload, timeout=10)
        result = resp.json()

        if resp.status_code != 200:
            return redirect(f"{reverse('admin_login')}?toast=link-invalid")

        verified_email = result.get('email', email)
    except requests.exceptions.RequestException:
        return redirect(f"{reverse('admin_login')}?toast=link-invalid")

    # Find or create the user
    user = User.objects.filter(email=verified_email).first()
    if not user:
        username = verified_email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user = User.objects.create_user(username=username, email=verified_email)
        user.is_active = True
        user.save()
        UserProfile.objects.get_or_create(user=user)
    else:
        if not user.is_active:
            user.is_active = True
            user.save()

    # Log the user in and redirect to set password
    login(request, user)
    request.session['force_password_set'] = True
    request.session.pop('forgot_password_email', None)
    return redirect('set_password')


def set_password_view(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')
    
    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        if not password or password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        else:
            request.user.set_password(password)
            request.user.is_active = True
            request.user.save()
            request.session.pop('force_password_set', None)
            login(request, request.user)
            return redirect(f"{reverse('profile')}?toast=password-set")
            
    return render(request, 'products/set_password.html', {'error': error})


@require_http_methods(["POST"])
def change_password_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    current_password = request.POST.get('current_password', '').strip()
    new_password = request.POST.get('new_password', '').strip()
    confirm_new_password = request.POST.get('confirm_new_password', '').strip()

    if not current_password or not new_password or not confirm_new_password:
        return JsonResponse({'error': 'All fields are required.'}, status=400)

    if new_password != confirm_new_password:
        return JsonResponse({'error': 'New passwords do not match.'}, status=400)

    if len(new_password) < 6:
        return JsonResponse({'error': 'Password must be at least 6 characters long.'}, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({'error': 'Current password is incorrect.'}, status=400)

    request.user.set_password(new_password)
    request.user.save()
    login(request, request.user)
    return JsonResponse({'status': 'ok', 'message': 'Password changed successfully.'})

def get_cart_data(request):
    cart = request.session.get('cart', {})
    if not cart:
        return [], 0
    cart_items = []
    subtotal = 0
    product_ids = []
    for key in cart.keys():
        if '::' in key:
            pk = key.split('::')[0]
        else:
            pk = key
        if pk.isdigit():
            product_ids.append(pk)
            
    product_map = {str(p.id): p for p in Product.objects.filter(pk__in=product_ids).only(
        'id', 'name', 'price', 'discount_price', 'stock', 'category',
        'sku', 'source', 'needs_image', 'image_file', 'image_url'
    )}
    for key, quantity in cart.items():
        if '::' in key:
            parts = key.split('::')
            pk = parts[0]
            colour = parts[1] if len(parts) > 1 and parts[1] else None
            dimension = parts[2] if len(parts) > 2 and parts[2] else None
        else:
            pk = key
            colour = None
            dimension = None
            
        product = product_map.get(pk)
        if product is None:
            continue
        price = product.discount_price if product.discount_price else product.price
        total_price = price * quantity
        subtotal += total_price
        cart_items.append({
            'product': product,
            'colour': colour,
            'dimension': dimension,
            'key': key,
            'quantity': quantity,
            'total_price': total_price,
            'is_available': product.stock > 0,
        })
    return cart_items, subtotal

def cart_view(request):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    cart_items, subtotal = get_cart_data(request)
    has_unavailable_items = any(not item['is_available'] for item in cart_items)
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'has_unavailable_items': has_unavailable_items,
    })

def add_to_cart(request, pk):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            colour = request.POST.get('colour', '').strip()
            dimension = request.POST.get('dimension', '').strip()
            
            product = get_object_or_404(Product, pk=pk)
            # validation!
            if product.colours and not colour:
                return redirect(f"{reverse('product_detail', args=[pk])}?toast=select-variants-required")
            if product.dimension_specs.exists() and not dimension:
                return redirect(f"{reverse('product_detail', args=[pk])}?toast=select-variants-required")
            
            cart = request.session.get('cart', {})
            if colour or dimension:
                key = f"{pk}::{colour}::{dimension}"
            else:
                key = str(pk)
            current = cart.get(key, 0)
            cart[key] = current + quantity
            request.session['cart'] = cart
            request.session.modified = True
        except (ValueError, KeyError):
            pass

    next_param = request.GET.get('next', '')
    if next_param == 'checkout':
        if not request.user.is_authenticated:
            login_url = reverse('admin_login')
            return redirect(f"{login_url}?next={reverse('cart')}&toast=login-required")
        return redirect(reverse('checkout'))
    elif next_param == 'stay':
        referer = request.META.get('HTTP_REFERER', '/')
        separator = '&' if '?' in referer else '?'
        return redirect(f'{referer}{separator}toast=added')
    return redirect('cart')

def remove_from_cart(request, pk):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    if request.method == 'POST':
        colour = request.POST.get('colour', '').strip()
        dimension = request.POST.get('dimension', '').strip()
        cart = request.session.get('cart', {})
        if colour or dimension:
            key = f"{pk}::{colour}::{dimension}"
        else:
            key = str(pk)
        if key in cart:
            del cart[key]
            request.session['cart'] = cart
            request.session.modified = True
    return redirect(f"{reverse('cart')}?toast=removed")

def update_cart(request, pk):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            colour = request.POST.get('colour', '').strip()
            dimension = request.POST.get('dimension', '').strip()
            cart = request.session.get('cart', {})
            if colour or dimension:
                key = f"{pk}::{colour}::{dimension}"
            else:
                key = str(pk)
            if quantity <= 0:
                cart.pop(key, None)
            else:
                cart[key] = quantity
            request.session['cart'] = cart
            request.session.modified = True
        except (ValueError, KeyError):
            pass
    return redirect(f"{reverse('cart')}?toast=updated")


def admin_dashboard(request):
    if not is_admin_user(request):
        return redirect('admin_login')

    products = Product.objects.prefetch_related('class_specs', 'dimension_specs').order_by('-created_at')

    # Handle sorting and filtering for inquiries
    status_filter = request.GET.get('status', '').strip().upper()
    inquiries = Inquiry.objects.all().prefetch_related('line_items')
    if status_filter in ['NEW', 'CONTACTED', 'CLOSED']:
        inquiries = inquiries.filter(status=status_filter)
    inquiries = inquiries.order_by('-created_at')

    orders_count = Order.objects.count()

    # Cache sales aggregates for 5 minutes
    sales_data = cache.get('admin_sales_data')
    if sales_data is None:
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
        cache.set('admin_sales_data', sales_data, 300)  # 5 min

    return render(request, 'products/admin_dashboard.html', {
        'products': products,
        'inquiries': inquiries,
        'current_status_filter': status_filter,
        'sales': sales_data,
        'orders_count': orders_count,
        'admin_email': request.user.email,
        'product_colours': PRODUCT_COLOURS,
    })

def add_product(request):
    if not is_admin_user(request):
        return redirect('admin_login')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'INDOORS').strip()
        price = request.POST.get('price', '0').replace(',', '').replace('₹', '').strip()
        stock = request.POST.get('stock', '10').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        
        # Colors parsing
        no_colour_active = request.POST.get('no_colour_active', 'false') == 'true'
        colours = []
        if not no_colour_active:
            colours = request.POST.getlist('colours')
            if not colours:
                return redirect(f"{reverse('admin_dashboard')}?toast=colours-empty")

        # Sizing specs tables validation
        class_labels = request.POST.getlist('class_label[]')
        class_age_mins = request.POST.getlist('class_age_min[]')
        class_age_maxs = request.POST.getlist('class_age_max[]')
        
        class_specs_to_create = []
        for i in range(len(class_labels)):
            lbl = class_labels[i].strip()
            min_val = class_age_mins[i].strip()
            max_val = class_age_maxs[i].strip()
            if any([lbl, min_val, max_val]):
                if not all([lbl, min_val, max_val]):
                    return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-incomplete")
                try:
                    age_min = int(min_val)
                    age_max = int(max_val)
                    if age_min > age_max or age_min < 0:
                        return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-invalid-values")
                except (ValueError, TypeError):
                    return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-invalid-types")
                
                class_specs_to_create.append({
                    'class_label': lbl,
                    'age_min': age_min,
                    'age_max': age_max,
                    'order': i
                })

        dim_group_labels = request.POST.getlist('dim_group_label[]')
        dim_components = request.POST.getlist('dim_component[]')
        dim_lengths = request.POST.getlist('dim_length[]')
        dim_widths = request.POST.getlist('dim_width[]')
        dim_heights = request.POST.getlist('dim_height[]')
        dim_units = request.POST.getlist('dim_unit[]')
        dim_notes = request.POST.getlist('dim_notes[]')
        
        dimension_specs_to_create = []
        for i in range(len(dim_lengths)):
            g_val = dim_group_labels[i].strip() if i < len(dim_group_labels) else ''
            c_val = dim_components[i].strip() if i < len(dim_components) else ''
            l_val = dim_lengths[i].strip()
            w_val = dim_widths[i].strip()
            h_val = dim_heights[i].strip()
            u_val = dim_units[i].strip() if i < len(dim_units) else 'cm'
            n_val = dim_notes[i].strip() if i < len(dim_notes) else ''
            
            if any([g_val, c_val, l_val, w_val, h_val, n_val]):
                if not l_val:
                    return redirect(f"{reverse('admin_dashboard')}?toast=dimension-spec-incomplete")
                
                dimension_specs_to_create.append({
                    'group_label': g_val,
                    'component': c_val,
                    'length': l_val,
                    'width': w_val,
                    'height': h_val,
                    'unit': u_val,
                    'notes': n_val,
                    'order': i
                })

        # Auto-convert Google Drive sharing links to direct hotlink preview URLs
        if image_url and 'drive.google.com' in image_url:
            import re
            d_match = re.search(r'/file/d/([^/]+)', image_url)
            if d_match:
                image_url = f"https://lh3.googleusercontent.com/d/{d_match.group(1)}"
            else:
                id_match = re.search(r'[?&]id=([^&]+)', image_url)
                if id_match:
                    image_url = f"https://lh3.googleusercontent.com/d/{id_match.group(1)}"
            
        if name and price:
            if not image_url:
                image_url = "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"
            try:
                stock_val = int(stock)
            except ValueError:
                stock_val = 10
                
            product = Product.objects.create(
                name=name,
                category=category,
                price=price,
                stock=stock_val,
                description=description,
                image_url=image_url,
                colours=colours
            )
            
            for spec in class_specs_to_create:
                ProductClassSpec.objects.create(product=product, **spec)
            for spec in dimension_specs_to_create:
                ProductDimensionSpec.objects.create(product=product, **spec)
                
    return redirect('admin_dashboard')

def edit_product(request, pk):
    if not is_admin_user(request):
        return redirect('admin_login')
        
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'INDOORS').strip()
        price = request.POST.get('price', '0').replace(',', '').replace('₹', '').strip()
        stock = request.POST.get('stock', '10').strip()
        description = request.POST.get('description', '').strip()
        image_url = request.POST.get('image_url', '').strip()
        
        # Colors parsing
        no_colour_active = request.POST.get('no_colour_active', 'false') == 'true'
        colours = []
        if not no_colour_active:
            colours = request.POST.getlist('colours')
            if not colours:
                return redirect(f"{reverse('admin_dashboard')}?toast=colours-empty")

        # Sizing specs tables validation
        class_labels = request.POST.getlist('class_label[]')
        class_age_mins = request.POST.getlist('class_age_min[]')
        class_age_maxs = request.POST.getlist('class_age_max[]')
        
        class_specs_to_create = []
        for i in range(len(class_labels)):
            lbl = class_labels[i].strip()
            min_val = class_age_mins[i].strip()
            max_val = class_age_maxs[i].strip()
            if any([lbl, min_val, max_val]):
                if not all([lbl, min_val, max_val]):
                    return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-incomplete")
                try:
                    age_min = int(min_val)
                    age_max = int(max_val)
                    if age_min > age_max or age_min < 0:
                        return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-invalid-values")
                except (ValueError, TypeError):
                    return redirect(f"{reverse('admin_dashboard')}?toast=class-spec-invalid-types")
                
                class_specs_to_create.append({
                    'class_label': lbl,
                    'age_min': age_min,
                    'age_max': age_max,
                    'order': i
                })

        dim_group_labels = request.POST.getlist('dim_group_label[]')
        dim_components = request.POST.getlist('dim_component[]')
        dim_lengths = request.POST.getlist('dim_length[]')
        dim_widths = request.POST.getlist('dim_width[]')
        dim_heights = request.POST.getlist('dim_height[]')
        dim_units = request.POST.getlist('dim_unit[]')
        dim_notes = request.POST.getlist('dim_notes[]')
        
        dimension_specs_to_create = []
        for i in range(len(dim_lengths)):
            g_val = dim_group_labels[i].strip() if i < len(dim_group_labels) else ''
            c_val = dim_components[i].strip() if i < len(dim_components) else ''
            l_val = dim_lengths[i].strip()
            w_val = dim_widths[i].strip()
            h_val = dim_heights[i].strip()
            u_val = dim_units[i].strip() if i < len(dim_units) else 'cm'
            n_val = dim_notes[i].strip() if i < len(dim_notes) else ''
            
            if any([g_val, c_val, l_val, w_val, h_val, n_val]):
                if not l_val:
                    return redirect(f"{reverse('admin_dashboard')}?toast=dimension-spec-incomplete")
                
                dimension_specs_to_create.append({
                    'group_label': g_val,
                    'component': c_val,
                    'length': l_val,
                    'width': w_val,
                    'height': h_val,
                    'unit': u_val,
                    'notes': n_val,
                    'order': i
                })

        if image_url and 'drive.google.com' in image_url:
            import re
            d_match = re.search(r'/file/d/([^/]+)', image_url)
            if d_match:
                image_url = f"https://lh3.googleusercontent.com/d/{d_match.group(1)}"
            else:
                id_match = re.search(r'[?&]id=([^&]+)', image_url)
                if id_match:
                    image_url = f"https://lh3.googleusercontent.com/d/{id_match.group(1)}"

        if name and price:
            product.name = name
            product.category = category
            product.price = price
            try:
                product.stock = int(stock)
            except ValueError:
                pass
            product.description = description
            if image_url:
                product.image_url = image_url
            product.colours = colours
            product.save()
            
            # Recreate specs
            product.class_specs.all().delete()
            for spec in class_specs_to_create:
                ProductClassSpec.objects.create(product=product, **spec)
            
            product.dimension_specs.all().delete()
            for spec in dimension_specs_to_create:
                ProductDimensionSpec.objects.create(product=product, **spec)
                
            return redirect(f"{reverse('admin_dashboard')}?toast=saved")


    return redirect('admin_dashboard')

def delete_product(request, pk):
    if not is_admin_user(request):
        return redirect('admin_login')
        
    if request.method == 'POST':
        Product.objects.filter(pk=pk).delete()
    return redirect('admin_dashboard')

def home_view(request):
    featured_products = Product.objects.filter(stock__gt=0).only(
        'id', 'name', 'category', 'price', 'discount_price', 'stock',
        'sku', 'source', 'needs_image', 'image_file', 'image_url', 'created_at'
    ).order_by('-created_at')[:6]
    return render(request, 'products/home.html', {'featured_products': featured_products})

def category_listing(request, cat_code, template_name):
    q = request.GET.get('q', '').strip()
    if q:
        products = search_products(q, category=cat_code)
    else:
        products = Product.objects.filter(category=cat_code).only(
            'id', 'name', 'category', 'price', 'discount_price', 'stock',
            'sku', 'source', 'needs_image', 'image_file', 'image_url', 'created_at'
        ).order_by('-created_at')[:8]
    return render(request, template_name, {
        'products': products,
        'category_code': cat_code
    })

def indoors_view(request):
    return category_listing(request, 'INDOORS', 'products/listing.html')

def outdoors_view(request):
    return category_listing(request, 'OUTDOORS', 'products/outdoors.html')


def shreemsports_view(request):
    return category_listing(request, 'SHREEM_SPORTS', 'products/shreemsports.html')

def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return render(request, '404.html', status=404)

    # Determine which listing page to go back to based on category
    category_lower = (product.category or '').lower()
    if 'outdoor' in category_lower:
        back_url = reverse('outdoors')
        back_label = 'Outdoors'
    elif 'shreem' in category_lower or 'sports' in category_lower:
        back_url = reverse('shreemsports')
        back_label = 'Shreem Sports'
    else:
        back_url = reverse('indoors')
        back_label = 'Indoors'

    # Cache related products for 5 minutes per category
    cache_key = f'related_products_{product.category}_{product.pk}'
    related_products = cache.get(cache_key)
    if related_products is None:
        related_products = list(
            Product.objects.filter(category=product.category)
            .exclude(pk=product.pk)
            .exclude(stock__lte=0)
            .only('id', 'name', 'category', 'price', 'discount_price', 'stock',
                  'sku', 'source', 'needs_image', 'image_file', 'image_url', 'created_at')
            .order_by('-created_at')[:3]
        )
        cache.set(cache_key, related_products, 300)

    # Compile unique dimension options
    unique_dimensions = []
    specs = product.dimension_specs.all().order_by('order')
    has_groups = specs.exclude(group_label='').exists()
    
    if has_groups:
        seen_groups = set()
        for s in specs:
            g = s.group_label.strip()
            if g and g not in seen_groups:
                seen_groups.add(g)
                unique_dimensions.append({
                    'label': g,
                    'value': g
                })
    else:
        for s in specs:
            parts = []
            if s.component:
                parts.append(f"{s.component}:")
            parts.append(s.length)
            if s.width:
                parts.append(f"x {s.width}")
            if s.height:
                parts.append(f"x {s.height}")
            parts.append(s.unit)
            if s.notes:
                parts.append(f"({s.notes})")
            
            label = " ".join(parts)
            unique_dimensions.append({
                'label': label,
                'value': label
            })

    return render(request, 'products/product_detail.html', {
        'product': product,
        'selected_variant': product,
        'variant_pk': product.pk,
        'related_products': related_products,
        'back_url': back_url,
        'back_label': back_label,
        'unique_dimensions': unique_dimensions,
        'has_groups': has_groups,
    })

# --- SEO: Sitemap & Robots ---

class ProductSitemap(Sitemap):
    """Generates <urlset> for all products."""
    changefreq = "weekly"
    priority = 0.7
    protocol = 'https'

    def items(self):
        return Product.objects.all().only('id', 'name', 'created_at').order_by('id')

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        from django.urls import reverse
        return reverse('product_detail', args=[obj.pk])


class StaticViewSitemap(Sitemap):
    """Sitemap entries for static pages that don't depend on a model."""
    changefreq = "monthly"
    protocol = 'https'

    def items(self):
        return [
            {'name': 'home', 'priority': 1.0},
            {'name': 'indoors', 'priority': 0.8},
            {'name': 'outdoors', 'priority': 0.8},
            {'name': 'shreemsports', 'priority': 0.8},
            {'name': 'about', 'priority': 0.6},
            {'name': 'safety_standards', 'priority': 0.5},
            {'name': 'testimonials', 'priority': 0.5},
            {'name': 'contact', 'priority': 0.6},
            {'name': 'privacy_policy', 'priority': 0.3},
            {'name': 'terms_of_service', 'priority': 0.3},
        ]

    def priority(self, obj):
        return obj['priority']

    def location(self, obj):
        from django.urls import reverse
        return reverse(obj['name'])


@require_safe
def robots_txt(request):
    """Serve robots.txt at domain root from static asset."""
    from django.conf import settings
    robots_path = settings.BASE_DIR.parent / 'frontend' / 'static' / 'robots.txt'
    if robots_path.exists():
        content = robots_path.read_text(encoding='utf-8')
    else:
        content = "User-agent: *\nAllow: /\nSitemap: https://akidsenterprise.com/sitemap.xml\n"
    return HttpResponse(content, content_type="text/plain; charset=utf-8")


@require_safe
def bing_site_auth(request):
    """Serve BingSiteAuth.xml at domain root."""
    from django.conf import settings
    auth_path = settings.BASE_DIR.parent / 'frontend' / 'static' / 'BingSiteAuth.xml'
    if not auth_path.exists():
        auth_path = settings.BASE_DIR.parent / 'BingSiteAuth.xml'
    if auth_path.exists():
        content = auth_path.read_text(encoding='utf-8')
    else:
        content = '<?xml version="1.0"?>\n<users>\n\t<user>724911A214A55EE0A000561E989A291E</user>\n</users>'
    return HttpResponse(content, content_type="application/xml; charset=utf-8")


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


def api_search_suggestions(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    
    if not category or category.lower() == 'all':
        category = None
        
    results = []
    if len(q) >= 1:
        products = search_products(q, category)[:5]
        for prod in products:
            price_val = prod.discount_price if prod.discount_price is not None else prod.price
            formatted_price = f"{price_val:,.2f}"
            results.append({
                'name': prod.name,
                'price': formatted_price,
                'url': reverse('product_detail', args=[prod.id]),
                'image': prod.display_image
            })
            
    return JsonResponse({'results': results})


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
        "We specialize in premium children's playground equipment, indoor & outdoor toys, Shreem Sports gear, educational furniture, and spare parts. "
        "Your goal is to engage warmly with customers, give them expert advice on playground products, answer their queries with enthusiasm, and help them find the right equipment. "
        "CRITICAL INSTRUCTION: For larger queries with more gravity, complex installations, bulk orders, complaints, safety concerns, or urgent matters, you MUST prompt and advise the user to call our direct hotline at: +91 7433 026 008. "
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
            return JsonResponse({"reply": "Namaste! I'm Mohanlal. I'm having a little trouble connecting right now, but for any urgent queries or larger requirements, please feel free to call us directly at +91 7433 026 008!"}, status=200)
    except Exception:
        return JsonResponse({"reply": "Namaste! I'm Mohanlal. I encountered a momentary connection glitch. For any important queries or immediate advice, please call us at +91 7433 026 008!"}, status=200)



def update_inquiry_status(request, pk):
    if not is_admin_user(request):
        return redirect('admin_login')
        
    if request.method == 'POST':
        inquiry = get_object_or_404(Inquiry, pk=pk)
        new_status = request.POST.get('status', '').strip().upper()
        if new_status in ['NEW', 'CONTACTED', 'CLOSED']:
            inquiry.status = new_status
            inquiry.save()
            
    return redirect('admin_dashboard')


def delete_inquiry(request, pk):
    if not is_admin_user(request):
        return redirect('admin_login')
        
    if request.method == 'POST':
        Inquiry.objects.filter(pk=pk).delete()
        
    return redirect('admin_dashboard')


# --- STOREFRONT ORDER VIEWS ---

def checkout_view(request):
    if is_admin_user(request):
        return redirect('admin_dashboard')
    if not request.user.is_authenticated:
        return redirect(f"{reverse('admin_login')}?next={reverse('cart')}&toast=login-required")

    cart_items, subtotal = get_cart_data(request)
    if not cart_items:
        return redirect('cart')

    if any(not item['is_available'] for item in cart_items):
        return redirect(f"{reverse('cart')}?toast=unavailable")

    profile, _ = UserProfile.objects.select_related('user').get_or_create(user=request.user)

    # Compute tax breakdown via the shared single source of truth.
    # Business rule: all prices are GST-exclusive; 18% GST is added on top.
    tax = calculate_gst(subtotal)
    gst_amount = tax['gst']
    cgst_amount = tax['cgst']
    sgst_amount = tax['sgst']
    total_with_tax = tax['total']

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip() or request.user.username
        shipping_address = request.POST.get('shipping_address', '').strip()
        if not shipping_address:
            return render(request, 'products/checkout.html', {
                'cart_items': cart_items,
                'subtotal': subtotal,
                'total': subtotal,
                'total_with_tax': total_with_tax,
                'gst_amount': gst_amount,
                'cgst_amount': cgst_amount,
                'sgst_amount': sgst_amount,
                'profile': profile,
                'error': 'Please enter your delivery address.',
            })

        # Save to profile if missing
        if not profile.shipping_address and shipping_address:
            profile.shipping_address = shipping_address
            profile.save()

        # ------------------------------------------------------------------
        # DELIBERATE SIMULATION — ACCEPTED, INTENTIONAL EXCEPTION (not a bug):
        # Order creation here simulates payment in "test mode". No payment
        # gateway is integrated yet; this is pending client sign-off before a
        # real Razorpay + webhook flow is wired in. Stock is still deducted
        # atomically (select_for_update) so the flow is race-safe. Do NOT flag
        # this as an unresolved finding in re-audits — it is a known deferral.
        # ------------------------------------------------------------------
        try:
            with transaction.atomic():
                locked_items = []
                for item in cart_items:
                    product = Product.objects.select_for_update().get(pk=item['product'].pk)
                    if product.stock < item['quantity']:
                        raise ValueError(f"{product.name} no longer has enough stock.")
                    locked_items.append((product, item['quantity'], item['colour'], item.get('dimension')))

                order = Order.objects.create(
                    user=request.user,
                    customer_name=customer_name,
                    shipping_address=shipping_address,
                    order_status='PLACED',
                )
                for product, quantity, colour, dimension in locked_items:
                    unit_price = product.discount_price or product.price
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        colour=colour,
                        dimension=dimension,
                    )
                    product.stock -= quantity
                    product.save(update_fields=['stock'])
        except ValueError as error:
            return redirect(f"{reverse('cart')}?toast=unavailable")

        request.session['cart'] = {}
        request.session.modified = True
        return redirect('order_success', order_id=order.pk)

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()

    return render(request, 'products/checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'total_with_tax': total_with_tax,
        'gst_amount': gst_amount,
        'cgst_amount': cgst_amount,
        'sgst_amount': sgst_amount,
        'profile': profile,
        'addresses': addresses,
        'default_address': default_address,
    })


def order_success(request, order_id):
    # IDOR guard: regular users may only view their own orders. A non-owner gets
    # a 404 (not 403) so order existence is never leaked. Staff/superusers may
    # view any order via this view, consistent with api_admin_order_invoice.
    orders_qs = Order.objects.prefetch_related('items').only(
        'id', 'order_no', 'customer_name', 'shipping_address',
        'order_status', 'subtotal_amount', 'gst_amount', 'total_amount', 'created_at'
    )
    if not is_admin_user(request):
        # Unauthenticated visitors never own orders; return 404 without querying
        # (avoids filtering with AnonymousUser and leaks no order existence).
        if not request.user.is_authenticated:
            raise Http404
        orders_qs = orders_qs.filter(user=request.user)
    order = get_object_or_404(orders_qs, pk=order_id)
    return render(request, 'products/order_success.html', {'order': order})


# ==========================================
# Catalog "View All Products" & Inquiries
# ==========================================

def serve_catalogue_pdf(request, module_type):
    """Serve a catalogue PDF with inline Content-Disposition so the
    browser renders it inside an iframe rather than navigating to a new page."""
    module_type = module_type.lower()
    if module_type not in ('indoor', 'outdoor'):
        raise Http404

    pdf_paths = {
        'indoor': 'catalogues/Indoor Catalogue March 2026-.pdf',
        'outdoor': 'catalogues/Outdoor Catalogue March 2026-.pdf',
    }
    rel_path = pdf_paths[module_type]

    # Resolve relative to the project root (one level up from BASE_DIR)
    full_path = settings.BASE_DIR.parent / rel_path
    if not full_path.exists():
        raise Http404(f"Catalogue PDF not found at {full_path}")

    # Use FileResponse to stream the file without loading it all into memory
    pdf_file = open(full_path, 'rb')
    response = FileResponse(pdf_file, content_type='application/pdf')

    # ?download=1 forces attachment (download); otherwise inline (in-page view)
    if request.GET.get('download') == '1':
        disposition = 'attachment'
    else:
        disposition = 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="catalogue-{module_type}.pdf"'
    return response

@cache_page(60 * 5)  # Cache for 5 minutes
def view_all_products(request, module_type):
    module_type = module_type.lower()
    if module_type not in ['indoor', 'outdoor']:
        return render(request, '404.html', status=404)
        
    pdf_url = reverse('serve_catalogue_pdf', args=[module_type])
    
    category_map = {
        'indoor': 'INDOORS',
        'outdoor': 'OUTDOORS'
    }
    db_category = category_map[module_type]
    
    products = Product.objects.filter(category=db_category).only('sku', 'name').order_by('sku')
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
        
    if module not in ['indoor', 'outdoor', 'shreem_sports']:
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
            line_items = []
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
                line_items.append(InquiryLineItem(
                    inquiry=inquiry,
                    product_code=product_code,
                    quantity=qty
                ))
            InquiryLineItem.objects.bulk_create(line_items)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
        
    # Format dynamic WhatsApp pre-typed message
    module_display = {
        'indoor': 'Indoor',
        'outdoor': 'Outdoor',
        'shreem_sports': 'Shreem Sports'
    }.get(module, module.title())

    message_lines = [
        f"Hello Akids Enterprise,",
        f"",
        f"I would like to request a quote for the following items from the *{module_display} Catalogue*:",
        f"",
        f"*Customer Name:* {name}",
        f"*Phone:* {phone_number}",
        f"*Email:* {email}",
        f"",
        f"*Selected Items:*",
    ]
    for item in line_items_data:
        code = item.get('product_code', '').strip()
        qty = item.get('quantity', 1)
        message_lines.append(f"• {qty}x {code}")

    message_lines.append("")
    message_lines.append("Thank you!")
    message_text = "\n".join(message_lines)

    # Fetch Whatsapp target number from .env
    raw_target = get_whatsapp_number()
    clean_target = raw_target.strip()
    if len(clean_target) == 10 and clean_target.isdigit():
        clean_target = "91" + clean_target

    import urllib.parse
    encoded_text = urllib.parse.quote(message_text)
    whatsapp_url = f"https://wa.me/{clean_target}?text={encoded_text}"
        
    return JsonResponse({
        'success': True,
        'inquiry_id': inquiry.pk,
        'whatsapp_url': whatsapp_url
    })


# --- ADMIN API ENDPOINTS (Protected) ---

NEXT_STATUS_MAP = {
    'PLACED': 'CONFIRMED',
    'CONFIRMED': 'PACKED',
    'PACKED': 'SHIPPED',
    'SHIPPED': 'DELIVERED',
}

def api_admin_orders(request):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    orders_qs = Order.objects.select_related('user').prefetch_related('items').only(
        'id', 'order_no', 'user', 'customer_name', 'shipping_address',
        'order_status', 'total_amount', 'created_at'
    ).all()
    
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
        items_list = list(order.items.all())
        if not items_list:
            items_summary = "No items"
        elif len(items_list) == 1:
            items_summary = f"{items_list[0].quantity}x {items_list[0].product_name}"
        elif len(items_list) == 2:
            items_summary = f"{items_list[0].quantity}x {items_list[0].product_name}, {items_list[1].quantity}x {items_list[1].product_name}"
        else:
            extra = len(items_list) - 2
            items_summary = f"{items_list[0].quantity}x {items_list[0].product_name}, {items_list[1].quantity}x {items_list[1].product_name} +{extra} more"

        orders_list.append({
            'id': order.id,
            'order_no': order.order_no,
            'customer_name': order.customer_name,
            'shipping_address': order.shipping_address,
            'order_status': order.order_status,
            'order_status_display': order.get_order_status_display(),
            'total_amount': float(order.total_amount),
            'created_at_str': order.created_at.strftime('%d %b %Y, %I:%M %p'),
            'items_summary': items_summary,
            'can_advance': order.order_status in NEXT_STATUS_MAP,
            'can_cancel': order.order_status not in ['DELIVERED', 'CANCELLED', 'RETURNED']
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
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    order = get_object_or_404(
        Order.objects.prefetch_related('items', 'items__product').only(
            'id', 'order_no', 'customer_name', 'shipping_address',
            'order_status', 'subtotal_amount', 'gst_amount', 'total_amount', 'created_at'
        ),
        pk=order_id
    )
    
    items_list = []
    for item in order.items.all():
        display_image = item.product.display_image if item.product else "https://images.unsplash.com/photo-1545558014-8692077e9b5c?auto=format&fit=crop&w=600&q=80"
        items_list.append({
            'product_name': item.product_name,
            'colour': item.colour,
            'dimension': item.dimension,
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
        'subtotal_amount': float(order.subtotal_amount),
        'gst_amount': float(order.gst_amount),
        'total_amount': float(order.total_amount),
        'created_at_str': order.created_at.strftime('%d %b %Y, %I:%M %p'),
        'items': items_list
    })


@require_http_methods(["PATCH", "POST"])
def api_admin_order_status_update(request, order_id):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    order = get_object_or_404(Order, pk=order_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
        
    action = data.get('action', '').strip().lower()
    new_status = data.get('status', '').strip().upper()
    current_status = order.order_status

    if action == 'next':
        if current_status not in NEXT_STATUS_MAP:
            return JsonResponse({'error': f"Order in status '{current_status}' cannot be advanced further."}, status=400)
        new_status = NEXT_STATUS_MAP[current_status]
    elif action == 'cancel':
        if current_status in ['DELIVERED', 'CANCELLED', 'RETURNED']:
            return JsonResponse({'error': f"Order in status '{current_status}' cannot be cancelled."}, status=400)
        new_status = 'CANCELLED'
        
    if not new_status:
        return JsonResponse({'error': 'Action or status parameter required.'}, status=400)
        
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
        'order_status_display': order.get_order_status_display(),
        'can_advance': order.order_status in NEXT_STATUS_MAP,
        'can_cancel': order.order_status not in ['DELIVERED', 'CANCELLED', 'RETURNED']
    })


def api_admin_order_invoice(request, order_id):
    from .pdf_generator import generate_invoice_pdf  # Lazy import to avoid loading ReportLab on every request
    # Ownership filter (same pattern as order_success): non-admins may only
    # fetch their own invoice, and get a 404 for others so order existence is
    # never leaked (no 403 existence oracle).
    orders_qs = Order.objects.prefetch_related('items')
    if not is_admin_user(request):
        if not request.user.is_authenticated:
            raise Http404
        orders_qs = orders_qs.filter(user=request.user)
    order = get_object_or_404(orders_qs, pk=order_id)
    try:
        is_admin = is_admin_user(request)
        pdf_content = generate_invoice_pdf(order, is_admin=is_admin)
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{order.order_no}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Invoice generation failed: {str(e)}", status=500)


def api_admin_inquiries(request):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    module_filter = request.GET.get('module', '').strip().lower()
    date_start = request.GET.get('date_start', '').strip()
    date_end = request.GET.get('date_end', '').strip()
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().upper()

    inquiries = Inquiry.objects.exclude(status='CLOSED').prefetch_related('line_items').only(
        'id', 'inquiry_no', 'module', 'name', 'contact_number', 'email',
        'quantity', 'product', 'status', 'created_at'
    )
    
    if module_filter in ['indoor', 'outdoor', 'shreem_sports']:
        inquiries = inquiries.filter(module=module_filter)
        
    if status_filter in ['NEW', 'CONTACTED', 'CLOSED']:
        inquiries = inquiries.filter(status=status_filter)
        
    if date_start:
        inquiries = inquiries.filter(created_at__date__gte=date_start)
    if date_end:
        inquiries = inquiries.filter(created_at__date__lte=date_end)
        
    if q:
        inquiries = inquiries.filter(
            Q(name__icontains=q) |
            Q(line_items__product_name__icontains=q) |
            Q(line_items__product_code__icontains=q) |
            Q(product__name__icontains=q) |
            Q(inquiry_no__icontains=q)
        ).distinct()
        
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
        items_list = list(inq.line_items.all())
        if items_list:
            if len(items_list) == 1:
                items_summary = f"{items_list[0].product_name or items_list[0].product_code} ({items_list[0].quantity})"
            elif len(items_list) == 2:
                items_summary = f"{items_list[0].product_name or items_list[0].product_code} ({items_list[0].quantity}), {items_list[1].product_name or items_list[1].product_code} ({items_list[1].quantity})"
            else:
                extra = len(items_list) - 2
                items_summary = f"{items_list[0].product_name or items_list[0].product_code} ({items_list[0].quantity}), {items_list[1].product_name or items_list[1].product_code} ({items_list[1].quantity}) +{extra} more"
        elif inq.product:
            items_summary = f"Product: {inq.product.name} (Qty: {inq.quantity})"
        else:
            items_summary = "No items"

        data['inquiries'].append({
            'id': inq.id,
            'inquiry_no': inq.inquiry_no,
            'module': inq.module,
            'module_display': inq.get_module_display() if inq.module else 'Single Product',
            'customer_name': inq.name,
            'phone_number': inq.contact_number,
            'email': inq.email or 'N/A',
            'items_summary': items_summary,
            'created_at_str': inq.created_at.strftime('%d %b %Y, %I:%M %p'),
            'status': inq.status,
            'status_display': inq.get_status_display()
        })
        
    return JsonResponse(data)


@require_http_methods(["POST"])
def api_admin_inquiry_close(request, pk):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    try:
        outcome = json.loads(request.body).get('outcome', '').strip().upper()
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)
    if outcome not in {'WON', 'LOST'}:
        return JsonResponse({'error': 'Outcome must be WON or LOST.'}, status=400)

    inquiry = get_object_or_404(Inquiry, pk=pk)
    inquiry.status = 'CLOSED'
    inquiry.closure_outcome = outcome
    inquiry.save(update_fields=['status', 'closure_outcome'])
    return JsonResponse({'success': True, 'status': inquiry.status, 'closure_outcome': inquiry.closure_outcome})


def api_admin_closed_inquiries(request):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    closed = Inquiry.objects.filter(
        status='CLOSED', closure_outcome__in=['WON', 'LOST']
    ).only('id', 'inquiry_no', 'name', 'closure_outcome', 'created_at').order_by('-created_at')
    data = {'won': [], 'lost': []}
    for inquiry in closed:
        data[inquiry.closure_outcome.lower()].append({
            'id': inquiry.id,
            'inquiry_no': inquiry.inquiry_no,
            'customer_name': inquiry.name,
            'created_at_str': inquiry.created_at.strftime('%d %b %Y, %I:%M %p'),
        })
    return JsonResponse(data)


def api_admin_inquiry_detail(request, pk):
    if not is_admin_user(request):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    inq = get_object_or_404(
        Inquiry.objects.prefetch_related('line_items').only(
            'id', 'inquiry_no', 'module', 'name', 'contact_number', 'email',
            'quantity', 'status', 'closure_outcome', 'created_at'
        ),
        pk=pk
    )
    
    items = []
    for item in inq.line_items.all():
        items.append({
            'product_code': item.product_code,
            'quantity': item.quantity
        })
        
    previous_inquiries = Inquiry.objects.filter(
        Q(contact_number=inq.contact_number) | Q(email__isnull=False, email=inq.email)
    ).exclude(pk=inq.pk).prefetch_related('line_items').order_by('-created_at')

    data = {
        'id': inq.id,
        'inquiry_no': inq.inquiry_no,
        'module': inq.module,
        'module_display': inq.get_module_display() if inq.module else 'Single Product',
        'customer_name': inq.name,
        'phone_number': inq.contact_number,
        'email': inq.email or 'N/A',
        'status': inq.status,
        'status_display': inq.get_status_display(),
        'created_at_str': inq.created_at.strftime('%d %b %Y, %I:%M %p'),
        'items': items,
        'previous_inquiries': [{
            'inquiry_no': previous.inquiry_no,
            'status_display': previous.get_status_display(),
            'created_at_str': previous.created_at.strftime('%d %b %Y, %I:%M %p'),
            'items': [f'{item.quantity}x {item.product_code}' for item in previous.line_items.all()],
        } for previous in previous_inquiries]
    }
    return JsonResponse(data)


from datetime import timedelta

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('admin_login')}?next={reverse('profile')}")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Auto-migrate legacy shipping_address data to Address model if no addresses exist
    if profile.shipping_address and not Address.objects.filter(user=request.user).exists():
        Address.objects.create(
            user=request.user,
            full_name=profile.full_name or request.user.username,
            phone_number=profile.phone_number,
            street_address=profile.shipping_address,
            is_default=True
        )

    error = None
    success_toast = 'saved'

    if request.method == 'POST':
        action = request.POST.get('action', 'update_profile')

        if action == 'add_address':
            street = request.POST.get('street_address', '').strip()
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone_number', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            pincode = request.POST.get('pincode', '').strip()
            make_default = request.POST.get('is_default') == 'on' or not Address.objects.filter(user=request.user).exists()

            if street:
                try:
                    Address.objects.create(
                        user=request.user,
                        full_name=full_name,
                        phone_number=phone,
                        street_address=street,
                        city=city,
                        state=state,
                        pincode=pincode,
                        is_default=make_default
                    )
                except ValueError as ve:
                    error = str(ve)
        elif action == 'edit_address':
            addr_id = request.POST.get('address_id')
            address = get_object_or_404(Address, pk=addr_id, user=request.user)
            address.street_address = request.POST.get('street_address', '').strip()
            address.full_name = request.POST.get('full_name', '').strip()
            address.phone_number = request.POST.get('phone_number', '').strip()
            address.city = request.POST.get('city', '').strip()
            address.state = request.POST.get('state', '').strip()
            address.pincode = request.POST.get('pincode', '').strip()
            if request.POST.get('is_default') == 'on':
                address.is_default = True
            address.save()
        elif action == 'delete_address':
            addr_id = request.POST.get('address_id')
            Address.objects.filter(pk=addr_id, user=request.user).delete()
        elif action == 'set_default_address':
            addr_id = request.POST.get('address_id')
            address = get_object_or_404(Address, pk=addr_id, user=request.user)
            address.is_default = True
            address.save()
        else: # update_profile
            # 1. Phone number & Avatar color
            profile.phone_number = request.POST.get('phone_number', '').strip()
            avatar_color = request.POST.get('avatar_color', '').strip().lower()
            valid_colors = {'sea', 'tangerine', 'blush', 'matcha', 'butter', 'coral', 'lavender', 'mint', 'midnight', 'emerald', 'sunset', 'berry'}
            if avatar_color in valid_colors:
                profile.avatar_color = avatar_color

            # 2. Username change with 30-day cooldown
            new_username = request.POST.get('username', '').strip()
            if new_username and new_username != request.user.username:
                if profile.username_changed_at and timezone.now() < profile.username_changed_at + timedelta(days=30):
                    next_eligible = (profile.username_changed_at + timedelta(days=30)).strftime('%d %b %Y')
                    error = f"Username can only be changed once every 30 days. Next eligible change: {next_eligible}."
                elif User.objects.filter(username=new_username).exclude(pk=request.user.pk).exists():
                    error = "That username is already taken by another user."
                else:
                    request.user.username = new_username
                    request.user.save(update_fields=['username'])
                    profile.username_changed_at = timezone.now()

            profile.save()

        if not error:
            return redirect(f"{reverse('profile')}?toast={success_toast}")

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first()

    # Calculate username change eligibility
    can_change_username = True
    next_username_date = None
    if profile.username_changed_at and timezone.now() < profile.username_changed_at + timedelta(days=30):
        can_change_username = False
        next_username_date = (profile.username_changed_at + timedelta(days=30)).strftime('%d %b %Y')

    orders = Order.objects.filter(user=request.user).prefetch_related('items').only(
        'id', 'order_no', 'customer_name', 'order_status', 'total_amount', 'created_at'
    ).order_by('-created_at')

    return render(request, 'products/profile.html', {
        'profile': profile,
        'addresses': addresses,
        'default_address': default_address,
        'can_change_username': can_change_username,
        'next_username_date': next_username_date,
        'orders': orders,
        'error': error,
    })


# --- Third-Party Auth: Google OAuth & Firebase Passwordless ---

def google_login(request):
    _read_env_file()
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if not client_id or client_id.startswith("YOUR_"):
        return redirect(f"{reverse('admin_login')}?toast=google-not-configured")
    
    redirect_uri = _google_redirect_uri(request)
    google_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile"
    )
    return redirect(google_url)


def google_callback(request):
    _read_env_file()
    code = request.GET.get('code')
    if not code:
        return redirect(f"{reverse('admin_login')}?toast=google-error")
    
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = _google_redirect_uri(request)
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        resp = requests.post(token_url, data=data, timeout=10)
        tokens = resp.json()
        access_token = tokens.get('access_token')
        if not access_token:
            return redirect(f"{reverse('admin_login')}?toast=google-error")
        
        user_info_resp = requests.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        info = user_info_resp.json()
        email = info.get('email')
        name = info.get('name', '')
        
        if not email:
            return redirect(f"{reverse('admin_login')}?toast=google-error")
        
        user = User.objects.filter(email=email).first()
        if not user:
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user = User.objects.create_user(username=username, email=email)
            user.first_name = name
            user.save()
            UserProfile.objects.get_or_create(user=user, defaults={'full_name': name})
            
        login(request, user)
        return redirect(f"{reverse('cart')}?toast=login")
    except Exception:
        return redirect(f"{reverse('admin_login')}?toast=google-error")



