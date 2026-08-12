import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from datetime import datetime

import db

class VotingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        public_dir = os.path.join(os.path.dirname(__file__), 'public')
        super().__init__(*args, directory=public_dir, **kwargs)

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _calculate_summary(self, votes):
        going_votes = [v for v in votes if v['choice'] == 'going']
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
            'total': len(votes),
            'restaurants': rest_tally,
            'winner': winner,
            'winner_votes': max_votes
        }

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/votes':
            params = parse_qs(parsed.query)
            vote_date = params.get('date', [None])[0]
            votes = db.get_votes(vote_date)
            
            response_data = {
                'success': True,
                'date': vote_date or db.get_today_date_str(),
                'votes': votes,
                'summary': self._calculate_summary(votes)
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/votes':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                data = json.loads(body)
                name = data.get('name')
                choice = data.get('choice')
                restaurant = data.get('restaurant', '')
                note = data.get('note', '')
                vote_date = data.get('date')

                votes = db.upsert_vote(name=name, choice=choice, restaurant=restaurant, note=note, vote_date=vote_date)

                response_data = {
                    'success': True,
                    'message': 'Голос успішно збережено!',
                    'votes': votes,
                    'summary': self._calculate_summary(votes)
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/votes':
            params = parse_qs(parsed.query)
            name = params.get('name', [None])[0]
            vote_date = params.get('date', [None])[0]

            if not name:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    try:
                        data = json.loads(body)
                        name = data.get('name')
                        vote_date = data.get('date')
                    except Exception:
                        pass

            if name:
                votes = db.delete_vote(name, vote_date)
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
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': 'Ім\'я користувача не вказано'}).encode('utf-8'))
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
