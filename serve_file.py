from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def do_GET(self):
        files = {
            '/main.py': 'main.py',
            '/requirements.txt': 'requirements.txt',
            '/blackjack.py': 'blackjack.py',
            '/database.py': 'database.py',
            '/webhook_server.py': 'webhook_server.py',
        }
        
        if self.path in files:
            filename = files[self.path]
            if os.path.exists(filename):
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                with open(filename, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head><title>Gild Tesoro Casino Bot - File Server</title></head>
<body style="font-family: Arial; padding: 20px; background: #1a1a2e; color: #eee;">
<h1>Gild Tesoro Casino Bot</h1>
<p>This server hosts the bot files for download to your external server.</p>
<h2>Available Files:</h2>
<ul>
<li><a href="/main.py">main.py</a></li>
<li><a href="/requirements.txt">requirements.txt</a></li>
<li><a href="/blackjack.py">blackjack.py</a></li>
<li><a href="/webhook_server.py">webhook_server.py</a></li>
</ul>
<p><em>Bot runs on external Webdock server at casino.vps.webdock.cloud</em></p>
</body>
</html>"""
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('0.0.0.0', port), CORSHandler)
    print(f"File server running on port {port}")
    server.serve_forever()
