import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7'
}

DAY_MAP = {
    0: 'Понеділок',
    1: 'Вівторок',
    2: 'Середа',
    3: 'Четвер',
    4: 'П\'ятниця'
}

DAY_PATTERNS = {
    0: ['понеділок', 'monday'],
    1: ['вівторок', 'tuesday'],
    2: ['середа', 'wednesday'],
    3: ['четвер', 'thursday'],
    4: ['п\'ятниця', 'пятниця', 'friday']
}

RESTAURANTS = [
    {
        'id': 'chacha',
        'name': 'Chacha che (Чача)',
        'url': 'https://carry.ck.ua/chacha',
        'icon': '🍷'
    },
    {
        'id': 'erik',
        'name': 'Eric / Bierstube (Ерік)',
        'url': 'https://carry.ck.ua/erik',
        'icon': '🍺'
    },
    {
        'id': 'escobar',
        'name': 'Escobar (Ескобар)',
        'url': 'https://escobar30.ps.me/',
        'icon': '🌮'
    }
]

def detect_day(text: str):
    """Returns day index 0..4 (Mon..Fri) if day is found in text, else None."""
    text_lower = text.lower().replace('ʼ', "'").replace('’', "'").replace('`', "'")
    for day_code, patterns in DAY_PATTERNS.items():
        for p in patterns:
            p_normalized = p.replace('ʼ', "'").replace('’', "'").replace('`', "'")
            if p_normalized in text_lower:
                return day_code
    return None

def fetch_restaurant_lunches(url: str):
    """
    Parses Tilda product catalog cards from carry.ck.ua or PosterShop cards from escobar30.ps.me.
    Returns a dict mapping day_code (0..4) -> lunch info.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[Error] Failed to fetch {url}: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    lunches_by_day = {}

    if 'ps.me' in url:
        # PosterShop platform (Escobar)
        cards = soup.find_all(attrs={"data-testid": "product_block"})
        for card in cards:
            name_el = card.find(attrs={"data-testid": "product_name"})
            if not name_el:
                continue
            title = name_el.get_text(strip=True)
            day_code = detect_day(title)
            if day_code is None:
                continue

            price_el = card.find(attrs={"data-testid": "product_price"})
            price = price_el.get_text(strip=True) if price_el else ''

            descr_el = card.find(class_=re.compile("productDescription|description"))
            raw_descr = descr_el.get_text(separator='\n', strip=True) if descr_el else ''
            
            dishes = [d.strip() for d in raw_descr.split('\n') if d.strip() and d.strip().lower() != 'склад:']

            img_el = card.find('img')
            img_url = img_el.get('src') if img_el else None

            if day_code not in lunches_by_day or (not lunches_by_day[day_code]['dishes'] and dishes):
                lunches_by_day[day_code] = {
                    'title': title,
                    'day_code': day_code,
                    'day_name': DAY_MAP[day_code],
                    'price': price if price else 'Ціна не вказана',
                    'dishes': dishes,
                    'raw_description': raw_descr,
                    'image_url': img_url
                }
    else:
        # Tilda platform (carry.ck.ua)
        cards = soup.select('.js-product, .t778__col, .t-catalog__item, .t776__col')
        for card in cards:
            name_el = card.select_one('.js-product-name, .t778__title, .t776__title')
            if not name_el:
                continue
            
            title = name_el.get_text(strip=True)
            day_code = detect_day(title)
            if day_code is None:
                continue

            descr_el = card.select_one('.t778__descr, .t776__descr, .js-product-descr')
            raw_descr = descr_el.get_text(separator='\n', strip=True) if descr_el else ''

            price_el = card.select_one('.js-product-price, .t778__price-value, .t776__price-value')
            price = price_el.get_text(strip=True) if price_el else ''

            curr_el = card.select_one('.t778__price-currency, .t776__price-currency')
            curr = curr_el.get_text(strip=True) if curr_el else 'грн.'

            img_el = card.select_one('img')
            img_url = img_el.get('src') or img_el.get('data-original') if img_el else None

            dishes = [d.strip() for d in raw_descr.split('\n') if d.strip() and d.strip().lower() != 'склад:']

            if day_code not in lunches_by_day or (not lunches_by_day[day_code]['dishes'] and dishes):
                lunches_by_day[day_code] = {
                    'title': title,
                    'day_code': day_code,
                    'day_name': DAY_MAP[day_code],
                    'price': f'{price} {curr}'.strip() if price else 'Ціна не вказана',
                    'dishes': dishes,
                    'raw_description': raw_descr,
                    'image_url': img_url
                }

    return lunches_by_day

def fetch_all_lunches():
    """
    Fetches business lunches for all configured restaurants.
    Returns structured data grouped by restaurant.
    """
    all_data = []
    for rest in RESTAURANTS:
        lunches = fetch_restaurant_lunches(rest['url'])
        all_data.append({
            'id': rest['id'],
            'name': rest['name'],
            'url': rest['url'],
            'icon': rest['icon'],
            'lunches': lunches
        })
    return all_data

if __name__ == '__main__':
    data = fetch_all_lunches()
    for rest in data:
        print(f"\n=== {rest['name']} ({rest['url']}) ===")
        for day_code in range(5):
            lunch = rest['lunches'].get(day_code)
            if lunch:
                print(f"[{lunch['day_name']}] {lunch['title']} - {lunch['price']}")
                for dish in lunch['dishes']:
                    print(f"  • {dish}")
            else:
                print(f"[{DAY_MAP[day_code]}] Меню відсутнє")
