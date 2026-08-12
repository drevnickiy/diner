#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv

from parser import fetch_all_lunches, DAY_MAP
from formatter import generate_html_report, generate_text_report
from mailer import send_email

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Parse business lunches from carry.ck.ua (Chacha & Erik) and send via email.")
    parser.add_argument('--today', action='store_true', help="Highlight and focus on today's lunch")
    parser.add_argument('--day', type=int, choices=[0, 1, 2, 3, 4], help="Specify day index (0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday)")
    parser.add_argument('--recipient', type=str, help="Recipient email address (default: drevnickiy@gmail.com)")
    parser.add_argument('--preview', action='store_true', help="Force preview mode (save HTML file without sending email)")
    
    args = parser.parse_args()

    target_day = args.day
    if target_day is None:
        target_day = datetime.now().weekday()
        # If weekend (Sat/Sun), default to Monday
        if target_day > 4:
            target_day = 0

    day_name = DAY_MAP.get(target_day, 'Сьогодні')

    print(f"🔄 Fetching business lunches from carry.ck.ua (Chacha & Erik)...")
    restaurants_data = fetch_all_lunches()

    print(f"🎨 Generating email report for day: {day_name}...")
    html_content = generate_html_report(restaurants_data, target_day=target_day)
    text_content = generate_text_report(restaurants_data, target_day=target_day)

    # Save local preview and public index.html for web hosting (GitHub Pages / Vercel)
    import os
    os.makedirs('public', exist_ok=True)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    with open('email_preview.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"📄 Generated web page at public/index.html and email_preview.html")

    if args.preview:
        print("ℹ️ Preview mode requested. Skipping email dispatch.")
        print("\n--- TEXT PREVIEW ---")
        print(text_content)
        return

    recipient = args.recipient or None
    print(f"📧 Sending report via email...")
    success, info = send_email(
        html_content=html_content,
        text_content=text_content,
        subject=f"🍱 Бізнес-ланчі {day_name} ({datetime.now().strftime('%d.%m.%Y')}) - Chacha & Erik",
        recipient=recipient
    )

    if success:
        print(f"✨ Finished! Email sent to {info}.")
    else:
        print(f"📌 Finished! HTML report saved to {preview_path}.")

if __name__ == '__main__':
    main()
