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
        <div style="flex: 1 1 340px; min-width: 300px; background: #ffffff; border-radius: 14px; border: 1px solid #e2e8f0; margin-bottom: 24px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); box-sizing: border-box;">
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
    <!-- Auth Container -->
    <div id="auth-container" style="max-width: 400px; margin: 60px auto; background: #ffffff; padding: 32px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); display: none;">
        <h2 style="text-align: center; color: #0f172a; margin-top: 0;">Вхід у систему</h2>
        <form id="auth-form" action="javascript:void(0);" style="display: flex; flex-direction: column; gap: 16px;">
            <div>
                <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">Логін</label>
                <input type="text" id="auth-username" required style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">Пароль</label>
                <input type="password" id="auth-password" required style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box;">
            </div>
            <div>
                <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">Автомобіль (опціонально при реєстрації)</label>
                <input type="text" id="auth-car" placeholder="Наприклад: Skoda Fabia" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; box-sizing: border-box;">
            </div>
            <div id="auth-error" style="color: #ef4444; font-size: 13px; font-weight: 600; text-align: center; display: none;"></div>
            <button type="submit" id="auth-login-btn" onclick="handleAuth(event, 'login')" style="background: #2563eb; color: #fff; border: none; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 15px;">Увійти</button>
            <button type="button" id="auth-register-btn" onclick="handleAuth(event, 'register')" style="background: #ffffff; color: #2563eb; border: 2px solid #2563eb; padding: 12px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 15px;">Зареєструватися</button>
        </form>
    </div>

    <!-- Main App Container -->
    <div id="main-app" style="max-width: 1240px; margin: 0 auto; display: none;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 28px 24px; border-radius: 16px 16px 14px 14px; text-align: center; margin-bottom: 24px; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; display: inline-block;">
                    📅 {today_str} • {current_day_name}
                </span>
                <button onclick="handleLogout()" style="background: rgba(239, 68, 68, 0.8); color: white; border: none; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; transition: background 0.2s;">
                    Вийти 🚪
                </button>
            </div>
            <h1 style="margin: 6px 0 0 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">
                🍱 Меню бізнес-ланчів на тиждень
            </h1>
            <p style="margin: 8px 0 0 0; font-size: 14px; color: #94a3b8;">
                Chacha che, Eric Bierstube & Escobar
            </p>
        </div>

        <!-- Canvas Fireworks Container -->
        <canvas id="fireworks-canvas" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9999;"></canvas>

        <!-- Voting Widget -->
        <div id="voting-widget" style="background: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; padding: 24px; margin-bottom: 24px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05); box-sizing: border-box;">
            
            <!-- Header & Action Buttons -->
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; border-bottom: 2px solid #f1f5f9; padding-bottom: 16px; margin-bottom: 20px;">
                <div>
                    <h2 style="margin: 0; font-size: 22px; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 8px;">
                        🚗 Голосування: Їдемо чи Не їдемо?
                    </h2>
                    <p style="margin: 4px 0 0 0; font-size: 13px; color: #64748b;">
                        Обирайте заклад, вводьте ім'я та голосуйте! ⏰ <strong>Час голосування: 11:30 – 12:00 (Київ)</strong>
                    </p>
                    <div id="voting-time-status" style="margin-top: 8px; display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;">
                        <!-- Dynamic status inserted by JS -->
                    </div>
                </div>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button id="fireworks-btn" onclick="launchFireworks()" style="background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); color: #ffffff; border: none; padding: 8px 14px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(236,72,153,0.3); transition: transform 0.1s;">
                        🎆 Феєрверк!
                    </button>
                    <button id="copy-tg-btn" onclick="copyVotesForTelegram()" style="background: #0284c7; color: #ffffff; border: none; padding: 8px 14px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s;">
                        📋 Скопіювати для Telegram
                    </button>
                </div>
            </div>

            <!-- Winning Restaurant Banner -->
            <div id="winner-banner" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">🏆</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; color: #b45309; text-transform: uppercase; letter-spacing: 1px;">
                            Лідер голосування сьогодні:
                        </div>
                        <div id="winner-title" style="font-size: 18px; font-weight: 800; color: #78350f;">
                            Очікування перших голосів...
                        </div>
                    </div>
                </div>
                <div id="restaurant-breakdown" style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <!-- Restaurant tally pills -->
                </div>
            </div>

            <!-- Driver / Car Selection Banner -->
            <div id="driver-banner" style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 2px solid #3b82f6; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 28px;">🚘</span>
                    <div>
                        <div style="font-size: 11px; font-weight: 800; color: #1e40af; text-transform: uppercase; letter-spacing: 1px;">
                            Чия машина їде (вибірка серед тих, хто проголосував "Їдемо"):
                        </div>
                        <div id="driver-title" style="font-size: 16px; font-weight: 800; color: #1e3a8a;">
                            Ще не обрано водія
                        </div>
                    </div>
                </div>
                <div>
                    <button id="pick-driver-btn" onclick="pickRandomDriver(true)" style="background: #2563eb; color: #ffffff; border: none; padding: 8px 14px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(37,99,235,0.3); transition: transform 0.1s;">
                        🎲 Обрати чия машина їде
                    </button>
                </div>
            </div>

            <!-- Main Voting Content Grid -->
            <div style="display: flex; flex-wrap: wrap; gap: 24px; align-items: flex-start;">
                
                <!-- Form Section -->
                <div style="flex: 1 1 320px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px;">
                    <form id="vote-form" action="javascript:void(0);" onsubmit="handleVoteSubmit(event); return false;" style="display: flex; flex-direction: column; gap: 14px;">
                        
                        <!-- Name input removed, inferred from session -->

                        <div>
                            <label for="voter-role-select" style="display: block; font-size: 13px; font-weight: 700; color: #9f1239; margin-bottom: 6px;">
                                🕵️ Ваша масть / роль у кримінальному світі <span style="color: #ef4444;">*</span>
                            </label>
                            <select id="voter-role-select" required style="width: 100%; padding: 10px 12px; border: 2px solid #f43f5e; border-radius: 8px; font-size: 14px; outline: none; background: #fff1f2; color: #0f172a; cursor: pointer; font-weight: 700;">
                                <option value="Вор в законі">👑 Вор в законі</option>
                                <option value="Бродяга">🗡️ Бродяга (Смотрящий)</option>
                                <option value="Блатной">🕶️ Блатной / Авторитет</option>
                                <option value="Пацан">🧢 Правильний пацан</option>
                                <option value="Мужик">🛠️ Мужик (Роботяга)</option>
                                <option value="Фраєр">🎩 Фраєр (Без права голосу)</option>
                                <option value="Барига">💰 Барига (Без права голосу)</option>
                                <option value="Чорт">🃏 Чорт / Шістка (Без права голосу)</option>
                                <option value="Шерсть">🐺 Шерсть (Без права голосу)</option>
                                <option value="Опущений">🧹 Опущений (Без права голосу)</option>
                            </select>
                        </div>

                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 8px;">
                                🎯 Ваш вибір <span style="color: #ef4444;">*</span>
                            </label>
                            <div style="display: flex; gap: 10px;">
                                <label style="flex: 1; border: 2px solid #10b981; background: #ecfdf5; border-radius: 10px; padding: 12px 10px; text-align: center; cursor: pointer; transition: all 0.2s;">
                                    <input type="radio" name="vote-choice" value="going" checked style="margin-right: 4px; accent-color: #059669;">
                                    <strong style="color: #065f46; font-size: 14px;">🚗 Їдемо</strong>
                                </label>
                                <label style="flex: 1; border: 2px solid #f43f5e; background: #fff1f2; border-radius: 10px; padding: 12px 10px; text-align: center; cursor: pointer; transition: all 0.2s;">
                                    <input type="radio" name="vote-choice" value="not_going" style="margin-right: 4px; accent-color: #e11d48;">
                                    <strong style="color: #9f1239; font-size: 14px;">🏠 Не їдемо</strong>
                                </label>
                            </div>
                        </div>

                        <div>
                            <label for="voter-restaurant-select" style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">
                                🍽️ Оберіть заклад (куди їдемо):
                            </label>
                            <select id="voter-restaurant-select" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; background: #ffffff; color: #0f172a; cursor: pointer;">
                                <option value="Chacha che (Чача)">🍷 Chacha che (Чача)</option>
                                <option value="Eric / Bierstube (Ерік)">🍺 Eric / Bierstube (Ерік)</option>
                                <option value="Escobar (Ескобар)">🌮 Escobar (Ескобар)</option>
                                <option value="Будь-яке / Без різниці">🤷 Будь-яке / Без різниці</option>
                            </select>
                        </div>

                        <div>
                            <label for="voter-car-select" style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">
                                🚘 Ваше авто (BMW, Audi, Mazda, VW):
                            </label>
                            <select id="voter-car-select" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; background: #ffffff; color: #0f172a; cursor: pointer;">
                                <option value="BMW">🏎️ BMW</option>
                                <option value="Audi">🚔 Audi</option>
                                <option value="Mazda">🚗 Mazda</option>
                                <option value="VW">🚘 VW</option>
                                <option value="Без авто">🚶 Без авто / Пішки</option>
                            </select>
                        </div>

                        <div>
                            <label for="voter-note-input" style="display: block; font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 6px;">
                                💬 Примітка (необов'язково)
                            </label>
                            <input type="text" id="voter-note-input" placeholder="напр. на 13:15 / з колегою" style="width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; box-sizing: border-box;">
                        </div>

                        <button type="submit" id="submit-vote-btn" style="background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%); color: #ffffff; border: none; padding: 12px; border-radius: 8px; font-size: 15px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 12px rgba(37,99,235,0.25); transition: transform 0.1s;">
                            🗳️ Проголосувати / Оновити
                        </button>
                    </form>
                </div>

                <!-- Dashboard Section -->
                <div style="flex: 1 1 380px; display: flex; flex-direction: column; gap: 16px;">
                    
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <div style="flex: 1; min-width: 110px; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 12px; text-align: center;">
                            <div style="font-size: 22px; font-weight: 800; color: #047857;" id="count-going">0</div>
                            <div style="font-size: 12px; font-weight: 700; color: #065f46; text-transform: uppercase;">🚗 Їдемо</div>
                        </div>
                        <div style="flex: 1; min-width: 110px; background: #fff1f2; border: 1px solid #fecdd3; border-radius: 10px; padding: 12px; text-align: center;">
                            <div style="font-size: 22px; font-weight: 800; color: #be123c;" id="count-not-going">0</div>
                            <div style="font-size: 12px; font-weight: 700; color: #9f1239; text-transform: uppercase;">🏠 Не їдемо</div>
                        </div>
                        <div style="flex: 1; min-width: 110px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; text-align: center;">
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;" id="count-total">0</div>
                            <div style="font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">👥 Всього</div>
                        </div>
                    </div>

                    <div style="background: #f1f5f9; border-radius: 999px; height: 12px; overflow: hidden; display: flex;">
                        <div id="progress-going" style="width: 0%; background: #10b981; transition: width 0.4s ease;"></div>
                        <div id="progress-not-going" style="width: 0%; background: #f43f5e; transition: width 0.4s ease;"></div>
                    </div>

                    <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; background: #ffffff;">
                        <div style="font-size: 13px; font-weight: 700; color: #475569; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px;">
                            📋 Учасники голосування:
                        </div>
                        <div id="participants-list" style="display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto;">
                            <div style="color: #94a3b8; font-size: 13px; font-style: italic; text-align: center; padding: 12px;">
                                Поки немає голосів. Будьте першим!
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Restaurant Content Grid -->
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;">
            {rest_sections_html}
        </div>

        <!-- Footer -->
        <div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 24px; padding: 12px;">
            Сформовано автоматично • <a href="https://carry.ck.ua" style="color: #2563eb; text-decoration: none;">Carry.ck.ua</a>
        </div>
        <!-- Main App Closing Div -->
    </div>

    <!-- Initialization and Voting Logic -->
    <script>
// Authentication Logic
let authToken = localStorage.getItem('diner_auth_token');
let authUsername = localStorage.getItem('diner_auth_username');
let authCar = localStorage.getItem('diner_auth_car');

function checkAuthStatus() {{
    const authContainer = document.getElementById('auth-container');
    const mainApp = document.getElementById('main-app');
    
    if (authToken) {{
        authContainer.style.display = 'none';
        mainApp.style.display = 'block';
        if (authCar && document.getElementById('vote-car')) {{
            document.getElementById('vote-car').value = authCar;
        }}
        fetchVotes();
    }} else {{
        authContainer.style.display = 'block';
        mainApp.style.display = 'none';
    }}
}}

async function handleAuth(event, type) {{
    event.preventDefault();
    const usernameEl = document.getElementById('auth-username');
    const passwordEl = document.getElementById('auth-password');
    const carEl = document.getElementById('auth-car');
    const errorEl = document.getElementById('auth-error');
    
    if (!usernameEl.value || !passwordEl.value) {{
        errorEl.innerText = 'Будь ласка, введіть логін та пароль.';
        errorEl.style.display = 'block';
        return;
    }}

    errorEl.style.display = 'none';
    const endpoint = type === 'login' ? '/api/login' : '/api/register';
    
    let payload = {{ username: usernameEl.value.trim(), password: passwordEl.value }};
    if (type === 'register' && carEl) {{
        payload.car = carEl.value.trim();
    }}
    
    try {{
        const res = await fetch(endpoint, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(payload)
        }});
        const data = await res.json();
        
        if (data.success) {{
            authToken = data.token;
            authUsername = data.username;
            authCar = data.car || '';
            localStorage.setItem('diner_auth_token', authToken);
            localStorage.setItem('diner_auth_username', authUsername);
            localStorage.setItem('diner_auth_car', authCar);
            usernameEl.value = '';
            passwordEl.value = '';
            if (carEl) carEl.value = '';
            checkAuthStatus();
            showToast(type === 'login' ? 'Успішний вхід!' : 'Успішна реєстрація!');
        }} else {{
            errorEl.innerText = data.error || 'Помилка авторизації.';
            errorEl.style.display = 'block';
        }}
    }} catch (e) {{
        errorEl.innerText = "Помилка з'єднання із сервером.";
        errorEl.style.display = 'block';
    }}
}}

