📩 Reminder

Asynchronous SMS Reminder System built with Django, Celery & Redis

A professional, scalable SMS sending and management system featuring user dashboards, admin analytics, background task processing, and retry mechanisms

✨ Features

Asynchronous SMS sending using Celery

Redis-backed task queue

Real & Fake SMS Providers support

User-specific SMS dashboard

Admin dashboard with analytics charts

Message status tracking (Queued / Sent / Failed)

Automatic retry on failure

Clean, classic, and professional UI

Pagination & status badges

Easily extendable architecture

🧱 Tech Stack

Python 3.10+

Django

Celery

Redis

SQLite / PostgreSQL

Bootstrap 5

Chart.js

📸 Screenshots

⚙️ Installation & Setup
1️⃣ Clone the Repository
```bash
git clone https://github.com/alisamadzadeh46/Reminder.git
cd Reminder
```
2️⃣ Create Virtual Environment
```bashe
python -m venv .venv
```
Activate it:

Windows:
```bash
.venv\Scripts\activate
```

Linux / macOS :
```bash
source .venv/bin/activate
```


3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

Or manually:
```
pip install django celery redis requests
```

4️⃣ Database Setup
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5️⃣ Run Django Server
```
python manage.py runserver
```

Access the app at:
```
http://127.0.0.1:8000
```

🚀 Running Redis
🔹 Windows

Download Redis from:
https://github.com/microsoftarchive/redis/releases

Install and run Redis

Default port: 6379

🔹 Linux / macOS
```
sudo apt install redis
redis-server
```

or
```
brew install redis
brew services start redis
```

🔁 Running Celery
Start Celery Worker

Open a new terminal:
```
celery -A config worker -l info --pool=solo
```

⚠️ Windows users: --pool=solo is required.
```
(Optional) Run Celery Beat
celery -A config beat -l info
```

⚙️ Celery Configuration (Example)

📁 config/settings.py
```
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"
```


🧪 Fake Provider Mode

If SMS provider credentials are missing or invalid, the system automatically falls back to FakeProvider for safe testing without failures.

🔐 Notes

Redis must be running before Celery

Celery worker should always be active

On Windows, Celery requires --pool=solo

For production, use Docker or Supervisor

🗺️ Roadmap

 Advanced reporting

 Date filtering

 Real-time updates (WebSocket)

 Multi-provider support

 User-configurable SMS templates

👨‍💻 Author

Built with ❤️ using Django & Celery
Feel free to contribute or suggest improvements.

⭐ If you like this project

Don’t forget to star ⭐ the repository
