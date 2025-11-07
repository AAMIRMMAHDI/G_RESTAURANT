# user/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, OTPCode
from .forms import MobileForm, OTPForm, UserRegistrationForm, UserManagementForm


def is_manager(user):
    return user.role == 'manager'


def login_view(request):
    step = request.session.get('login_step', 1)
    mobile = request.session.get('mobile')

    if request.method == 'POST':
        if step == 1:
            form = MobileForm(request.POST)
            if form.is_valid():
                mobile = form.cleaned_data['mobile']
                try:
                    OTPCode.generate_otp(mobile)
                    messages.success(request, f'کد تأیید به {mobile} ارسال شد.')
                except Exception as e:
                    messages.error(request, 'خطا در ارسال پیامک. لطفاً دوباره تلاش کنید.')
                    return render(request, 'login.html', {'form': form, 'step': step})
                
                request.session['mobile'] = mobile
                request.session['login_step'] = 2
                return redirect('user:login')
                
        elif step == 2:
            form = OTPForm(request.POST)
            if form.is_valid():
                code = form.cleaned_data['code']
                otp = OTPCode.objects.filter(mobile=mobile, code=code).first()
                if otp and otp.is_valid():
                    user, created = User.objects.get_or_create(
                        mobile=mobile,
                        defaults={'username': mobile}  # مهم!
                    )
                    if created or not user.first_name:
                        request.session['login_step'] = 3
                        return redirect('user:login')
                    login(request, user)
                    _cleanup_session(request)
                    return redirect('index:home')
                else:
                    messages.error(request, 'کد نامعتبر یا منقضی شده است.')
        elif step == 3:
            user = User.objects.get(mobile=mobile)
            form = UserRegistrationForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                login(request, user)
                _cleanup_session(request)
                return redirect('index:home')

    # GET request
    if step == 1:
        form = MobileForm()
    elif step == 2:
        form = OTPForm()
    elif step == 3:
        user = User.objects.get(mobile=mobile)
        form = UserRegistrationForm(instance=user)

    return render(request, 'login.html', {'form': form, 'step': step})


def _cleanup_session(request):
    for key in ['login_step', 'mobile']:
        request.session.pop(key, None)


@login_required
@user_passes_test(is_manager)
def manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    form = UserManagementForm()

    if request.method == 'POST':
        if 'delete' in request.POST:
            user_id = request.POST.get('user_id')
            User.objects.filter(id=user_id).delete()
            messages.success(request, 'کاربر حذف شد.')
        else:
            form = UserManagementForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.username = user.mobile  # مهم!
                user.save()
                messages.success(request, 'کاربر ذخیره شد.')

    return render(request, 'manager_karbaran.html', {
        'users': users,
        'form': form
    })


def logout_view(request):
    logout(request)
    return redirect('index:home')