async function handleLogout() {{
    if (authToken) {{
        try {{
            await fetch('/api/logout', {{
                method: 'POST',
                headers: {{ 'Authorization': `Bearer ${{authToken}}` }}
            }});
        }} catch (e) {{}}
    }}
    authToken = null;
    authUsername = null;
    authCar = null;
    localStorage.removeItem('diner_auth_token');
    localStorage.removeItem('diner_auth_username');
    localStorage.removeItem('diner_auth_car');
    checkAuthStatus();
}}

let currentVotes = [];
let lastWinner = null;
let selectedDriver = null;

// Firebase Realtime Database URL for global sync on GitHub Pages

document.addEventListener('DOMContentLoaded', () => {{
    // Auto-clean old days' votes from localStorage
    try {{
        const todayKey = 'diner_votes_' + getTodayStr();
        const todayDriverKey = 'diner_driver_' + getTodayStr();
        for (let i = localStorage.length - 1; i >= 0; i--) {{
            const k = localStorage.key(i);
            if (k && ((k.startsWith('diner_votes_') && k !== todayKey) || (k.startsWith('diner_driver_') && k !== todayDriverKey))) {{
                localStorage.removeItem(k);
            }}
        }}
    }} catch(e) {{}}

    const savedName = localStorage.getItem('diner_user_name');
    if (savedName) {{
        const input = document.getElementById('voter-name-input');
        if (input) input.value = savedName;
    }}
    updateTimeStatus();
    checkAuthStatus();
    setInterval(updateTimeStatus, 60000); // Check time every minute
    
    // fetchVotes is now called inside checkAuthStatus if logged in
    // Automatic polling is disabled. Users must refresh manually or vote to see updates.
    initFireworksCanvas();
}});

