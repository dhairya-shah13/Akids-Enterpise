from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .forms import RegistrationForm, LoginForm, ProfileForm, AddressForm
from .models import Address


def register_view(request):
    """User registration — auto-login on success."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Akids, {user.get_short_name()}!')
            return redirect('core:home')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Email + password login with next redirect support."""
    if request.user.is_authenticated:
        return redirect('core:home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_short_name()}!')
                redirect_to = request.POST.get('next', '') or next_url or 'core:home'
                # If redirect_to is a URL name, resolve it; if it's a path, use directly
                if redirect_to.startswith('/'):
                    return redirect(redirect_to)
                return redirect(redirect_to)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """Log the user out and redirect to homepage."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """User profile with address management."""
    user = request.user
    addresses = user.addresses.all()

    # Profile form
    if request.method == 'POST' and 'update_profile' in request.POST:
        profile_form = ProfileForm(request.POST, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        profile_form = ProfileForm(instance=user)

    # Address form — add new
    if request.method == 'POST' and 'add_address' in request.POST:
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = user
            address.save()
            messages.success(request, 'Address added successfully.')
            return redirect('accounts:profile')
    else:
        address_form = AddressForm()

    # Stats
    from apps.orders.models import Order
    orders = Order.objects.filter(user=user, payment_status__in=['SIMULATED', 'PAID'])
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total'))['total'] or 0

    context = {
        'profile_form': profile_form,
        'address_form': address_form,
        'addresses': addresses,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_address_view(request, address_id):
    """Edit an existing address."""
    address = get_object_or_404(Address, pk=address_id, user=request.user)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('accounts:profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/edit_address.html', {
        'form': form,
        'address': address,
    })


@login_required
def delete_address_view(request, address_id):
    """Delete an address."""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted.')
    return redirect('accounts:profile')


@login_required
def set_default_address_view(request, address_id):
    """Set an address as the default."""
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f'"{address.label}" set as default address.')
    return redirect('accounts:profile')


@login_required
def order_history_view(request):
    """Show all orders for the logged-in user."""
    from apps.orders.models import Order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/order_history.html', {'orders': orders})
