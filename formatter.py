from datetime import datetime

DAY_NAMES = {
    0: 'Понеділок',
    1: 'Вівторок',
    2: 'Середа',
    3: 'Четвер',
    4: 'П\'ятниця',
    5: 'Субота',
    6: 'Неділя'
}

def generate_html_report(restaurants_data, target_day=None):
    """
    Generates a responsive HTML email report for business lunches.
    target_day: integer 0..6 (0=Monday..6=Sunday). If None, defaults to current day of week.
    """
    if target_day is None:
        target_day = datetime.now().weekday()

    current_day_name = DAY_NAMES.get(target_day, 'Сьогодні')
    today_str = datetime.now().strftime('%d.%m.%Y')

    # Build restaurant sections
    rest_sections_html = ""

    for rest in restaurants_data:
        rest_name = rest['name']
        rest_url = rest['url']
        rest_icon = rest.get('icon', '🍽️')
        lunches = rest.get('lunches', {})

        days_html = ""
        for day_code in range(5):
            day_name = DAY_NAMES[day_code]
            is_today = (day_code == target_day)
            lunch = lunches.get(day_code)

            card_border = "border: 2px solid #e11d48;" if is_today else "border: 1px solid #e2e8f0;"
            card_bg = "#fff1f2" if is_today else "#ffffff"
            today_badge = '<span style="background: #e11d48; color: #ffffff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; margin-left: 8px; text-transform: uppercase;">Сьогодні</span>' if is_today else ''

            if lunch:
                price_badge = f'<span style="background: #0f172a; color: #ffffff; font-size: 13px; font-weight: 700; padding: 4px 10px; border-radius: 6px; float: right;">{lunch["price"]}</span>'
                dishes_list = "".join([f'<li style="margin-bottom: 6px; color: #334155; line-height: 1.4;">• {dish}</li>' for dish in lunch['dishes']])
                
                days_html += f"""
                <div style="background-color: {card_bg}; {card_border} border-radius: 10px; padding: 16px; margin-bottom: 14px;">
                    <div style="margin-bottom: 10px;">
                        {price_badge}
                        <strong style="font-size: 16px; color: #0f172a;">{day_name}</strong>
                        {today_badge}
                    </div>
                    <ul style="margin: 0; padding-left: 4px; list-style: none; font-size: 14px;">
                        {dishes_list}
                    </ul>
                </div>
                """
            else:
                days_html += f"""
                <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 10px; padding: 12px 16px; margin-bottom: 14px; color: #94a3b8;">
                    <strong>{day_name}</strong> {today_badge} — <em>Меню не вказано</em>
                </div>
                """

        rest_sections_html += f"""
        <div style="flex: 1 1 460px; min-width: 320px; background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; margin-bottom: 24px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 16px;">
                <h2 style="margin: 0; font-size: 20px; color: #0f172a;">{rest_icon} {rest_name}</h2>
                <a href="{rest_url}" target="_blank" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 8px 14px; border-radius: 8px; font-weight: 600; font-size: 13px;">Замовити</a>
            </div>
            {days_html}
        </div>
        """

    html_email = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Бізнес-ланчі в Черкасах</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 24px 12px;">
    <div style="max-width: 1060px; margin: 0 auto;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 28px 24px; border-radius: 16px 16px 14px 14px; text-align: center; margin-bottom: 24px; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.3);">
            <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; display: inline-block; margin-bottom: 8px;">
                📅 {today_str} • {current_day_name}
            </span>
            <h1 style="margin: 6px 0 0 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                🍱 Меню бізнес-ланчів на тиждень
            </h1>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #94a3b8;">
                Chacha che & Eric Bierstube (Carry.ck.ua)
            </p>
        </div>

        <!-- Restaurant Content 2-Column Grid -->
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;">
            {rest_sections_html}
        </div>

        <!-- Footer -->
        <div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 24px; padding: 12px;">
            Сформовано автоматично • <a href="https://carry.ck.ua" style="color: #2563eb; text-decoration: none;">Carry.ck.ua</a>
        </div>
    </div>
</body>
</html>"""
    return html_email


def generate_text_report(restaurants_data, target_day=None):
    """
    Generates a clean plain-text version of the lunch report.
    """
    if target_day is None:
        target_day = datetime.now().weekday()

    current_day_name = DAY_NAMES.get(target_day, 'Сьогодні')
    today_str = datetime.now().strftime('%d.%m.%Y')

    lines = []
    lines.append(f"==========================================")
    lines.append(f"🍱 МЕНЮ БІЗНЕС-ЛАНЧІВ ({today_str} • {current_day_name})")
    lines.append(f"==========================================\n")

    for rest in restaurants_data:
        lines.append(f"=== {rest['name'].upper()} ===")
        lines.append(f"Ссылка: {rest['url']}\n")

        lunches = rest.get('lunches', {})
        for day_code in range(5):
            day_name = DAY_NAMES[day_code]
            is_today = (day_code == target_day)
            prefix = "👉 [СЬОГОДНІ] " if is_today else "   "

            lunch = lunches.get(day_code)
            if lunch:
                lines.append(f"{prefix}{day_name} ({lunch['price']}):")
                for dish in lunch['dishes']:
                    lines.append(f"      • {dish}")
                lines.append("")
            else:
                lines.append(f"{prefix}{day_name}: Меню не вказано\n")

        lines.append("-" * 42 + "\n")

    return "\n".join(lines)
