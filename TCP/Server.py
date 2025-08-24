import socket
import threading
import time # Import time

host = '127.0.0.1'
port = 9999

def handle_client(client_socket, address):
    """Handles communication with a single client."""
    print(f'Connected to client {address}')
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                print(f'Client {address} disconnected')
                break

            try:
                decoded_data = data.decode('utf-8')
                print(f'Received message from {address}: {decoded_data}')

                # Simulate a time-consuming operation
                print(f"Processing client {address} for 3 seconds...")
                time.sleep(3) # Simulate some work
                print(f"Finished processing client {address}")


                sent_message = f'Server Received: {decoded_data}'
                client_socket.sendall(sent_message.encode('utf-8'))
                print(f'Sent response to {address}')

            except UnicodeDecodeError as e:
                print(f'Error decoding data from {address}: {e}')
                break

    except socket.error as e:
        print(f'Socket error with client {address}: {e}')

    except Exception as e:
        print(f'An unexpected error occurred with client {address}: {e}')

    finally:
        print(f'Closing connection with {address}')
        client_socket.close()

def main():
    """Main function to start the server and handle connections."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as Server:
            Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            Server.bind((host, port))

            print(f'Server about to initialize a connection...')
            Server.listen(5)
            print(f'Server waiting on {host}:{port}...')

            while True:
                Client, address = Server.accept()
                client_thread = threading.Thread(target=handle_client, args=(Client, address))
                client_thread.start()

    except socket.error as e:
        print(f'Socket error: {e}')
    except KeyboardInterrupt:
        print('Server shutting down.')
    except Exception as e:
        print(f'An unexpected error occurred: {e}')

if __name__ == "__main__":
    main()
