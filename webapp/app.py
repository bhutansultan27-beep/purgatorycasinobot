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

LEVEL_TIERS = [
    {"name": "Bronze", "emoji": "🥉", "thresholds": [100, 500, 1000, 2500, 5000]},
    {"name": "Silver", "emoji": "🥈", "thresholds": [10000, 15200, 20500, 26000, 32000]},
    {"name": "Gold", "emoji": "🏆", "thresholds": [39000, 48000, 58000, 69000, 81000]},
    {"name": "Platinum", "emoji": "💎", "thresholds": [94000, 107500, 122000, 138000, 155000]},
    {"name": "Diamond", "emoji": "💠", "thresholds": [173000, 192000, 211500, 232000, 253000]},
    {"name": "Emerald", "emoji": "💚", "thresholds": [275000, 298000, 322000, 347000, 373000]},
    {"name": "Ruby", "emoji": "❤️", "thresholds": [400000, 428000, 457000, 487000, 518000]},
    {"name": "Sapphire", "emoji": "💙", "thresholds": [550000, 583000, 617000, 652000, 688000]},
    {"name": "Amethyst", "emoji": "💜", "thresholds": [725000, 763000, 802000, 842000, 883000]},
    {"name": "Obsidian", "emoji": "🖤", "thresholds": [925000, 968000, 1012000, 1058000, 1107000]},
    {"name": "Mythic", "emoji": "🔮", "thresholds": [1159000, 1213000, 1270000, 1330000, 1393000]},
    {"name": "Legendary", "emoji": "👑", "thresholds": [1458000, 1525000, 1595000, 1668000, 1743000]},
    {"name": "Ethereal", "emoji": "✨", "thresholds": [1850000, 2000000, 2175000, 2400000, 2650000]},
]

def get_user_level(total_wagered):
    current_level = {"name": "Unranked", "emoji": "⚪", "threshold": 0}
    next_level = None
    
    all_levels = []
    for tier in LEVEL_TIERS:
        for i, threshold in enumerate(tier["thresholds"]):
            all_levels.append({
                "name": f"{tier['name']} {['I', 'II', 'III', 'IV', 'V'][i]}",
                "emoji": tier["emoji"],
                "threshold": threshold
            })
    
    for i, level in enumerate(all_levels):
        if total_wagered >= level["threshold"]:
            current_level = level
            if i + 1 < len(all_levels):
                next_level = all_levels[i + 1]
            else:
                next_level = None
        else:
            if current_level["name"] == "Unranked":
                next_level = level
            break
    
    return current_level, next_level

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
                    level, next_level = get_user_level(total_wagered)
                    return {
                        "balance": user.get('balance', 0),
                        "level_emoji": level["emoji"],
                        "level_name": level["name"],
                        "total_wagered": total_wagered,
                        "total_won": user.get('total_pnl', 0) if user.get('total_pnl', 0) > 0 else 0,
                        "games_played": games_played,
                        "win_rate": win_rate
                    }
    except:
        pass
    return None

def get_full_user_from_db(user_id):
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
                    level, next_level = get_user_level(total_wagered)
                    return {
                        "balance": user.get('balance', 0),
                        "level_emoji": level["emoji"],
                        "level_name": level["name"],
                        "current_threshold": level["threshold"],
                        "total_wagered": total_wagered,
                        "total_pnl": user.get('total_pnl', 0),
                        "games_played": games_played,
                        "games_won": games_won,
                        "win_rate": win_rate,
                        "best_win_streak": user.get('best_win_streak', 0),
                        "join_date": user.get('join_date'),
                        "next_level": next_level
                    }
    except:
        pass
    return None

def get_leaderboard_data():
    try:
        if os.path.exists('casino_data.json'):
            with open('casino_data.json', 'r') as f:
                data = json.load(f)
                users = data.get('users', {})
                leaderboard = []
                for user_id, user in users.items():
                    total_wagered = user.get('total_wagered', 0)
                    if total_wagered > 0:
                        level, _ = get_user_level(total_wagered)
                        leaderboard.append({
                            "username": user.get('username', f'User{user_id}'),
                            "total_wagered": total_wagered,
                            "level_emoji": level["emoji"],
                            "level_name": level["name"]
                        })
                leaderboard.sort(key=lambda x: x['total_wagered'], reverse=True)
                return leaderboard[:50]
    except:
        pass
    return []

def get_user_history(user_id):
    try:
        if os.path.exists('casino_data.json'):
            with open('casino_data.json', 'r') as f:
                data = json.load(f)
                games = data.get('games', [])
                user_games = [g for g in games if g.get('user_id') == user_id]
                user_games.reverse()
                return user_games[:50]
    except:
        pass
    return []

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

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/profile', methods=['POST'])
def get_profile():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if user_id:
            profile = get_full_user_from_db(user_id)
            if profile:
                return jsonify({"success": True, "profile": profile})
        
        return jsonify({
            "success": True, 
            "profile": {
                "balance": 0,
                "level_emoji": "⚪",
                "level_name": "Unranked",
                "current_threshold": 0,
                "total_wagered": 0,
                "total_pnl": 0,
                "games_played": 0,
                "games_won": 0,
                "win_rate": 0,
                "best_win_streak": 0,
                "next_level": {"name": "Bronze I", "emoji": "🥉", "threshold": 100}
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        leaderboard = get_leaderboard_data()
        return jsonify({"success": True, "leaderboard": leaderboard})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history', methods=['POST'])
def get_history():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if user_id:
            history = get_user_history(user_id)
            return jsonify({"success": True, "history": history})
        
        return jsonify({"success": True, "history": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

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
