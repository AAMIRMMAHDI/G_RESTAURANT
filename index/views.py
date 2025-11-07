# views.py (بروزرسانی شده برای پنل‌های جدید)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from django.http import JsonResponse
import json
import logging

from .models import MenuItem, Category, Order, OrderItem
from .forms import OrderForm

logger = logging.getLogger(__name__)

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

    menu_items_json = json.dumps([{
        'id': item.id,
        'name': item.name,
        'price': int(item.price),
        'image': item.image.url if item.image else '/static/no-image.jpg'
    } for item in menu_items], ensure_ascii=False)

    form = OrderForm()
    cart = request.session.get('cart', [])

    return render(request, 'muno.html', {
        'menu_items': menu_items,
        'categories': categories,
        'form': form,
        'menu_items_json': menu_items_json,
        'cart': cart,
        'csrf_token': request.COOKIES.get('csrftoken', '')
    })


# --- API برای همگام‌سازی سبد خرید ---
@login_required
def sync_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            request.session['cart'] = cart
            request.session.modified = True
            logger.info(f"سبد خرید همگام شد برای کاربر {request.user}: {cart}")
            return JsonResponse({'status': 'ok', 'cart': cart})
        except Exception as e:
            logger.error(f"خطا در sync_cart: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)


# --- ثبت سفارش ---
@login_required
def place_order(request):
    cart = request.session.get('cart', [])
    logger.warning(f"سبد خرید در place_order: {cart}")  # دیباگ
    print("CART IN SESSION:", cart)

    if not cart:
        messages.warning(request, "سبد خرید خالی است.")
        return redirect('index:order_menu')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = Order.objects.create(
                    user=request.user,
                    table_number=form.cleaned_data['table_number'],
                    special_requests=form.cleaned_data['special_requests']
                )

                for item in cart:
                    menu_item = get_object_or_404(MenuItem, id=item['id'])
                    OrderItem.objects.create(
                        order=order,
                        menu_item=menu_item,
                        quantity=item['quantity'],
                        price_at_order=menu_item.price
                    )

                order.calculate_total()
                request.session['cart'] = []
                request.session.modified = True

                messages.success(request, f"سفارش #{order.id} با موفقیت ثبت شد!")
                logger.info(f"سفارش {order.id} توسط {request.user} ثبت شد.")
                return redirect('index:home')

            except Exception as e:
                logger.error(f"خطا در ثبت سفارش: {e}")
                messages.error(request, "خطایی رخ داد. دوباره تلاش کنید.")
    else:
        form = OrderForm()

    return render(request, 'muno.html', {
        'form': form,
        'cart': cart,
        'menu_items': MenuItem.objects.filter(is_available=True),
        'categories': Category.objects.all(),
        'csrf_token': request.COOKIES.get('csrftoken', '')
    })


# --- پنل مدیر ---
@login_required
@user_passes_test(is_manager)
def manage_orders(request):
    return render(request, 'manager_taiid.html')  # فرض بر اینکه فایل پنل مدیریت manager_ers.html هست


# --- API برای دریافت سفارشات مدیر ---
@login_required
@user_passes_test(is_manager)
def get_manager_orders(request):
    orders = Order.objects.all().select_related('user').prefetch_related('items__menu_item')
    orders_data = []
    for order in orders:
        customer_name = f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username
        items = [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'price': int(item.price_at_order),
            'notes': ''  # اگر یادداشتی دارید اضافه کنید
        } for item in order.items.all()]
        
        orders_data.append({
            'id': f"ORD-{order.id:03d}",
            'customer': customer_name,
            'table': order.table_number,
            'items': items,
            'total': int(order.total_price),
            'status': order.status,
            'time': order.created_at.strftime('%H:%M'),
            'urgent': False  # می‌توانید منطق فوری اضافه کنید
        })
    
    return JsonResponse({'orders': orders_data})


# --- API برای تایید سفارش توسط مدیر ---
@login_required
@user_passes_test(is_manager)
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'pending':
        order.status = 'confirmed'
        order.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# --- API برای رد سفارش توسط مدیر ---
@login_required
@user_passes_test(is_manager)
def reject_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return JsonResponse({'status': 'success'})


# --- پنل آشپز ---
@login_required
@user_passes_test(is_chef)
def chef_panel(request):
    return render(request, 'manager_aspazi.html')  # فایل HTML جدید برای آشپز


# --- API برای دریافت سفارشات آشپز ---
@login_required
@user_passes_test(is_chef)
def get_chef_orders(request):
    orders = Order.objects.filter(status__in=['confirmed', 'preparing', 'ready']).select_related('user').prefetch_related('items__menu_item')
    orders_data = []
    for order in orders:
        customer_name = f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username
        items = [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'notes': ''  # اگر یادداشتی دارید اضافه کنید
        } for item in order.items.all()]
        
        orders_data.append({
            'id': f"ORD-{order.id:03d}",
            'customer': customer_name,
            'table': order.table_number,
            'items': items,
            'total': int(order.total_price),
            'status': 'pending' if order.status == 'confirmed' else order.status,
            'time': order.created_at.strftime('%H:%M'),
            'urgent': False  # می‌توانید منطق فوری اضافه کنید
        })
    
    return JsonResponse({'orders': orders_data})


# --- API برای شروع پخت توسط آشپز ---
@login_required
@user_passes_test(is_chef)
def start_cooking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'confirmed':
        order.status = 'preparing'
        order.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# --- API برای اتمام پخت توسط آشپز ---
@login_required
@user_passes_test(is_chef)
def finish_cooking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'preparing':
        order.status = 'ready'
        order.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


# --- پنل گارسون ---
@login_required
@user_passes_test(is_waiter)
def waiter_panel(request):
    today = timezone.now().date()
    delivered_today = Order.objects.filter(
        status='delivered',
        created_at__date=today
    ).aggregate(total=Sum('total_price'))['total'] or 0

    return render(request, 'manager_garson.html', {
        'delivered_today': int(delivered_today)
    })  # فایل HTML جدید برای گارسون


# --- API برای دریافت سفارشات گارسون ---
@login_required
@user_passes_test(is_waiter)
def get_waiter_orders(request):
    orders = Order.objects.filter(status='ready').select_related('user').prefetch_related('items__menu_item')
    orders_data = []
    for order in orders:
        customer_name = f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username
        items = [{
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'notes': ''  # اگر یادداشتی دارید اضافه کنید
        } for item in order.items.all()]
        
        orders_data.append({
            'id': f"ORD-{order.id:03d}",
            'customer': customer_name,
            'table': order.table_number,
            'items': items,
            'total': int(order.total_price),
            'status': order.status,
            'time': order.created_at.strftime('%H:%M'),
            'urgent': False  # می‌توانید منطق فوری اضافه کنید
        })
    
    return JsonResponse({'orders': orders_data})


# --- API برای تحویل سفارش توسط گارسون ---
@login_required
@user_passes_test(is_waiter)
def deliver_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'ready':
        order.status = 'delivered'
        order.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)