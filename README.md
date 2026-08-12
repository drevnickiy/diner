# 🍱 Carry.ck.ua Business Lunch Scraper & Notifier

Міні-проєкт для автоматичного парсингу бізнес-ланчів по днях тижня з ресторанів:
- **Chacha che** (`https://carry.ck.ua/chacha`)
- **Eric / Bierstube** (`https://carry.ck.ua/erik`)

Та надсилання красивого звіту на пошту **`drevnickiy@gmail.com`**.

---

## 📁 Структура проєкту

```text
diner/
├── parser.py          # Парсер сторінок Tilda (дублювання страв, ціни, дні тижня)
├── formatter.py       # Генерація адаптивного HTML та Plain Text листів
├── mailer.py          # Відправка пошти через SMTP (з прев'ю-режимом)
├── main.py            # Точка входу (CLI інтерфейс)
├── requirements.txt   # Залежності (requests, beautifulsoup4, python-dotenv)
├── .env               # Конфігурація пошти та SMTP
└── README.md          # Інструкція
```

---

## 🚀 Швидкий старт

### 1. Установка залежностей
```bash
pip install -r requirements.txt
```

### 2. Запуск у режимі попереднього перегляду (Preview)
Для генерації та перегляду локального HTML-файлу без відправки пошти:
```bash
python main.py --preview
```
Файл `email_preview.html` буде збережено в папочці проєкту.

### 3. Відправка листа на пошту `drevnickiy@gmail.com`
Для відправки реального листа налаштуйте SMTP-параметри в файлі `.env`:

```env
RECIPIENT_EMAIL=drevnickiy@gmail.com

SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_gmail_app_password
SENDER_EMAIL=your_email@gmail.com
```

> **Як отримати Gmail App Password:**
> 1. Перейдіть у свій Google Акаунт -> **Безпека** -> **Двоетапна перевірка**.
> 2. Унизу сторінки виберіть **Паролі додатків (App Passwords)**.
> 3. Введіть назву (наприклад, `Diner Lunch`) та згенеруйте 16-значний пароль.
> 4. Вставте отриманий пароль у поле `SMTP_PASS` в файлі `.env`.

Після налаштування запустіть:
```bash
python main.py
```

---

## ⚙️ Опції CLI

- **За замовчуванням (весь тиждень з підсвічуванням поточного дня):**
  ```bash
  python main.py
  ```
- **Примусова відправка на інший email:**
  ```bash
  python main.py --recipient another@example.com
  ```
- **Вибір конкретного дня (0=Понеділок, 1=Вівторок, 2=Середа, 3=Четвер, 4=П'ятниця):**
  ```bash
  python main.py --day 2
  ```

---

## ⏰ Автоматизація через Cron (щодня о 10:00 з понеділка по п'ятницю)

Відкрийте crontab:
```bash
crontab -e
```

Додайте рядок:
```cron
0 10 * * 1-5 cd /Users/bogdansunday/Desktop/diner && /usr/bin/python3 main.py >> /Users/bogdansunday/Desktop/diner/cron.log 2>&1
```

---

## 🌐 Безкоштовний хостинг та власний домен

### Варіант 1: GitHub Pages (Рекомендовано — 100% безкоштовно)
1. Створіть репозиторій на GitHub і запуште код:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/diner.git
   git push -u origin main
   ```
2. У налаштуваннях репозиторію **Settings -> Secrets and variables -> Actions** додайте секрети `SMTP_USER` та `SMTP_PASS`.
3. GitHub Actions автоматично щодня о 10:00:
   - Розпарсить меню
   - Відправить лист на `drevnickiy@gmail.com`
   - Оновить безкоштовний сайт: `https://YOUR_USERNAME.github.io/diner/`

### Варіант 2: Vercel (Безкоштовний домен `*.vercel.app`)
1. Встановіть Vercel CLI або завантажте репозиторій на GitHub.
2. Підключіть репозиторій у [Vercel Dashboard](https://vercel.com).
3. Отримайте безкоштовний домен вигляду: `https://diner-lunches.vercel.app`

