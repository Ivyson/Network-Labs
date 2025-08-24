import socket 
import time
import datetime

server_message = f'Hello, This is the response from the server'
host  ='127.0.0.1' # Host of the server
port = 9999     # Port of my server
data_size = 1042
try:
    with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as Server:
        # Bind the host and associate it to this system, 
        Server.bind((host, port))
        print(f'The Server is running at host:{host} and Port: {port}')
        ## Now we need to start listening
        ## The receiving function will return the IP ADDRESS of the client and the data
        message, IP = Server.recvfrom(data_size)
        print(f'Message from The client : {message.decode('utf-8')}')
        print(f'The IP Address of the Client is: {IP}')
        current_time = datetime.datetime.now()
        string_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        server_message =f'{string_time} '+ server_message
        print(f'The message the client is: {server_message}')
        Server.sendto(server_message.encode('utf-8'), IP)
except socket.error as e:
    print(f'Error occured, Server shutting down ')

