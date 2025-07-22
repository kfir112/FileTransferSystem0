import tkinter as tk
from tkinter import messagebox
import os
import socket

class FileTransferApp():
    def __init__(self,root,client_socket,client_folder):
        self.CLIENT_FOLDER=client_folder
        self.client_socket=client_socket
        self.root=root
        self.root.title("File |Upload+Download| System")


        self.client_listbox = tk.Listbox(self.root,width=40)
        self.server_listbox = tk.Listbox(self.root,width=40)

        self.client_listbox.grid(row=1,column=0,padx=10,pady=10)
        self.server_listbox.grid(row=1,column=2,padx=10,pady=10)

        tk.Label(root,text="Client Files").grid(row=0,column=0)
        tk.Label(root,text="Server Files").grid(row=0,column=2)
        self.list_files()

        self.upload_button=tk.Button(self.root,text="Upload to Server",command=self.upload_file)
        self.upload_button.grid(row=2,column=0,pady=5)
        
        self.download_button= tk.Button(self.root,text="Download To Client",command=self.download_file)
        self.download_button.grid(row=2,column=2,pady=5)

        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    

    def list_files(self):
        for file in self.receive_filenames(self.client_socket):
            self.server_listbox.insert(0,file)
        
        for file in os.listdir(self.CLIENT_FOLDER):
            self.client_listbox.insert(0,file)

    def receive_filenames(self,client_socket):
        file_names=""
        while True:
            data=client_socket.recv(1024)
            if not data:
                print("Server closed connection.")
                messagebox.showerror("Disconnected", "Server closed the connection.")
                client_socket.close()
                self.root.destroy()
                return
            file_names+=data.decode()
            if "__END__" in file_names:
                print("Done receiving file names")
                break
        file_names= file_names.split("\n")
        file_names.pop()
        return file_names


    def download_file(self):
        selected_index_tuple=self.server_listbox.curselection()
        if not selected_index_tuple:
            messagebox.showwarning("No File Selected","select a file from server to download")
            return
        file_name=self.server_listbox.get(selected_index_tuple[0])
        self.download_button.config(state="disabled")
        try:
            self.send_filename_download(self.client_socket,file_name)
            print(f"downloading {file_name}")
            buffer=b""
            with open(os.path.join(self.CLIENT_FOLDER, file_name),'wb') as file:
                while True:
                    data = self.client_socket.recv(1024)
                    buffer+=data
                    if b"__END__" in buffer:
                        file_content=buffer.split(b"__END__")[0]
                        if not file_content:
                            messagebox.showerror("Error",f"File: {file_name} not found in server / file is empty.")
                            self.server_listbox.delete(selected_index_tuple[0])
                            return
                        file.write(file_content)
                        print("file download done.")
                        messagebox.showinfo("Download Finished", f"Finished Downloading {file_name}...")
                        break
                    elif not data:
                        print("Server closed connection.")
                        messagebox.showerror("Disconnected", "Server closed the connection.")
                        client_socket.close()
                        self.root.destroy()
                        return
                    print("received 1024 bytes..")
            if file_name not in self.client_listbox.get(0,"end"):
                self.client_listbox.insert(0,file_name)
        except (ConnectionResetError, BrokenPipeError, OSError) as e: 
            print(f"Socket error: {e}")
            messagebox.showerror("Disconnected", "Lost connection to server.")
            self.client_socket.close()
            self.root.destroy()
            return
        except Exception as e:
            print(f"Something unexpected happened: {e}")
            messagebox.showerror("Error",f"Something unexpected happened: {e}")
        finally:
            self.download_button.config(state="normal")
        

    def send_filename_download(self,client_socket,file_name):
        client_socket.send(f"{file_name}__DOWNLOADNAME__".encode())


    def upload_file(self):
        try:
            selected_index_tuple=self.client_listbox.curselection()
            if not selected_index_tuple:
                messagebox.showwarning("No File Selected","Select a file from client to upload")
                return
            file_name=self.client_listbox.get(selected_index_tuple[0])
            self.send_filename_upload(self.client_socket,file_name)
            if not os.path.exists(os.path.join(self.CLIENT_FOLDER, file_name)):
                messagebox.showwarning("Error",f"file doesnt exist: {os.path.join(self.CLIENT_FOLDER, file_name)}")
                return
            self.upload_button.config(state="disabled")
            print(f"Uploading {file_name}")
            with open(os.path.join(self.CLIENT_FOLDER, file_name),"rb") as file:
                while True:
                    data=file.read(1024)
                    if not data:
                        self.client_socket.send(b"__END__")
                        print("file upload finished.")
                        messagebox.showinfo("Upload", f"Finished uploading {file_name}...")
                        break
                    print("sending 1024 bytes..")
                    self.client_socket.send(data)
            print(f"Done uploading {file_name}")
            if file_name not in self.server_listbox.get(0,"end"):
                self.server_listbox.insert(0,file_name)
        except (ConnectionResetError, BrokenPipeError, OSError) as e: 
            print(f"Socket error: {e}")
            messagebox.showerror("Disconnected", "Lost connection to server.")
            self.client_socket.close()
            self.root.destroy()
            return
        except Exception as e:
            print(f"Something unexpected happened: {e}")
            messagebox.showerror("Error",f"Something unexpected happened: {e}")
        finally:
            self.upload_button.config(state="normal")


    def send_filename_upload(self,client_socket,file_name):  
        client_socket.send(f"{file_name}__UPLOADNAME__".encode())

    def on_close(self):
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.client_socket.close()
        self.root.destroy()


def create_client_socket():
    try:
        new_socket= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        new_socket.connect(("127.0.0.1",1337))
        print("Client connected..")
        return new_socket
    except ConnectionRefusedError:
        print("Server is not up/available")



if __name__=="__main__":
    root = tk.Tk()
    CLIENT_FOLDER=os.path.join(os.path.expanduser("~"),"OneDrive","Desktop", "daclient")
    os.makedirs(CLIENT_FOLDER, exist_ok=True)
    client_socket=create_client_socket()
    app=FileTransferApp(root,client_socket,CLIENT_FOLDER)
