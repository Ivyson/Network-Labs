import socket

host = '192.168.24.87'# IP adress of the server
port = 9999# The port of the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Client:
    Client.connect((host, port))
    message = f'Sam is saying Hi'
    Client.sendall((message.encode('utf-8'))) # Send a message to the Server
    data = Client.recv(1024)
    if  data:
        decoded_message = data.decode('utf-8')
        print(f'The Server sent back the message {decoded_message}')

