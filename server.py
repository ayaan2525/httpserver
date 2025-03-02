import socket
import threading
import os
import urllib.parse

# server address and port
HOST, PORT = "", 8000
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"

def parse_request(request):
    if "\r\n\r\n" in request:
        headers, body = request.split("\r\n\r\n", 1)
    else:
        headers, body = request, ""  # Handle cases where the request has no body
    lines = headers.split('\r\n')
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
            return file.read()
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

def handle_request(client_conn):
    request_data = client_conn.recv(1024).decode("utf-8")
    print(f"received request:\n{request_data}")

    method, path, headers, body = parse_request(request_data)

    if method == "POST" and path == "/submit":
        post_data = dict(urllib.parse.parse_qsl(body))
        name = post_data.get("name", "Guest")

        response_body = read_file(os.path.join(TEMPLATES_DIR, "success.html"))
        response_body = response_body.replace("<span id=\"username\"></span>", f"<span>{name}</span>")

        status_code = "200 OK"

    elif path.startswith("/static"):
        file_path = os.path.join(STATIC_DIR, path[len("/static/"):])
        content_type = "text/plain"

        if path.endswith(".css"):
            content_type = "text/css"
        elif path.endswith(".js"):
            content_type = "application/javascript"
        elif path.endswith(".png"):
            content_type = "image/png"

        response_body = read_file(file_path, "rb")
        if response_body:
            status_code = "200 OK"
        else:
            response_body = "<h1>404 Not Found</h1>".encode("utf-8")
            status_code = "404 Not Found"

        client_conn.sendall(f"HTTP/1.1 {status_code}\r\nContent-Type: {content_type}\r\n\r\n".encode("utf-8") + response_body)
        client_conn.close()
        return
    elif path == "/":
        response_body = read_file(os.path.join(TEMPLATES_DIR, "index.html"))
        status_code = "200 OK" if response_body else "404 Not Found"
    elif path == "/about":
        response_body = read_file(os.path.join(TEMPLATES_DIR, "about.html"))
        status_code = "200 OK" if response_body else "404 Not Found"

    else:
        response_body = "<h1>404 Not Found</h1>"
        status_code = "404 Not Found"

    # Prepare HTTP response
    http_response = f"HTTP/1.1 {status_code}\r\n"
    http_response += "Content-Type: text/html; charset=UTF-8\r\n"
    http_response += f"Content-Length: {len(response_body.encode('utf-8'))}\r\n"
    http_response += "Connection: close\r\n\r\n"
    http_response += response_body

    client_conn.sendall(http_response.encode("utf-8"))
    client_conn.close()

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"listening on port {PORT}")

    while True:
        client_conn, client_addr = server_socket.accept()
        print(f"new connection from {client_addr}")

        client_thread = threading.Thread(target=handle_request, args=(client_conn,))
        client_thread.start()

if __name__ == "__main__":
    run_server()