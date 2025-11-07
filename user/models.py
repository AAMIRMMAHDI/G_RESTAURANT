# user/models.py
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone
import random
from kavenegar import KavenegarAPI, APIException
from django.conf import settings


class CustomUserManager(UserManager):
    def create_user(self, mobile, password=None, **extra_fields):
        if not mobile:
            raise ValueError('شماره موبایل الزامی است.')

        # username رو با mobile + رندوم پر می‌کنیم تا UNIQUE نباشه مشکل
        extra_fields['username'] = f"{mobile}_{random.randint(1000, 9999)}"

        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'manager')

        return self.create_user(mobile, password, **extra_fields)


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

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    mobile = models.CharField(max_length=15, unique=True, verbose_name='موبایل')
    first_name = models.CharField(max_length=100, verbose_name='نام')
    last_name = models.CharField(max_length=100, verbose_name='نام خانوادگی')
    national_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='کد ملی')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    hire_date = models.DateField(null=True, blank=True, verbose_name='تاریخ استخدام')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer', verbose_name='نقش')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='وضعیت')
    address = models.TextField(blank=True, verbose_name='آدرس')

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"{self.mobile}_{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mobile})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    class Meta:
        db_table = 'user_user'
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'


# مدل OTPCode — کامل و با پیامک واقعی
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
        
        OTPCode.objects.filter(mobile=mobile).delete()
        otp = OTPCode.objects.create(mobile=mobile, code=code, expires_at=expires_at)

        try:
            api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
            params = {
                'sender': settings.KAVENEGAR_SENDER,
                'receptor': mobile,
                'message': f'کد ورود شما: {code}\nرستوران گل‌سرخ'
            }
            response = api.sms_send(params)
            print(f"پیامک ارسال شد به {mobile}: {code}")
        except APIException as e:
            print(f"خطای کاوه‌نگار: {e}")
        except Exception as e:
            print(f"خطای غیرمنتظره: {e}")

        return otp

    def __str__(self):
        return f"OTP {self.code} برای {self.mobile}"