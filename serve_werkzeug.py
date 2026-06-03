#!/usr/bin/env python3
"""Serve static files using Werkzeug — same server as TensorBoard, passes corporate proxy."""
import os
import sys

from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response
from werkzeug.utils import send_file


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8194

MIME_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.json': 'application/json',
}


@Request.application
def app(request):
    path = request.path.lstrip('/')
    if not path or path.endswith('/'):
        path += 'index.html'

    file_path = os.path.join(DIRECTORY, path)
    if not os.path.isfile(file_path):
        return Response('Not Found', status=404, content_type='text/plain')

    ext = os.path.splitext(file_path)[1].lower()
    content_type = MIME_TYPES.get(ext, 'application/octet-stream')

    with open(file_path, 'rb') as f:
        data = f.read()

    resp = Response(data, content_type=content_type)
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['Content-Encoding'] = 'identity'
    resp.headers['Expires'] = '0'
    resp.headers['Cache-Control'] = 'no-cache, must-revalidate'
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self';"
        "font-src 'self' data:;"
        "frame-src 'self';"
        "img-src 'self' data: blob:;"
        "object-src 'none';"
        "style-src 'self' 'unsafe-inline';"
        "connect-src 'self';"
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
    )
    return resp


if __name__ == '__main__':
    print(f"Serving {DIRECTORY} on http://0.0.0.0:{PORT}")
    run_simple('0.0.0.0', PORT, app, threaded=True)
