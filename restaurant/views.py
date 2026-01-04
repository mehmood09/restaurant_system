from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout as auth_logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Category, MenuItem, Cart, CartItem, Order, OrderItem
from .forms import RegisterForm, CheckoutForm, CategoryForm, MenuItemForm

def home(request):
    categories = Category.objects.all()[:6]
    featured_items = MenuItem.objects.filter(is_available=True)[:6]
    return render(request, 'restaurant/home.html', {
        'categories': categories,
        'featured_items': featured_items
    })

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'restaurant/registration/register.html', {'form': form})

@login_required
def menu_view(request):
    category_filter = request.GET.get('category')
    categories = Category.objects.all()
    
    if category_filter:
        menu_items = MenuItem.objects.filter(category_id=category_filter, is_available=True)
    else:
        menu_items = MenuItem.objects.filter(is_available=True)
    
    return render(request, 'restaurant/menu.html', {
        'categories': categories,
        'menu_items': menu_items,
        'selected_category': category_filter
    })

@login_required
def add_to_cart(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f'{menu_item.name} added to cart!')
    return redirect('menu')

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'restaurant/cart.html', {'cart': cart})

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated!')
        else:
            cart_item.delete()
            messages.success(request, 'Item removed from cart!')
    
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')

@login_required
def checkout_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty!')
        return redirect('menu')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            subtotal = cart.total
            tax = subtotal * Decimal('0.10')
            total = subtotal + tax
            
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = subtotal
            order.tax = tax
            order.total = total
            order.status = 'completed'  # Set status to completed immediately
            order.save()
            
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    menu_item_name=cart_item.menu_item.name,
                    quantity=cart_item.quantity,
                    price=cart_item.menu_item.price,
                    subtotal=cart_item.subtotal
                )
            
            cart.items.all().delete()
            messages.success(request, f'Order placed successfully! Token: {order.token_number}')
            return redirect('receipt', order_id=order.id)
    else:
        initial_data = {
            'customer_name': f"{request.user.first_name} {request.user.last_name}",
            'customer_email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)
    
    subtotal = cart.total
    tax = subtotal * Decimal('0.10')
    total = subtotal + tax
    
    return render(request, 'restaurant/checkout.html', {
        'form': form,
        'cart': cart,
        'subtotal': subtotal,
        'tax': tax,
        'total': total
    })

@login_required
def orders_view(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'restaurant/orders.html', {'orders': orders})

@login_required
def receipt_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'restaurant/receipt.html', {'order': order})

@login_required
def analytics_view(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_start = today.replace(day=1)
    
    # Calculate revenues for completed orders only
    daily_revenue = Order.objects.filter(
        created_at__date=today,
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    weekly_revenue = Order.objects.filter(
        created_at__date__gte=week_ago,
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    monthly_revenue = Order.objects.filter(
        created_at__date__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Total stats for all orders
    total_orders = Order.objects.filter(status='completed').count()
    pending_orders = Order.objects.filter(status__in=['pending', 'preparing', 'ready']).count()
    
    # Calculate total revenue (all time)
    total_revenue = Order.objects.filter(status='completed').aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    return render(request, 'restaurant/analytics.html', {
        'daily_revenue': daily_revenue,
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
    })

# Category Management Views
@staff_member_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'restaurant/category_list.html', {'categories': categories})

@staff_member_required
def category_add(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category added successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'restaurant/category_form.html', {'form': form, 'title': 'Add Category'})

@staff_member_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'restaurant/category_form.html', {'form': form, 'title': 'Edit Category'})

@staff_member_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    return render(request, 'restaurant/category_confirm_delete.html', {'category': category})

# Menu Item Management Views
@staff_member_required
def menuitem_list(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'restaurant/menuitem_list.html', {'menu_items': menu_items})

@staff_member_required
def menuitem_add(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('menuitem_list')
    else:
        form = MenuItemForm()
    return render(request, 'restaurant/menuitem_form.html', {'form': form, 'title': 'Add Menu Item'})

@staff_member_required
def menuitem_edit(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('menuitem_list')
    else:
        form = MenuItemForm(instance=menu_item)
    return render(request, 'restaurant/menuitem_form.html', {'form': form, 'title': 'Edit Menu Item'})

@staff_member_required
def menuitem_delete(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    if request.method == 'POST':
        menu_item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('menuitem_list')
    return render(request, 'restaurant/menuitem_confirm_delete.html', {'menu_item': menu_item})

@staff_member_required
def menuitem_toggle_availability(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    menu_item.is_available = not menu_item.is_available
    menu_item.save()
    status = "available" if menu_item.is_available else "unavailable"
    messages.success(request, f'{menu_item.name} is now {status}!')

    return redirect('menuitem_list')

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')
