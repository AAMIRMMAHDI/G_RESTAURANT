from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse
import json

from .models import MenuItem, Category, Order, OrderItem
from .forms import OrderForm


# --- نقش‌ها ---
def is_manager(user):
    return user.role in ['manager', 'order_manager']

def is_chef(user):
    return user.role == 'chef'

def is_waiter(user):
    return user.role == 'waiter'


# --- صفحه اصلی ---
def home(request):
    return render(request, 'home.html')


# --- منوی سفارش ---
@login_required
def order_menu(request):
    categories = Category.objects.all()
    menu_items = MenuItem.objects.filter(is_available=True).select_related('category')

    # تبدیل منو به JSON برای JS
    menu_items_json = json.dumps([{
        'id': item.id,
        'name': item.name,
        'price': int(item.price),
        'image': item.image.url if item.image else '/static/no-image.jpg'
    } for item in menu_items])

    form = OrderForm()

    # سبد خرید از sessionStorage (فرانت) + session (بک‌اند)
    cart = request.session.get('cart', [])

    if request.method == 'POST' and 'place_order' in request.POST:
        return redirect('index:place_order')

    return render(request, 'muno.html', {
        'menu_items': menu_items,
        'categories': categories,
        'form': form,
        'menu_items_json': menu_items_json,
        'cart': cart
    })


# --- API برای همگام‌سازی سبد خرید ---
@login_required
def sync_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        request.session['cart'] = data.get('cart', [])
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


# --- ثبت سفارش ---
@login_required
def place_order(request):
    cart = request.session.get('cart', [])
    if not cart:
        messages.warning(request, "سبد خرید خالی است.")
        return redirect('index:order_menu')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                user=request.user,
                table_number=form.cleaned_data['table_number'],
                special_requests=form.cleaned_data['special_requests']
            )

            for item in cart:
                menu_item = MenuItem.objects.get(id=item['id'])
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    price_at_order=menu_item.price
                )

            order.calculate_total()
            request.session['cart'] = []
            messages.success(request, "سفارش شما با موفقیت ثبت شد!")
            return redirect('index:home')
    else:
        form = OrderForm()

    return render(request, 'muno.html', {
        'form': form,
        'cart': cart,
        'menu_items': MenuItem.objects.filter(is_available=True),
        'categories': Category.objects.all()
    })


# --- پنل مدیر (تأیید سفارش) ---
@login_required
@user_passes_test(is_manager)
def manage_orders(request):
    orders = Order.objects.filter(status='pending').select_related('user').prefetch_related('items__menu_item')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id, status='pending')
        order.status = 'confirmed'
        order.save()
        messages.success(request, f"سفارش {order.id} تأیید شد.")
        return redirect('index:manage_orders')

    return render(request, 'manager_taiid.html', {'orders': orders})


# --- پنل آشپز ---
@login_required
@user_passes_test(is_chef)
def chef_panel(request):
    orders = Order.objects.filter(status__in=['confirmed', 'preparing']).select_related('user').prefetch_related('items__menu_item')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        action = request.POST.get('action')
        order = get_object_or_404(Order, id=order_id)

        if action == 'start' and order.status == 'confirmed':
            order.status = 'preparing'
            messages.success(request, f"شروع پخت سفارش {order.id}")
        elif action == 'finish' and order.status == 'preparing':
            order.status = 'ready'
            messages.success(request, f"سفارش {order.id} آماده شد")
        order.save()
        return redirect('index:chef_panel')

    return render(request, 'manager_aspazi.html', {'orders': orders})


# --- پنل گارسون ---
@login_required
@user_passes_test(is_waiter)
def waiter_panel(request):
    orders = Order.objects.filter(status='ready').select_related('user').prefetch_related('items__menu_item')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id, status='ready')
        order.status = 'delivered'
        order.save()
        messages.success(request, f"سفارش {order.id} تحویل مشتری شد.")
        return redirect('index:waiter_panel')

    today = timezone.now().date()
    delivered_today = Order.objects.filter(
        status='delivered',
        created_at__date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0

    return render(request, 'manager_garson.html', {
        'orders': orders,
        'delivered_today': delivered_today
    })