function getKyivTimeInfo() {{
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('uk-UA', {{
        timeZone: 'Europe/Kiev',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    }});
    const parts = formatter.formatToParts(now);
    let hour = 0, minute = 0, second = 0;
    parts.forEach(p => {{
        if (p.type === 'hour') hour = parseInt(p.value, 10);
        if (p.type === 'minute') minute = parseInt(p.value, 10);
        if (p.type === 'second') second = parseInt(p.value, 10);
    }});
    const totalMinutes = hour * 60 + minute;
    // Voting window temporarily expanded for testing (always open)
    const isOpen = true;
    const timeStr = `${{String(hour).padStart(2, '0')}}:${{String(minute).padStart(2, '0')}}:${{String(second).padStart(2, '0')}}`;
    return {{ isOpen, timeStr, hour, minute }};
}}

function updateTimeStatus() {{
    const statusEl = document.getElementById('voting-time-status');
    const submitBtn = document.getElementById('submit-vote-btn');
    const {{ isOpen, timeStr }} = getKyivTimeInfo();
    
    if (statusEl) {{
        if (isOpen) {{
            statusEl.style.background = '#dcfce7';
            statusEl.style.color = '#15803d';
            statusEl.style.border = '1px solid #86efac';
            statusEl.innerHTML = `🟢 <strong>Голосування ВІДКРИТЕ</strong> (Зараз ${{timeStr}} Київ • 11:30 – 12:00)`;
        }} else {{
            statusEl.style.background = '#fef2f2';
            statusEl.style.color = '#b91c1c';
            statusEl.style.border = '1px solid #fca5a5';
            statusEl.innerHTML = `🔴 <strong>Голосування ЗАКРИТЕ</strong> (Зараз ${{timeStr}} Київ • Приймається з 11:30 до 12:00)`;
        }}
    }}

    if (submitBtn) {{
        if (!isOpen) {{
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.55';
            submitBtn.style.cursor = 'not-allowed';
            submitBtn.innerText = '🔒 Голосування закрите (11:30 - 12:00)';
        }} else {{
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.style.cursor = 'pointer';
            submitBtn.innerText = '🗳️ Проголосувати / Оновити';
        }}
    }}
}}

