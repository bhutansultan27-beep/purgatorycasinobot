from flask import Flask, render_template, jsonify, request
import os
import json
import hmac
import hashlib
from urllib.parse import parse_qsl

app = Flask(__name__, static_folder='static', template_folder='templates')

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set()
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = set(int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip())
    except ValueError:
        pass

def load_dynamic_admins():
    try:
        if os.path.exists('casino_data.json'):
            with open('casino_data.json', 'r') as f:
                data = json.load(f)
                return set(data.get('dynamic_admins', []))
    except:
        pass
    return set()

def is_admin(user_id):
    dynamic_admins = load_dynamic_admins()
    return user_id in ADMIN_IDS or user_id in dynamic_admins

def validate_init_data(init_data):
    if not init_data or not BOT_TOKEN:
        return None
    try:
        parsed = dict(parse_qsl(init_data))
        check_hash = parsed.pop('hash', None)
        if not check_hash:
            return None
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash == check_hash:
            user_data = json.loads(parsed.get('user', '{}'))
            return user_data
    except:
        pass
    return None

def get_user_from_db(user_id):
    try:
        if os.path.exists('casino_data.json'):
            with open('casino_data.json', 'r') as f:
                data = json.load(f)
                user = data.get('users', {}).get(str(user_id), {})
                if user:
                    total_wagered = user.get('total_wagered', 0)
                    games_played = user.get('games_played', 0)
                    games_won = user.get('games_won', 0)
                    win_rate = round((games_won / games_played * 100) if games_played > 0 else 0, 1)
                    return {
                        "balance": user.get('balance', 0),
                        "level_emoji": "⚪",
                        "level_name": "Unranked",
                        "total_wagered": total_wagered,
                        "total_won": user.get('total_pnl', 0) if user.get('total_pnl', 0) > 0 else 0,
                        "games_played": games_played,
                        "win_rate": win_rate
                    }
    except:
        pass
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/blackjack')
def blackjack():
    return render_template('blackjack.html')

@app.route('/slots')
def slots():
    return render_template('slots.html')

@app.route('/mines')
def mines():
    return render_template('mines.html')

@app.route('/limbo')
def limbo():
    return render_template('limbo.html')

@app.route('/keno')
def keno():
    return render_template('keno.html')

@app.route('/hilo')
def hilo():
    return render_template('hilo.html')

@app.route('/baccarat')
def baccarat():
    return render_template('baccarat.html')

@app.route('/roulette')
def roulette():
    return render_template('coming_soon.html', game='Roulette')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/user', methods=['POST'])
def get_user():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        user_data = None
        admin_status = False
        
        if user_id:
            user_data = get_user_from_db(user_id)
            admin_status = is_admin(user_id)
        
        if not user_data:
            user_data = {
                "balance": 0.00,
                "level_emoji": "⚪",
                "level_name": "Unranked",
                "total_wagered": 0,
                "total_won": 0,
                "games_played": 0,
                "win_rate": 0
            }
        
        user_data["is_admin"] = admin_status
        
        bot_username = os.getenv("BOT_USERNAME", "GildTesoroCasinoBot")
        
        return jsonify({
            "success": True,
            "user": user_data,
            "bot_username": bot_username
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
