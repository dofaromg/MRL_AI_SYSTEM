"""Loopback-only fixture for the real URLSession file-upload test."""
import base64
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', '0'))
        if self.path != '/api/scans/upload' or not 0 < length < 1024 * 1024:
            self.send_error(400)
            return
        payload = self.rfile.read(length)
        message = BytesParser(policy=policy.default).parsebytes(
            ('Content-Type: ' + self.headers['Content-Type'] + '\r\nMIME-Version: 1.0\r\n\r\n').encode('ascii') + payload)
        files = [{'name': part.get_param('name', header='content-disposition'),
                  'filename': part.get_filename(),
                  'data': base64.b64encode(part.get_payload(decode=True)).decode('ascii')}
                 for part in message.iter_parts()]
        scan_id = self.headers.get('X-MRL-Scan-ID')
        receipt = {'scanId': scan_id, 'scanName': self.headers.get('X-MRL-Scan-Name'),
                   'length': length, 'files': files}
        (root / 'received.json').write_text(json.dumps(receipt))
        response = json.dumps({'ok': True, 'scanId': scan_id, 'uploaded': len(files),
                               'manifestPath': 'manifest.json'}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, *_):
        pass


server = HTTPServer(('127.0.0.1', 0), Handler)
(root / 'port').write_text(str(server.server_port))
server.serve_forever()