function getSelectedDriverKey() {{
    return 'diner_driver_' + getTodayStr();
}}

function getSelectedDriver() {{
    return localStorage.getItem(getSelectedDriverKey()) || selectedDriver;
}}

function setSelectedDriver(driverName) {{
    selectedDriver = driverName;
    if (driverName) {{
        localStorage.setItem(getSelectedDriverKey(), driverName);
    }} else {{
        localStorage.removeItem(getSelectedDriverKey());
    }}
}}


const DISQUALIFIED_ROLES = ['Фраєр', 'Барига', 'Чорт', 'Шерсть', 'Опущений'];

function isDisqualifiedRole(role) {{
    if (!role) return false;
    return DISQUALIFIED_ROLES.some(r => role.toLowerCase().includes(r.toLowerCase()));
}}

function pickRandomDriver(userTriggered = true) {{
    const goingVotes = currentVotes.filter(v => v.choice === 'going' && !isDisqualifiedRole(v.role));
    if (goingVotes.length === 0) {{
        setSelectedDriver(null);
        renderDriverBanner(null, 0);
        if (userTriggered) {{
            showToast("⚠️ Жоден авторитетний учасник ще не проголосував 'Їдемо'!", true);
        }}
        return;
    }}

    const randomIndex = Math.floor(Math.random() * goingVotes.length);
    const chosenVoter = goingVotes[randomIndex];
    setSelectedDriver(chosenVoter.name);
    renderDriverBanner(chosenVoter.name, goingVotes.length);

    if (userTriggered) {{
        try {{ launchFireworks(); }} catch(e) {{}}
        showToast(`🚘 Водієм обрано: ${{chosenVoter.name}}!`);
    }}
}}

