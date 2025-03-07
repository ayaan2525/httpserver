import socket
import threading
import os
import urllib.parse
import logging
import mimetypes
import signal
import time

# server address and port
HOST, PORT = "", 8004
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

logging.basicConfig(filename="server.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
shutdown_event = threading.Event()  # Used for clean shutdown

def log_request(client_addr, method, path, status_code, headers):
    
    # log incoming http request with timestamp, method, path and status

    user_agent = headers.get("user-agent", "unknown")
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    log_entry = f"{timestamp} {client_addr} - {method} {path} - {status_code} - {user_agent}"
    logging.info(log_entry)

def parse_request(request):
    if "\r\n\r\n" in request:
        headers, body = request.split("\r\n\r\n", 1)
    else:
        headers, body = request, ""  # Handle cases where the request has no body
    
    lines = headers.split("\r\n")
    method, full_path, http_version = lines[0].split()

    # Remove query parameters (anything after '?')
    path = full_path.split('?')[0]

    headers = {}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    return method, path, headers, body

def read_file(filepath, mode="r"):
    if os.path.exists(filepath):
        with open(filepath, mode) as file:
            return file.read() if "b" not in mode else file.read()
    return None

""" def get_content_type(path):
    if path.endswith(".html"):
        return "text/html"
    elif path.endswith(".css"):
        return "text/css"
    elif path.endswith(".js"):
        return "application/javascript"
    elif path.endswith(".png"):
        return "image/png"
    elif path.endswith(".jpg") or path.endswith(".jpeg"):
        return "image/jpeg"
    return "application/octet-stream" """

def serve_static_file(path):
    file_path = os.path.join(STATIC_DIR, path[len("/static"):])
    content_type, _ = mimetypes.guess_type(file_path)

    response_body = read_file(file_path, "rb")
    if response_body:
        status_code = "200 OK"
    else:
        response_body = b"<h1>404 Not found</h1>"
        status_code = "404 not found"

    return response_body, status_code, content_type or "application/octet-stream"

def not_found_page():
    return "<h1>404 Not Found</h1>", "404 Not Found"

def handle_form_submission(body):
    post_data = dict(urllib.parse.parse_qsl(body))
    name = post_data.get("name", "Guest")

    response_body = read_file(os.path.join(TEMPLATES_DIR, "success.html"))
    if response_body:
        response_body = response_body.replace("<span id=\"username\"></span>", f"<span>{name}</span>")
    else:
        response_body = "<h1>Form Submission Failed</h1>"
    return response_body, "200 OK"



def home_page():
    return read_file(os.path.join(TEMPLATES_DIR, "index.html")), "200 OK"

def about_page(query=""):
    name = "Guest"

    if query:
        query_dict = dict(urllib.parse.parse_qsl(query))
        name = query_dict.get("name", "Guest")
    return f"<h1>Welcome {name}!</h1>", "200 OK"

def route_request(method, path, body):
    if method == "POST" and path == "/submit":
        return handle_form_submission(body)
    if path.startswith("/static"):
        return serve_static_file(path)

    return routes.get(path, not_found_page)() + ("text/html",)


def handle_request(client_conn, client_addr):
    try:
        request_data = client_conn.recv(1024).decode("utf-8")

        if not request_data.strip():  # Ignore empty requests
            client_conn.close()
            return
        print(f"received request:\n{request_data}")

        method, path, headers, body = parse_request(request_data)
        response_body, status_code, content_type = route_request(method, path, body)

        log_request(client_addr, method, path, status_code, headers)

        # Prepare HTTP response
        http_response = f"HTTP/1.1 {status_code}\r\n"
        http_response += f"Content-Type: {content_type}; charset=UTF-8\r\n"
        http_response += f"Content-Length: {len(response_body) if isinstance(response_body, bytes) else len(response_body.encode('utf-8'))}\r\n"
        http_response += "Connection: close\r\n\r\n"

        if isinstance(response_body, str):
            response_body = response_body.encode("utf-8")
        
        client_conn.sendall(http_response.encode("utf-8") + response_body)
    except Exception as e:
        logging.error(f"Error handling request: {e}")
    finally:
        client_conn.close()

routes = {
    "/": home_page,
    "/about": about_page,  # Updated to support query parameter
}

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"listening on port {PORT}. Press crl+c to stop")

    def shutdown_server(signal_received, frame):
        print("\nShutdwon server gracefully")
        shutdown_event.set(5)
        server_socket.close()
        os._exit(0)
    signal.signal(signal.SIGINT, shutdown_server)

    try:
        while not shutdown_event.is_set():
            client_conn, client_addr = server_socket.accept()
            print(f"new connection from {client_addr}")

            client_thread = threading.Thread(target=handle_request, args=(client_conn, client_addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer is shutting down...")
    finally:
        server_socket.close()
        print("Server closed successfully")

if __name__ == "__main__":
    run_server()