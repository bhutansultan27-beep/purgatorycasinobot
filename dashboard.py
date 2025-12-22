import os
import asyncio
from aiohttp import web
from datetime import datetime

class Dashboard:
    def __init__(self, port=5000):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_get('/', self.home)
        self.app.router.add_get('/status', self.status)
        
    async def home(self, request):
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Gran Tesero Casino Bot</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #fff;
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                .header {
                    text-align: center;
                    padding: 40px 20px;
                }
                .logo {
                    font-size: 48px;
                    margin-bottom: 10px;
                }
                .title {
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }
                .subtitle {
                    font-size: 16px;
                    color: #aaa;
                    margin-bottom: 30px;
                }
                .status-card {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    backdrop-filter: blur(10px);
                }
                .status-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 10px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                .status-item:last-child {
                    border-bottom: none;
                }
                .label {
                    color: #aaa;
                }
                .value {
                    color: #4ade80;
                    font-weight: bold;
                }
                .games-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 15px;
                    margin-top: 30px;
                }
                .game-card {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 15px;
                    text-align: center;
                    transition: all 0.3s ease;
                    cursor: pointer;
                }
                .game-card:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-color: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                }
                .game-emoji {
                    font-size: 32px;
                    margin-bottom: 8px;
                }
                .game-name {
                    font-size: 14px;
                    color: #fff;
                }
                .button {
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 30px;
                    border-radius: 25px;
                    text-decoration: none;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                }
                .button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    margin-top: 40px;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🎰</div>
                    <div class="title">Gran Tesero Casino</div>
                    <div class="subtitle">Telegram Gambling Bot</div>
                </div>
                
                <div class="status-card">
                    <div class="status-item">
                        <span class="label">Bot Status</span>
                        <span class="value">🟢 Online</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Bot Username</span>
                        <span class="value">@emojigamblebot</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Mode</span>
                        <span class="value">Polling</span>
                    </div>
                    <div class="status-item">
                        <span class="label">Uptime</span>
                        <span class="value">Active</span>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <h2 style="margin: 30px 0 20px 0; font-size: 24px;">Available Games</h2>
                </div>
                
                <div class="games-grid">
                    <div class="game-card">
                        <div class="game-emoji">🎲</div>
                        <div class="game-name">Dice</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🎰</div>
                        <div class="game-name">Slots</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🃏</div>
                        <div class="game-name">Blackjack</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🎡</div>
                        <div class="game-name">Roulette</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">💣</div>
                        <div class="game-name">Mines</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🪙</div>
                        <div class="game-name">Coinflip</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🎴</div>
                        <div class="game-name">Baccarat</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🔢</div>
                        <div class="game-name">Keno</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">📉</div>
                        <div class="game-name">Limbo</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">📈</div>
                        <div class="game-name">Hi-Lo</div>
                    </div>
                    <div class="game-card">
                        <div class="game-emoji">🔴</div>
                        <div class="game-name">Connect 4</div>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button class="button" onclick="openTelegram()">Open Bot on Telegram</button>
                </div>
                
                <div class="footer">
                    <p>🚀 Bot is running and listening for messages on Telegram</p>
                    <p style="margin-top: 10px; color: #444;">Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                </div>
            </div>
            
            <script>
                function openTelegram() {
                    window.open('https://t.me/emojigamblebot', '_blank');
                }
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')
    
    async def status(self, request):
        return web.json_response({
            'status': 'online',
            'bot': '@emojigamblebot',
            'mode': 'polling',
            'timestamp': datetime.now().isoformat()
        })
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        print(f"Dashboard started on port {self.port}")
