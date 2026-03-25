# Tarixiy Matn Tarjimoni (Django Version)

Bu loyiha eski yozuvlarni rasm orqali o'qib, zamonaviy o'zbek tiliga tarjima qilib beruvchi veb-ilovadir.

## Lokal ishga tushirish

1. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. `.env` fayliga `GEMINI_API_KEY` ni yozing.

3. Bazani tayyorlang:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Lokal serverni ishga tushiring:
   ```bash
   python manage.py runserver
   ```

## Serverda (Production) ishga tushirish

Serverda odatda `gunicorn` ishlatiladi:

1. Statik fayllarni yig'ing:
   ```bash
   python manage.py collectstatic
   ```

2. Gunicorn bilan ishga tushiring:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```

**Eslatma:** Serverda `DEBUG = False` (settings.py da) qilishni va `ALLOWED_HOSTS` ni to'ldirishni unutmang.
