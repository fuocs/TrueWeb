# server.py – Minimal Localhost Bridge
from flask import Flask, request, jsonify

server = Flask(__name__)
TOKEN = 'dev-token'  # must match LOCALHOST_TOKEN in your extension
HOST = '127.0.0.1'
PORT = 38999

link_callback = None 
analyzed_urls = set()  # Track URLs that have been analyzed

def set_callback(func):
    """Set callback function to be called when URL is received from extension"""
    global link_callback
    link_callback = func

@server.get('/health')
def health():
    return jsonify({'ok': True})

@server.post('/download')
def download():
    if request.headers.get('X-Auth') != TOKEN:
        return jsonify({'ok': False, 'error': 'unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'ok': False, 'error': 'missing url'}), 400

    # Check if URL has already been analyzed
    if url in analyzed_urls:
        print(f"[LocalServer] URL already analyzed: {url}")
        return jsonify({'ok': False, 'error': 'duplicate', 'message': 'You cannot scan the same link twice! Close the analysis window to scan again.'}), 409
    
    print(f"[LocalServer] Received URL from extension: {url}")
    analyzed_urls.add(url)  # Mark URL as analyzed
    
    if link_callback:
        link_callback(url)

    return jsonify({'ok': True, 'url': url, 'message': 'Analysis started'})

def run():
    # Enable threaded mode to handle multiple requests simultaneously
    # Add request timeout and connection handling settings
    from werkzeug.serving import make_server
    import logging
    
    # Suppress Flask debug output
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    print(f"[LocalServer] Starting server on {HOST}:{PORT}")
    
    try:
        # Create server with timeout settings
        srv = make_server(
            HOST, 
            PORT, 
            server,
            threaded=True,
            request_handler=None  # Use default handler with proper timeout
        )
        
        # Set socket timeout (30 seconds)
        srv.socket.settimeout(30)
        
        print(f"[LocalServer] Server ready - listening for extension requests")
        srv.serve_forever()
    except Exception as e:
        print(f"[LocalServer] Error starting server: {e}")
        # Fallback to simple run
        server.run(HOST, PORT, debug=False, threaded=True)