function getCarBadge(car) {{
    if (!car || car === 'Без авто') return '';
    if (car === 'BMW') return '🏎️ BMW';
    if (car === 'Audi') return '🚔 Audi';
    if (car === 'Mazda') return '🚗 Mazda';
    if (car === 'VW') return '🚘 VW';
    return '🚘 ' + car;
}}

function renderDriverBanner(driverName, goingCount) {{
    const titleEl = document.getElementById('driver-title');
    if (!titleEl) return;

    if (driverName) {{
        const driverVote = currentVotes.find(v => v.name.toLowerCase() === (driverName || '').toLowerCase());
        const carBadge = (driverVote && driverVote.car && driverVote.car !== 'Без авто') ? ` (<strong style="color: #1e40af;">${{getCarBadge(driverVote.car)}}</strong>)` : '';
        titleEl.innerHTML = `🚘 На машині їде: <strong style="color: #1d4ed8; text-decoration: underline;">${{escapeHtml(driverName)}}</strong>${{carBadge}} <span style="font-size: 13px; font-weight: 600; color: #475569;">(обрано випадковим чином серед ${{goingCount}} ${{pluralVotes(goingCount)}})</span>`;
    }} else if (goingCount > 0) {{
        titleEl.innerHTML = `<em>Натисніть кнопку справа, щоб обрати водія з ${{goingCount}} ${{pluralVotes(goingCount)}}</em>`;
    }} else {{
        titleEl.innerText = 'Ще немає учасників, які проголосували "Їдемо" 🚗';
    }}
}}

function getTodayStr() {{
    return new Date().toISOString().split('T')[0];
}}

async function fetchVotes() {{
    const today = getTodayStr();

    // 1. Try Firebase Realtime Database (Cloud DB for GitHub Pages)

    // 2. Local Server Fallback
    try {{
        const res = await fetch('/api/votes', {{
            headers: {{ 'Authorization': `Bearer ${{authToken}}` }}
        }});
        const data = await res.json();
        if (data.success) {{
            currentVotes = data.votes || [];
            renderVotes(currentVotes, data.summary);
            return;
        }}
    }} catch (e) {{}}

    // 3. LocalStorage Fallback
    loadFromLocalStorage();
}}

function loadFromLocalStorage() {{
    const today = getTodayStr();
    const key = 'diner_votes_' + today;
    try {{
        const data = localStorage.getItem(key);
        currentVotes = data ? JSON.parse(data) : [];
    }} catch (e) {{
        currentVotes = [];
    }}
    renderVotes(currentVotes);
}}

function saveToLocalStorage(votes) {{
    const today = getTodayStr();
    const key = 'diner_votes_' + today;
    localStorage.setItem(key, JSON.stringify(votes));
}}

