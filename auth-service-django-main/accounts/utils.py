import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def generate_code():
    """توليد رمز عشوائي مكون من 6 أرقام"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(user):
    """إرسال رمز التحقق إلى البريد الإلكتروني"""
    code = generate_code()
    user.verification_code = code
    user.verification_code_created_at = timezone.now()
    user.save()
    
    subject = "🔐 رمز التحقق - Smart CV Matcher"
    message = f"""
    مرحباً {user.prenom} {user.nom},
    
    رمز التحقق الخاص بحسابك هو: {code}
    
    هذا الرمز صالح لمدة 15 دقيقة فقط.
    
    إذا لم تطلب هذا الرمز، يرجى تجاهل هذا البريد.
    
    تحيات فريق Smart CV Matcher
    """
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def send_reset_password_email(user):
    """إرسال رمز إعادة تعيين كلمة المرور"""
    code = generate_code()
    user.reset_password_code = code
    user.reset_password_code_created_at = timezone.now()
    user.save()
    
    subject = "🔑 إعادة تعيين كلمة المرور - Smart CV Matcher"
    message = f"""
    مرحباً {user.prenom} {user.nom},
    
    لقد تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بك.
    
    رمز إعادة التعيين هو: {code}
    
    هذا الرمز صالح لمدة 15 دقيقة فقط.
    
    إذا لم تطلب هذا، يرجى تجاهل هذا البريد.
    
    تحيات فريق Smart CV Matcher
    """
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def is_code_valid(created_at):
    """التحقق من صلاحية الرمز (15 دقيقة)"""
    if not created_at:
        return False
    return timezone.now() <= created_at + timedelta(minutes=15)