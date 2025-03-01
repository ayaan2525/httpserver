import socket
import threading
import os

# server address and port
HOST, PORT = "", 8000
TEMPLATES_DIR = "templates"

def parse_request(request):
    lines = request.split('\r\n')
    method, full_path, http_version = lines[0].split()

    # Remove query parameters (anything after '?')
    path = full_path.split('?')[0]

    headers ={}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    return method, path, headers

def read_html_files(filename):
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    return None

def handle_request(client_conn):
    request_data = client_conn.recv(1024).decode("utf-8")
    print(f"received request:\n{request_data}")

    method, path, headers = parse_request(request_data)

    if path == '/':
        response_body = read_html_files("index.html")
        status_code = "200 OK" if response_body else "404 Not found"
    elif path =='/about':
        response_body = read_html_files("about.html")
        status_code = "200 OK" if response_body else "404 Not found"
    else:
        response_body = "<h1> 404 Not found</h1>"
        status_code = "404 not found"

    http_response = f"HTTP/1.1 {status_code}\r\n"
    http_response += "Content-Type: text/html; charset=UTF-8\r\n"
    http_response += f"Content-Length: {len(response_body)}\r\n"
    http_response += "Connection: close\r\n\r\n"  # Correct HTTP format
    http_response += response_body  # Append the actual content

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