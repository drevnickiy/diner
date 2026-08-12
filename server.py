import os
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

import db

ip_requests = {}

DISQUALIFIED_ROLES = ['фраєр', 'барига', 'чорт', 'шерсть', 'опущений']

def is_disqualified_role(role):
    if not role:
        return False
    r_lower = role.lower()
    return any(d in r_lower for d in DISQUALIFIED_ROLES)

class VotingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        public_dir = os.path.join(os.path.dirname(__file__), 'public')
        super().__init__(*args, directory=public_dir, **kwargs)

    def _check_rate_limit(self):
        client_ip = self.client_address[0]
        now = time.time()
        if client_ip not in ip_requests:
            ip_requests[client_ip] = []
        ip_requests[client_ip] = [t for t in ip_requests[client_ip] if now - t < 60]
        if len(ip_requests[client_ip]) >= 10:
            return False
        ip_requests[client_ip].append(now)
        return True

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _calculate_summary(self, votes):
        valid_votes = [v for v in votes if not is_disqualified_role(v.get('role', ''))]
        going_votes = [v for v in valid_votes if v['choice'] == 'going']
        not_going_votes = [v for v in votes if v['choice'] == 'not_going']

        # Restaurant tally among going voters
        rest_tally = {}
        for v in going_votes:
            r = v.get('restaurant') or 'Будь-яке'
            rest_tally[r] = rest_tally.get(r, 0) + 1

        # Determine winner
        winner = None
        max_votes = 0
        for r, count in rest_tally.items():
            if count > max_votes:
                max_votes = count
                winner = r

        return {
            'going': len(going_votes),
            'not_going': len(not_going_votes),
            'total': len(valid_votes) + len(not_going_votes),
            'restaurants': rest_tally,
            'winner': winner,
            'winner_votes': max_votes
        }

    def _get_auth_user(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        token = auth_header.split(' ')[1]
        return db.get_user_by_token(token)

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        
        if not self._check_rate_limit():
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        if parsed.path == '/api/me':
            user = self._get_auth_user()
            if user:
                self._send_json(200, {'success': True, 'username': user})
            else:
                self._send_json(401, {'success': False, 'error': 'Unauthorized'})
        elif parsed.path == '/api/votes':
            params = parse_qs(parsed.query)
            vote_date = params.get('date', [None])[0]
            votes = db.get_votes(vote_date)
            
            response_data = {
                'success': True,
                'date': vote_date or db.get_today_date_str(),
                'votes': votes,
                'summary': self._calculate_summary(votes)
            }
            self._send_json(200, response_data)
        else:
            super().do_GET()

    def do_POST(self):
        
        if not self._check_rate_limit():
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        
        if parsed.path in ('/api/register', '/api/login'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                username = data.get('username')
                password = data.get('password')
                if parsed.path == '/api/register':
                    raise ValueError("Реєстрація наразі вимкнена.")
                    # token, user = db.register_user(username, password)
                else:
                    token, user = db.login_user(username, password)
                self._send_json(200, {'success': True, 'token': token, 'username': user})
            except Exception as e:
                self._send_json(400, {'success': False, 'error': str(e)})
                
        elif parsed.path == '/api/logout':
            auth_header = self.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                db.logout_user(token)
            self._send_json(200, {'success': True})
            
        elif parsed.path == '/api/votes':
            user = self._get_auth_user()
            if not user:
                self._send_json(401, {'success': False, 'error': 'Необхідно авторизуватися'})
                return
                
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                
                # Check Kyiv time window (11:30 - 12:00) unless force=true
                params = parse_qs(parsed.query)
                force = params.get('force', ['false'])[0].lower() == 'true' or data.get('force') is True
                
                if not force:
                    try:
                        from zoneinfo import ZoneInfo
                        now = datetime.now(ZoneInfo("Europe/Kyiv"))
                    except Exception:
                        now = datetime.now()
                    total_min = now.hour * 60 + now.minute
                    if not (690 <= total_min < 720):
                        time_str = now.strftime('%H:%M:%S')
                        raise ValueError(f"Голосування закрите! Зараз {time_str} за Києвом. Приймається лише з 11:30 до 12:00.")

                name = user
                choice = data.get('choice')
                restaurant = data.get('restaurant', '')
                car = data.get('car', '')
                role = data.get('role', '')
                note = data.get('note', '')
                vote_date = data.get('date')

                raise ValueError("Запис у базу даних наразі вимкнено адміністратором.")
                # votes = db.upsert_vote(name=name, choice=choice, restaurant=restaurant, car=car, role=role, note=note, vote_date=vote_date)

                response_data = {
                    'success': True,
                    'message': 'Голос успішно збережено!',
                    'votes': votes,
                    'summary': self._calculate_summary(votes)
                }
                self._send_json(200, response_data)
            except Exception as e:
                self._send_json(400, {'success': False, 'error': str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        
        if not self._check_rate_limit():
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        if parsed.path == '/api/votes':
            user = self._get_auth_user()
            if not user:
                self._send_json(401, {'success': False, 'error': 'Необхідно авторизуватися'})
                return
                
            params = parse_qs(parsed.query)
            vote_date = params.get('date', [None])[0]
            name = user
            
            if name:
                raise ValueError("Видалення голосів наразі вимкнено адміністратором.")
                # votes = db.delete_vote(name, vote_date)
                going_count = sum(1 for v in votes if v['choice'] == 'going')
                not_going_count = sum(1 for v in votes if v['choice'] == 'not_going')
                response_data = {
                    'success': True,
                    'message': 'Голос видалено',
                    'votes': votes,
                    'summary': {
                        'going': going_count,
                        'not_going': not_going_count,
                        'total': len(votes)
                    }
                }
                self._send_json(200, response_data)
            else:
                self._send_json(400, {'success': False, 'error': 'Ім\'я користувача не вказано'})
        else:
            self.send_response(404)
            self.end_headers()

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

def run_server(port=5050):
    db.init_db()
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, VotingHandler)
    print(f"🚀 Voting server running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
