#!/usr/bin/env python3
"""Simple HTTP server with layout save API."""
import http.server
import socketserver
import os
import sys
import json
import re
import subprocess
import threading

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(DIRECTORY, 'index.html')

def rewrite_default_layout(layout_json):
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    # Convert JSON layout to JS source
    js_src = json.dumps(layout_json, ensure_ascii=False, indent=4)
    # JSON uses null/true/false, JS uses null/true/false — same, but keys need no quotes in our style
    # Actually keep JSON style (quoted keys) — it's valid JS
    pattern = r'(const DEFAULT_LAYOUT = )\[.*?\n\];'
    replacement = f'const DEFAULT_LAYOUT = {js_src};'
    new_content, count = re.subn(pattern, replacement, content, count=1, flags=re.DOTALL)
    if count == 0:
        return False
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    threading.Thread(target=git_push, daemon=True).start()
    return True

def git_push():
    env = os.environ.copy()
    env['https_proxy'] = 'http://cmcproxy:WvUBhef4bQ@10.251.112.50:8128'
    subprocess.run(['git', 'add', 'index.html'], cwd=DIRECTORY)
    subprocess.run(['git', 'commit', '-m', 'auto: sync layout from browser'], cwd=DIRECTORY)
    subprocess.run(['git', 'push'], cwd=DIRECTORY, env=env)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/save-layout':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                layout = json.loads(body)
                if rewrite_default_layout(layout):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"ok":true}')
                else:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"error":"pattern not found"}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def version_string(self):
        return "nginx/1.24.0"

    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving {DIRECTORY} on port {PORT}")
    httpd.serve_forever()
