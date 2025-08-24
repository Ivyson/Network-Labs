import socket


Host = '127.0.0.1' # Local host
port =  9999
message = 'Hey, This is the client, Hello!!!'
address_server = (Host, port)
try:
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as Client:
        # A client just has to send data
        Client.sendto(message.encode('utf-8'), address_server)
        Message_server = Client.recvfrom(1024)
        print(f'The message form the server: {Message_server[0].decode('utf-8')}')
except socket.error as e:
    print(f'error occured: {e}.')
