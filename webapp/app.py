from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

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
        return jsonify({
            "success": True,
            "user": {
                "balance": 1000.00,
                "level_emoji": "⚪",
                "level_name": "Unranked",
                "total_wagered": 0,
                "total_won": 0,
                "games_played": 0,
                "win_rate": 0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
