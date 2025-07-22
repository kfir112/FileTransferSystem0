import threading
import socket
import os
import atexit

mutex = threading.Lock()

SERVER_FOLDER= os.path.join(os.path.expanduser("~"),"OneDrive" ,"Desktop","daserver")
os.makedirs(SERVER_FOLDER, exist_ok=True)



def create_server_socket():
    new_socket= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    new_socket.bind(("127.0.0.1",1337))
    new_socket.listen(2)
    print("waiting for connections...")
    return new_socket

def accept_client(server_socket):
    client_socket,client_adress=server_socket.accept()
    print(f"client connected: {client_adress}")
    return client_socket


def handle_client(client_socket):
    try:
        send_filenames(client_socket)
        while True:
            buffer = b""
            while True:
                data = client_socket.recv(1024)
                if not data:
                    print("client disconnected")
                    client_socket.close()
                    return
                print("got 1024 bytes")
                buffer +=data
                if b"__UPLOADNAME__" in buffer:
                    split_buffer=buffer.split(b"__UPLOADNAME__")
                    file_name=split_buffer[0].decode()
                    start_of_file_content=split_buffer[1]
                    with mutex:
                        download_file_from_client(client_socket,file_name,start_of_file_content)
                    break
                elif b"__DOWNLOADNAME__" in buffer:
                    file_name=buffer.split(b"__DOWNLOADNAME__")[0].decode()
                    upload_file_to_client(client_socket,file_name)
                    break
    except (ConnectionError,ConnectionResetError, BrokenPipeError, OSError) as e:
        print(f"Client connection lost: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        client_socket.close()
        print("Closed client socket.")


def download_file_from_client(client_socket,file_name,content_beggining):
    buffer=content_beggining
    with open(os.path.join(SERVER_FOLDER,file_name),'wb') as file:
        while True:
            if b"__END__" in buffer:
                file_content=buffer.split(b"__END__")[0]
                file.write(file_content)
                print("file upload done.")
                return
            data = client_socket.recv(1024)
            if not data:
                print("connection/communication with client closed")
                raise ConnectionError("Client disconnected during his file upload")
            buffer+=data
            print("received 1024 bytes..")

def upload_file_to_client(client_socket,file_name):
    full_path = os.path.join(SERVER_FOLDER, file_name)
    if not os.path.exists(full_path):
        client_socket.send(b"__END__") 
        return
    with open(os.path.join(SERVER_FOLDER,file_name),"rb") as file:
        while True:
            data=file.read(1024)
            if not data:
                client_socket.send(b"__END__")
                print("file upload finished.")
                break
            print("sending 1024 bytes..")
            client_socket.send(data)


def send_filenames(client_socket):
    for _, _, files in os.walk(SERVER_FOLDER):
            for file in files:
                client_socket.send(file.encode()+b"\n")
    client_socket.send(b"__END__")


def cleanup(threads):
    print("Shutting down...")
    try:
        server_socket.close()
    except Exception as e:
        print(e)
    if not threads:
        return
    threads[:]= [t for t in threads if t.is_alive()]
    for t in threads:
        t.join()
    print("Server cleanly shut down.")            


if __name__=="__main__":
    server_socket=create_server_socket()
    threads_list=[]
    atexit.register(cleanup, threads_list)
    while True:
        client_socket=accept_client(server_socket)
        client_thread=threading.Thread(target=handle_client,args=(client_socket,))
        client_thread.start()
        threads_list.append(client_thread)
