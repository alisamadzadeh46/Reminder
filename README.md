 Reminder — سامانه مدیریت جلسات و پیگیری وظایف سازمانی (Django)

این پروژه یک سامانه‌ی مدیریت جلسات سازمانی است که امکان برنامه‌ریزی جلسه، دعوت از افراد، ثبت صورتجلسه، تعریف وظایف در جلسه و پیگیری وضعیت آن‌ها را فراهم می‌کند. همچنین سیستم اعلان و یادآور خودکار با Celery/Beat برای یادآوری جلسه و سررسید وظایف در نظر گرفته شده است.

---

## امکانات اصلی

### مدیریت جلسه
- ایجاد و مدیریت جلسه (عنوان، زمان، مکان/لینک، توضیحات)
- تعیین نقش‌ها در جلسه:
  - دبیر جلسه (Secretary)
  - پیگیری‌کننده (Follow-up Owner)
  - تأییدکننده (Approver)
- مدیریت دعوت‌نامه‌ها و وضعیت RSVP شرکت‌کنندگان

### صورتجلسه و پیوست‌ها
- ثبت صورتجلسه (Minutes)
- امکان پیوست فایل به جلسه و وظیفه (Attachment)

### مدیریت وظایف
- تعریف وظیفه (در قالب جلسه یا مستقل)
- تعیین مسئول (Assignee)، پیگیری‌کننده (Follower)، تأییدکننده (Approver)
- تغییر وضعیت وظیفه با سطح دسترسی (Workflow پایه)
- صفحه «وظایف من» با فیلتر، جستجو، pagination و اکشن‌های سریع

### اعلان و یادآور خودکار
- اعلان‌های داخل سیستم (Notifications)
- یادآور خودکار با Celery + Celery Beat (قابل توسعه برای ایمیل/SMS)

### پنل مدیریت
- پنل Admin داخلی Django برای مدیریت داده‌ها

---

## تکنولوژی‌ها
- Backend: Django
- DB: Sql
- Background Jobs: Celery + Celery Beat
- Frontend: Bootstrap 5 RTL + Dark/Light Switch
- Storage: فایل‌های Media (قابل توسعه به S3/MinIO)

---

## پیش‌نیازها
- Python 3.10+ (ترجیحاً 3.11)
- Redis (برای Celery Broker)
- pip / venv

---

## نصب و اجرا (Local)

### 1) کلون پروژه
```bash
git clone https://github.com/alisamadzadeh46/Reminder.git
cd Reminder
```
2) ساخت محیط مجازی  
```bash                                                  
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

```bash   
3)  Migrationا
python manage.py makemigrations
python manage.py migrate
```

```bash   
4)create super user
python manage.py createsuperuser
```
5 ) run project
```bash                                                                                                                                                                                                       
python manage.py runserver
```
پروژه در آدرس زیر در دسترس است:
داشبورد: http://127.0.0.1:8000/
ورود: http://127.0.0.1:8000/login/
ثبت‌نام: http://127.0.0.1:8000/register/
ادمین: http://127.0.0.1:8000/admin/



اجرای Celery و Celery Beat (یادآورها)
1) اجرای Redis
اگر Redis روی سیستم نصب است اجراش کن. یا با Docker:



docker run -p 6379:6379 redis

 اجرای worker 
 در ترمینال جدا 
celery -A reminder worker -l info



3) اجرای Beat
در ترمینال جدا:
Copy code
Bash
celery -A reminder beat -l info
اگر از django-celery-beat استفاده می‌کنی حتماً migrateها انجام شده باشند:
Copy code
Bash
python manage.py migrate django_celery_beat
استفاده از سیستم (راهنمای سریع)
وارد سیستم شوید (یا ثبت‌نام کنید).
از منوی «جلسات من» جلسه ایجاد کنید و نقش‌ها را تعیین کنید.
مدعوها را اضافه کنید و RSVP را بررسی کنید.
از داخل جلسه، وظایف مرتبط ایجاد کنید و مسئول/پیگیری‌کننده/تأییدکننده را مشخص کنید.
از صفحه «وظایف من» وضعیت وظایف را پیگیری و تغییر دهید.
اعلان‌ها در بخش Notifications نمایش داده می‌شوند و یادآورها با Celery قابل ارسال هستند.
