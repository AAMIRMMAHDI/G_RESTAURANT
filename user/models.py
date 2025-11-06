# models.py
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
import random
from kavenegar import KavenegarAPI, APIException
from django.conf import settings


class CustomUserManager(UserManager):
    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'manager')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('سوپریوزر باید is_staff=True داشته باشد.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('سوپریوزر باید is_superuser=True داشته باشد.')

        extra_fields['username'] = mobile
        return self.create_user(mobile, password, **extra_fields)

    def create_user(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        if not mobile:
            raise ValueError('شماره موبایل الزامی است.')

        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'مشتری'),
        ('manager', 'مدیر'),
        ('chef', 'آشپز'),
        ('waiter', 'گارسون'),
        ('cashier', 'صندوقدار'),
        ('cleaner', 'نظافتچی'),
    )
    STATUS_CHOICES = (
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('suspended', 'تعلیق'),
    )

    mobile = models.CharField(max_length=15, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_code = models.CharField(max_length=10, blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    address = models.TextField(blank=True)

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mobile})"


class OTPCode(models.Model):
    mobile = models.CharField(max_length=15)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return timezone.now() < self.expires_at

    @staticmethod
    def generate_otp(mobile):
        code = str(random.randint(1000, 9999))
        expires_at = timezone.now() + timezone.timedelta(minutes=5)
        
        # حذف کدهای قبلی
        OTPCode.objects.filter(mobile=mobile).delete()
        
        # ایجاد OTP جدید
        otp = OTPCode.objects.create(mobile=mobile, code=code, expires_at=expires_at)

        # ارسال پیامک واقعی با کاوه‌نگار
        try:
            api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
            params = {
                'sender': settings.KAVENEGAR_SENDER,
                'receptor': mobile,
                'message': f'کد تأییدی شما: {code}'
            }
            response = api.sms_send(params)
            print(f"پیامک با موفقیت ارسال شد به {mobile}: {code}")
        except APIException as e:
            print(f"خطا در ارسال پیامک: {e}")
            # می‌تونید اینجا لاگ کنید یا خطا برگردونید
        except Exception as e:
            print(f"خطای غیرمنتظره: {e}")

        return otp