import http.server
import socketserver
import json
import urllib.parse
import os

# scser - Cloud Variable & WebSockets/HTTP Relay Server for TurboWarp / PenguinMod / Packager
# Ready for direct deployment on Render via GitHub repository.

ROOMS = {}

class ScserHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        project_id = params.get('project_id', ['default'])[0]

        if parsed.path in ['/poll', '/get', '/cloud']:
            room_data = ROOMS.get(project_id, {})
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "ok",
                "project_id": project_id,
                "vars": room_data
            }).encode('utf-8'))
        elif parsed.path == '/':
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "server": "scser",
                "status": "online",
                "endpoint": "https://scser.com",
                "message": "Ready for TurboWarp and PenguinMod Packager Cloud Variables"
            }).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint Not Found"}).encode('utf-8'))

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else ""
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        parsed = urllib.parse.urlparse(self.path)
        project_id = str(data.get('project_id', data.get('project', 'default')))

        if project_id not in ROOMS:
            ROOMS[project_id] = {}

        method = data.get('method', 'set')

        if method == 'handshake' or parsed.path == '/handshake':
            self._set_headers(200)
            self.wfile.write(json.dumps({
                "status": "ok",
                "method": "handshake",
                "project_id": project_id,
                "vars": ROOMS[project_id]
            }).encode('utf-8'))
            return

        var_name = data.get('name')
        var_val = data.get('value')
        vars_dict = data.get('vars')

        if var_name is not None:
            ROOMS[project_id][var_name] = var_val

        if isinstance(vars_dict, dict):
            for k, v in vars_dict.items():
                ROOMS[project_id][k] = v

        self._set_headers(200)
        self.wfile.write(json.dumps({
            "status": "ok",
            "project_id": project_id,
            "vars": ROOMS[project_id]
        }).encode('utf-8'))

    def log_message(self, format, *args):
        return

def run():
    port = int(os.environ.get('PORT', 10000))
    server_address = ('', port)
    httpd = socketserver.TCPServer(server_address, ScserHandler)
    print(f"scser server is running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()