function renderVotes(votes, summary) {{
    updateTimeStatus();

    const validVotes = votes.filter(v => !isDisqualifiedRole(v.role));
    const goingVotes = validVotes.filter(v => v.choice === 'going');
    const notGoingVotes = votes.filter(v => v.choice === 'not_going');
    
    document.getElementById('count-going').innerText = goingVotes.length;
    document.getElementById('count-not-going').innerText = notGoingVotes.length;
    document.getElementById('count-total').innerText = validVotes.length + notGoingVotes.length;

    const total = (validVotes.length + notGoingVotes.length) || 1;
    const goingPct = (goingVotes.length / total) * 100;
    const notGoingPct = (notGoingVotes.length / total) * 100;

    document.getElementById('progress-going').style.width = (total ? goingPct : 0) + '%';
    document.getElementById('progress-not-going').style.width = (total ? notGoingPct : 0) + '%';

    // Check & Render Driver Selection
    let currentDriver = getSelectedDriver();
    const driverStillGoing = goingVotes.some(v => v.name.toLowerCase() === (currentDriver || '').toLowerCase());
    if (currentDriver && !driverStillGoing) {{
        if (goingVotes.length > 0) {{
            pickRandomDriver(false);
        }} else {{
            setSelectedDriver(null);
            renderDriverBanner(null, 0);
        }}
    }} else {{
        renderDriverBanner(currentDriver, goingVotes.length);
    }}

    // Calculate Restaurant Winner & Breakdown
    let winnerName = summary ? summary.winner : null;
    let winnerVotes = summary ? summary.winner_votes : 0;
    let restTally = summary ? summary.restaurants : {{}};

    if (!summary) {{
        restTally = {{}};
        goingVotes.forEach(v => {{
            const r = v.restaurant || 'Будь-яке / Без різниці';
            restTally[r] = (restTally[r] || 0) + 1;
        }});
        let maxCount = 0;
        for (const [r, count] of Object.entries(restTally)) {{
            if (count > maxCount) {{
                maxCount = count;
                winnerName = r;
                winnerVotes = count;
            }}
        }}
    }}

    const winnerTitleEl = document.getElementById('winner-title');
    const breakdownEl = document.getElementById('restaurant-breakdown');

    if (winnerName && winnerVotes > 0) {{
        winnerTitleEl.innerHTML = `🎉 <strong>${{escapeHtml(winnerName)}}</strong> — ${{winnerVotes}} ${{pluralVotes(winnerVotes)}}!`;
        if (lastWinner !== winnerName && goingVotes.length > 0) {{
            lastWinner = winnerName;
            launchFireworks();
        }}
    }} else {{
        winnerTitleEl.innerText = 'Очікування перших авторитетних голосів...';
    }}

    let breakdownHtml = '';
    for (const [r, count] of Object.entries(restTally)) {{
        breakdownHtml += `<span style="background: #ffffff; color: #78350f; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 20px; border: 1px solid #fcd34d;">${{escapeHtml(r)}}: ${{count}}</span>`;
    }}
    breakdownEl.innerHTML = breakdownHtml;

    // Render Participant Cards
    const container = document.getElementById('participants-list');
    if (votes.length === 0) {{
        container.innerHTML = '<div style="color: #94a3b8; font-size: 13px; font-style: italic; text-align: center; padding: 12px;">Поки немає голосів. Будьте першим!</div>';
        return;
    }}

    let html = '';
    votes.forEach(v => {{
        const isDisq = isDisqualifiedRole(v.role);
        const isGoing = v.choice === 'going';
        const badgeBg = isDisq ? '#fef2f2' : (isGoing ? '#ecfdf5' : '#fff1f2');
        const badgeBorder = isDisq ? '#fca5a5' : (isGoing ? '#a7f3d0' : '#fecdd3');
        const badgeText = isDisq ? '#b91c1c' : (isGoing ? '#047857' : '#be123c');
        const icon = isDisq ? '🚫 Без права голосу' : (isGoing ? '🚗 Їдемо' : '🏠 Не їдемо');
        const restStr = (isGoing && v.restaurant && !isDisq) ? `<span style="background: rgba(255,255,255,0.8); border: 1px solid #cbd5e1; border-radius: 6px; padding: 2px 6px; font-size: 11px; color: #334155; margin-left: 4px;">📍 ${{escapeHtml(v.restaurant)}}</span>` : '';
        const carStr = (isGoing && v.car && v.car !== 'Без авто' && !isDisq) ? `<span style="background: #eff6ff; border: 1px solid #93c5fd; border-radius: 6px; padding: 2px 6px; font-size: 11px; color: #1e40af; font-weight: 700; margin-left: 4px;">${{getCarBadge(v.car)}}</span>` : '';
        const roleStr = v.role ? `<span style="background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 2px 6px; font-size: 11px; color: #475569; font-weight: 600; margin-left: 4px;">🕵️ ${{escapeHtml(v.role)}}</span>` : '';
        const noteStr = v.note ? `<span style="color: #64748b; font-size: 12px; margin-left: 4px;">(${{escapeHtml(v.note)}})</span>` : '';

        html += `
        <div style="display: flex; justify-content: space-between; align-items: center; background: ${{badgeBg}}; border: 1px solid ${{badgeBorder}}; border-radius: 8px; padding: 8px 12px;">
            <div style="font-size: 14px; font-weight: 600; color: #0f172a; display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                <span style="font-size: 12px; font-weight: 700; color: ${{badgeText}}; background: #ffffff; padding: 2px 8px; border-radius: 6px; border: 1px solid ${{badgeBorder}};">${{icon}}</span>
                <strong>${{escapeHtml(v.name)}}</strong>
                ${{roleStr}}
                ${{carStr}}
                ${{restStr}}
                ${{noteStr}}
            </div>
        </div>
        `;
    }});

    container.innerHTML = html;
}}

