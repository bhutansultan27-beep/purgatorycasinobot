from http.server import HTTPServer, SimpleHTTPRequestHandler

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>Bot runs on external server</h1>')

if __name__ == '__main__':
    HTTPServer(('0.0.0.0', 5000), Handler).serve_forever()
