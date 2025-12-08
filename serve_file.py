from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
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
            html = "<h1>Casino Bot Files</h1><ul>"
            for path in files:
                html += f'<li><a href="{path}">{path}</a></li>'
            html += "</ul>"
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = 5000
    server = HTTPServer(('0.0.0.0', port), CORSHandler)
    print(f"Serving files on port {port}")
    server.serve_forever()
