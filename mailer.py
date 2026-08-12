import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def send_email(html_content, text_content, subject="🍱 Меню бізнес-ланчів на тиждень (Carry.ck.ua)", recipient=None):
    """
    Sends HTML + Text email using SMTP settings from .env file or environment variables.
    If credentials are not set, saves preview HTML and returns False.
    """
    if not recipient:
        recipient = os.getenv('RECIPIENT_EMAIL', 'drevnickiy@gmail.com')

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '465'))
    smtp_user = os.getenv('SMTP_USER', '').strip()
    smtp_pass = os.getenv('SMTP_PASS', '').strip()
    sender = os.getenv('SENDER_EMAIL', '').strip() or smtp_user or 'noreply@diner.local'

    if not smtp_user or not smtp_pass:
        print("\n[Preview Mode] SMTP_USER and SMTP_PASS are not configured in .env file.")
        print(f"Recipient configured as: {recipient}")
        preview_file = 'email_preview.html'
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTML preview saved to file://{os.path.abspath(preview_file)}")
        print("💡 To enable real email sending, set SMTP_USER and SMTP_PASS in .env")
        return False, preview_file

    # Build MIME message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"Carry Lunch Notifier <{sender}>"
    msg['To'] = recipient

    part_text = MIMEText(text_content, 'plain', 'utf-8')
    part_html = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part_text)
    msg.attach(part_html)

    try:
        print(f"Connecting to SMTP server {smtp_host}:{smtp_port}...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(sender, [recipient], msg.as_string())
        server.quit()
        print(f"🚀 Email successfully sent to {recipient}!")
        return True, recipient
    except Exception as e:
        print(f"[Error] Failed to send email: {e}")
        # Save preview fallback
        preview_file = 'email_preview.html'
        with open(preview_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Saved email preview to {preview_file}")
        return False, str(e)
