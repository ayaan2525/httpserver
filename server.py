import socket
import threading

# server address and port
HOST, PORT = "", 8002

def parse_request(request):
    lines = request.split('\r\n')
    method, path, _ = lines[0].split()
    headers ={}
    for line in lines[1:]:
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    return method, path, headers

def handle_request(client_conn):
    request_data = client_conn.recv(1024).decode("utf-8")
    print(f"received request:\n{request_data}")

    method, path, headers = parse_request(request_data)

    if 'X-Custom-Header' not in headers:
        response_body = """
        <html>
        <body>
        <h1>400 Bad Request</h1>
        <p>X-Custom-Header is required.</p>
        </body>
        </html>
        """
        status_code = "400 Bad Request"

    else:
        if path == '/':
            response_body = """
            <html>
            <head><title>Home</title></head>
            <body>
            <h1>Welcome to the Home Page!</h1>
            </body>
            </html>
            """
            status_code = "200 OK"
        elif path =='/about':
            response_body = """
            <html>
            <head><title>About</title></head>
            <body><h1>About us</h1>
            <p>This is a simple Http server.</p>
            </body>
            </html>
            """
            status_code = "200 OK"
        else:
            response_body = """
            <html>
            <head><title>404 not found</title></head>
            <body><h1>404 not found</h1></body>
            </html>
            """
            status_code = "404 not found"

    http_response = f"""
    HTTP/1.1 {status_code}
    Content-Type:text/html; charset=UTF-8
    Content-Length: {len(response_body)}

    {response_body}
    """
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