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

    def _check_rate_limit(self, limit=None):
        return True

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

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
        body_bytes = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body_bytes)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body_bytes)
        try:
            self.wfile.flush()
        except Exception:
            pass

    def do_GET(self):
        
        if not self._check_rate_limit(limit=120):
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        if parsed.path == '/api/me':
            user = self._get_auth_user()
            if user:
                self._send_json(200, {'success': True, 'username': user['username'], 'car': user['car']})
            else:
                self._send_json(401, {'success': False, 'error': 'Unauthorized'})
        elif parsed.path == '/api/votes':
            try:
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
            except Exception as e:
                self._send_json(500, {'success': False, 'error': str(e)})
        else:
            super().do_GET()

    def do_POST(self):
        
        if not self._check_rate_limit(limit=30):
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        
        if parsed.path in ('/api/register', '/api/login'):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                username = (data.get('username') or '').strip().upper()
                password = data.get('password')
                if parsed.path == '/api/register':
                    car = data.get('car', '')
                    token, user, user_car = db.register_user(username, password, car)
                else:
                    token, user, user_car = db.login_user(username, password)
                self._send_json(200, {'success': True, 'token': token, 'username': user, 'car': user_car})
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
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                
                name = (user['username'] if user else (data.get('name') or data.get('username') or '')).strip().upper()
                if not name:
                    self._send_json(400, {'success': False, 'error': 'Будь ласка, вкажіть ім\'я!'})
                    return
                
                choice = data.get('choice')
                restaurant = data.get('restaurant', '')
                
                if choice == 'going' and not restaurant:
                    raise ValueError("Будь ласка, оберіть заклад!")
                
                car = data.get('car')
                if car is None and user:
                    car = user['car']
                if not car:
                    car = ''
                
                role = data.get('role', '')
                note = data.get('note', '')
                vote_date = data.get('date')

                votes = db.upsert_vote(name=name, choice=choice, restaurant=restaurant, car=car, role=role, note=note, vote_date=vote_date)

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
        
        if not self._check_rate_limit(limit=30):
            self._send_json(429, {'success': False, 'error': 'Забагато запитів. Зачекайте 1 хвилину.'})
            return
        parsed = urlparse(self.path)
        if parsed.path == '/api/votes':
            user = self._get_auth_user()
            params = parse_qs(parsed.query)
            vote_date = params.get('date', [None])[0]
            name = (user['username'] if user else (params.get('name', [None])[0] or '')).strip().upper()
            if not name:
                self._send_json(400, {'success': False, 'error': 'Будь ласка, вкажіть ім\'я!'})
                return

            try:
                votes = db.delete_vote(name=name, vote_date=vote_date)
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
            except Exception as e:
                self._send_json(400, {'success': False, 'error': str(e)})
        elif parsed.path == '/api/clear':
            db.clear_all_db()
            self._send_json(200, {'success': True, 'message': 'Базу даних повністю очищено!'})
        else:
            self.send_response(404)
            self.end_headers()

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

def run_server(port=5050):
    try:
        db.init_db()
    except Exception as e:
        print(f"Warning during db.init_db(): {e}", file=sys.stderr)
    server_address = ('0.0.0.0', port)
    class ThreadedServer(ThreadingHTTPServer):
        allow_reuse_address = True
    httpd = ThreadedServer(server_address, VotingHandler)
    print(f"🚀 Voting server running at http://0.0.0.0:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    run_server(port)
