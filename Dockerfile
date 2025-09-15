<<<<<<< HEAD
# بیس ایمیج پایتون
FROM python:3.11-slim

# فولدر کاری
WORKDIR /app

# نصب پکیج‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل کد
COPY . .

# اجرای Flask با gunicorn روی پورت 8080
CMD ["gunicorn", "-b", ":8080", "app:app"]
=======
# بیس ایمیج پایتون
FROM python:3.11-slim

# فولدر کاری
WORKDIR /app

# نصب پکیج‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کل کد
COPY . .

# اجرای Flask با gunicorn روی پورت 8080
CMD ["gunicorn", "-b", ":8080", "app:app"]
>>>>>>> cfcae93ea699e8f6c6a3c5476818ffa4ecd426ce
