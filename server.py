import socket

# server address and port
HOST, PORT = "", 8000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Listening on port {PORT}")

while True:
    client_conn, client_addr = server_socket.accept()
    request_data = client_conn.recv(1024)
    print(request_data.decode("utf-8"))
    response_body = """
    <html>
    <head>
    <title>Hello</title>
    </head>
    <body>
    <h1>Hello, Networking World!</h1>
    </body>
    </html>
    """
    http_response = f"""
    HTTP/1.1 200 OK
    Content-Type: text/html; charset=UTF-8
    Content-Lenght: {len(response_body)}

    {response_body}
    """
    client_conn.sendall(http_response.encode("utf-8"))
    client_conn.close()