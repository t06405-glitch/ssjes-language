# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import time
import re
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

SITE_DIR = r"E:\教務處\07_母語日教學活動\新庄國小本土語言網站"
CLOUDFLARED_BIN = os.path.join(SITE_DIR, "cloudflared.exe")
PORT = 8080

# Check port availability
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

if is_port_in_use(PORT):
    PORT = 8088

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

def run_http_server():
    server = HTTPServer(('127.0.0.1', PORT), CustomHandler)
    print(f"Local HTTP server running at: http://127.0.0.1:{PORT}/")
    server.serve_forever()

# Start HTTP server thread
t = threading.Thread(target=run_http_server, daemon=True)
t.start()
time.sleep(1)

# Start Cloudflare Tunnel
print(f"Connecting to Cloudflare Quick Tunnel for port {PORT}...")
cmd = [CLOUDFLARED_BIN, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding='utf-8')

public_url = None
start_time = time.time()

with open(os.path.join(SITE_DIR, "tunnel_url.txt"), "w", encoding="utf-8") as url_file:
    while time.time() - start_time < 30:
        line = proc.stdout.readline()
        if not line:
            break
        # Look for trycloudflare.com URL
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            public_url = match.group(0)
            url_file.write(public_url + "\n")
            url_file.flush()
            print("\n" + "="*60)
            print("【網站發布成功！】")
            print(f"公開分享網址 (任何裝置皆可連線)： {public_url}")
            print(f"本機專屬預覽網址： http://127.0.0.1:{PORT}/")
            print("="*60 + "\n")
            break

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    proc.terminate()