function pluralVotes(count) {{
    if (count === 1) return 'голос';
    if (count >= 2 && count <= 4) return 'голоси';
    return 'голосів';
}}

function escapeHtml(str) {{
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {{
        return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }}[m];
    }});
}}

function showToast(message, isError = false) {{
    let toast = document.getElementById('vote-toast');
    if (!toast) {{
        toast = document.createElement('div');
        toast.id = 'vote-toast';
        toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; padding: 12px 20px; border-radius: 10px; font-weight: 700; font-size: 14px; color: #ffffff; z-index: 99999; box-shadow: 0 10px 25px rgba(0,0,0,0.2); transition: all 0.3s ease; opacity: 0; transform: translateY(10px);';
        document.body.appendChild(toast);
    }}
    toast.style.background = isError ? '#ef4444' : '#059669';
    toast.innerText = message;
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    setTimeout(() => {{
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
    }}, 2500);
}}

async function handleVoteSubmit(event) {{
    if (event) {{
        event.preventDefault();
    }}
    
    const {{ isOpen, timeStr }} = getKyivTimeInfo();
    if (!isOpen) {{
        showToast(`🔴 Голосування закрите! Приймається лише з 11:30 до 12:00 за Києвом (Зараз ${{timeStr}}).`, true);
        alert(`⛔ Голосування закрите!\n\nЗараз ${{timeStr}} за київським часом.\nОфіційне голосування відкрите виключно з 11:30 до 12:00.`);
        return false;
    }}

    const name = authUsername; // Inferred from session

    if (!name) {{
        alert("Помилка авторизації. Перезавантажте сторінку.");
        return false;
    }}

    const choiceEl = document.querySelector('input[name="vote-choice"]:checked');
    const choice = choiceEl ? choiceEl.value : 'going';
    
    const restEl = document.getElementById('voter-restaurant-select');
    const restaurant = restEl ? restEl.value : '';
    
    if (choice === 'going' && !restaurant) {{
        alert('Будь ласка, оберіть заклад!');
        submitBtn.disabled = false;
        submitBtn.innerText = '🗳️ Проголосувати / Оновити';
        return false;
    }}
    
    const carEl = document.getElementById('voter-car-select');
    const car = carEl ? carEl.value : '';

    const roleEl = document.getElementById('voter-role-select');
    const role = roleEl ? roleEl.value : '';

    if (isDisqualifiedRole(role)) {{
        alert(`⛔ УВАГА! ОБМЕЖЕННЯ ЗА ПОНЯТТЯМИ!\n\nМасть "${{role}}" не має права голосу!\n\nВаше ім'я з позначкою 🚫 (Без права голосу) буде додано в список, але голос НЕ враховуватиметься при виборі закладу та водія.`);
    }}

    const noteEl = document.getElementById('voter-note-input');
    const note = noteEl ? noteEl.value.trim() : '';

    if (choice === 'going') {{
        try {{ launchFireworks(); }} catch(e) {{}}
    }}

    const today = getTodayStr();
    const voteData = {{
        name: name,
        choice: choice,
        restaurant: restaurant,
        car: car,
        role: role,
        note: note,
        updated_at: new Date().toISOString()
    }};

    // 1. Instant local update
    const idx = currentVotes.findIndex(v => v.name.toLowerCase() === name.toLowerCase());
    if (idx >= 0) {{
        currentVotes[idx] = voteData;
    }} else {{
        currentVotes.push(voteData);
    }}
    saveToLocalStorage(currentVotes);
    renderVotes(currentVotes);

    showToast("✅ Ваш голос збережено!");

    // 2. Background Cloud Sync (Firebase)

    // 3. Background Local Server Sync
    try {{
        fetch('/api/votes', {{
            method: 'POST',
            headers: {{ 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${{authToken}}`
            }},
            body: JSON.stringify({{ choice, restaurant, car, role, note }})
        }}).then(res => res.json()).then(data => {{
            if (data && data.success) {{
                currentVotes = data.votes;
                renderVotes(currentVotes, data.summary);
            }}
        }}).catch(e => {{}});
    }} catch (e) {{}}

    return false;
}}

async function deleteVote(name) {{
    const today = getTodayStr();

    // 1. Instant local update
    currentVotes = currentVotes.filter(v => v.name.toLowerCase() !== name.toLowerCase());
    saveToLocalStorage(currentVotes);
    renderVotes(currentVotes);
    showToast("🗑️ Голос видалено");

    // 2. Background Cloud Sync (Firebase)

    // 3. Background Local Server Sync
    try {{
        fetch(`/api/votes`, {{ 
            method: 'DELETE',
            headers: {{ 'Authorization': `Bearer ${{authToken}}` }}
        }})
            .then(res => res.json())
            .then(data => {{
                if (data && data.success) {{
                    currentVotes = data.votes;
                    renderVotes(currentVotes, data.summary);
                }}
            }}).catch(e => {{}});
    }} catch (e) {{}}
}}


function copyVotesForTelegram() {{
    if (!currentVotes || currentVotes.length === 0) {{
        alert('Немає голосів для копіювання!');
        return;
    }}

    const going = currentVotes.filter(v => v.choice === 'going');
    const notGoing = currentVotes.filter(v => v.choice === 'not_going');
    const todayStr = new Date().toLocaleDateString('uk-UA');
    const currentDriver = getSelectedDriver();

    let lines = [];
    lines.push('🍱 *Голосування на обід (' + todayStr + ')*');
    lines.push('⏰ _Час голосування: 11:30 - 12:00 (Київ)_');
    lines.push('');
    lines.push('🚗 *Їдемо (' + going.length + '):*');
    if (going.length > 0) {{
        going.forEach(v => {{
            const rStr = v.restaurant ? ' [' + v.restaurant + ']' : '';
            const carStr = (v.car && v.car !== 'Без авто') ? ' ' + getCarBadge(v.car) : '';
            const note = v.note ? ' _(' + v.note + ')_' : '';
            lines.push('  • ' + v.name + carStr + rStr + note);
        }});
    }} else {{
        lines.push('  _(нікого)_');
    }}

    if (going.length > 0) {{
        lines.push('');
        const driverVote = currentVotes.find(v => v.name.toLowerCase() === (currentDriver || '').toLowerCase());
        const driverCarStr = (driverVote && driverVote.car && driverVote.car !== 'Без авто') ? ' (' + getCarBadge(driverVote.car) + ')' : '';
        lines.push('🚘 *Водій / Чия машина:* ' + (currentDriver ? '*' + currentDriver + '*' + driverCarStr : '_(ще не обрано)_'));
    }}

    lines.push('');
    lines.push('🏠 *Не їдемо (' + notGoing.length + '):*');
    if (notGoing.length > 0) {{
        notGoing.forEach(v => {{
            const note = v.note ? ' _(' + v.note + ')_' : '';
            lines.push('  • ' + v.name + note);
        }});
    }} else {{
        lines.push('  _(нікого)_');
    }}

    const text = lines.join(String.fromCharCode(10));

    navigator.clipboard.writeText(text).then(() => {{
        const btn = document.getElementById('copy-tg-btn');
        const origText = btn.innerHTML;
        btn.innerHTML = '✅ Скопійовано!';
        btn.style.background = '#059669';
        setTimeout(() => {{
            btn.innerHTML = origText;
            btn.style.background = '#0284c7';
        }}, 2000);
    }}).catch(err => {{
        alert('Результат:' + String.fromCharCode(10, 10) + text);
    }});
}}

/* Canvas Fireworks Celebration Engine */
let fwCanvas, fwCtx, particles = [];

function initFireworksCanvas() {{
    fwCanvas = document.getElementById('fireworks-canvas');
    if (!fwCanvas) return;
    fwCtx = fwCanvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    requestAnimationFrame(updateFireworks);
}}

function resizeCanvas() {{
    if (fwCanvas) {{
        fwCanvas.width = window.innerWidth;
        fwCanvas.height = window.innerHeight;
    }}
}}

function launchFireworks() {{
    if (!fwCanvas) initFireworksCanvas();
    const colors = ['#f43f5e', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6'];
    
    const centers = [
        {{ x: window.innerWidth * 0.3, y: window.innerHeight * 0.35 }},
        {{ x: window.innerWidth * 0.5, y: window.innerHeight * 0.25 }},
        {{ x: window.innerWidth * 0.7, y: window.innerHeight * 0.35 }}
    ];

    centers.forEach(c => {{
        for (let i = 0; i < 45; i++) {{
            const angle = Math.random() * Math.PI * 2;
            const speed = Math.random() * 8 + 2;
            particles.push({{
                x: c.x,
                y: c.y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                color: colors[Math.floor(Math.random() * colors.length)],
                size: Math.random() * 4 + 2,
                alpha: 1,
                decay: Math.random() * 0.02 + 0.015,
                gravity: 0.12
            }});
        }}
    }});
}}

function updateFireworks() {{
    if (fwCtx && fwCanvas) {{
        fwCtx.clearRect(0, 0, fwCanvas.width, fwCanvas.height);
        for (let i = particles.length - 1; i >= 0; i--) {{
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            p.alpha -= p.decay;

            if (p.alpha <= 0) {{
                particles.splice(i, 1);
            }} else {{
                fwCtx.save();
                fwCtx.globalAlpha = p.alpha;
                fwCtx.fillStyle = p.color;
                fwCtx.beginPath();
                fwCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                fwCtx.fill();
                fwCtx.restore();
            }}
        }}
    }}
    requestAnimationFrame(updateFireworks);
}}
    </script>
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
