import socket
import json
import os
import threading
from datetime import datetime

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
FILES_DIR = 'files'
DEFAULT_USER = 'student'
DEFAULT_PASSWORD = '1234'

file_operation_history = {}
history_lock = threading.Lock()


def ensure_files_dir():
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
        print(f"+ Directory '{FILES_DIR}' created")


def authenticate(username, password):
    return username == DEFAULT_USER and password == DEFAULT_PASSWORD


def add_to_history(filename, operation, user):
    with history_lock:
        if filename not in file_operation_history:
            file_operation_history[filename] = []
        
        entry = {
            'operation': operation,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user': user
        }
        file_operation_history[filename].append(entry)
        print(f"History updated for '{filename}': {operation} by {user}")


def handle_client(conn, addr):
    print(f"\nClient connected from {addr}")
    authenticated = False
    current_user = None
    
    try:
        while True:
            request_data = conn.recv(4096).decode('utf-8')
            if not request_data:
                break
            
            try:
                request = json.loads(request_data)
                command = request.get('command')
                
                print(f"Command received: {command}")
                
                if command == 'login':
                    username = request.get('username')
                    password = request.get('password')
                    
                    if authenticate(username, password):
                        authenticated = True
                        current_user = username
                        response = {
                            'status': 'success',
                            'message': f'Welcome {username}!'
                        }
                        print(f"+ User {username} authenticated")
                    else:
                        response = {
                            'status': 'error',
                            'message': 'Invalid credentials'
                        }
                        print(f"- Authentication failed for user {username}")
                
                elif not authenticated:
                    response = {
                        'status': 'error',
                        'message': 'Not authenticated. Use login first'
                    }
                
                elif command == 'create_file':
                    filename = request.get('filename')
                    content = request.get('content', '')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    add_to_history(filename, 'create', current_user)
                    
                    response = {
                        'status': 'success',
                        'message': f'File {filename} created on server'
                    }
                    print(f"+ File created: {filename}")
                
                elif command == 'upload':
                    filename = request.get('filename')
                    content = request.get('content')
                    
                    filepath = os.path.join(FILES_DIR, filename)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    
                    add_to_history(filename, 'upload', current_user)
                    
                    response = {
                        'status': 'success',
                        'message': f'File {filename} uploaded'
                    }
                    print(f"+ File uploaded: {filename}")
                
                elif command == 'rename_file':
                    old_name = request.get('old_name')
                    new_name = request.get('new_name')
                    
                    old_path = os.path.join(FILES_DIR, old_name)
                    new_path = os.path.join(FILES_DIR, new_name)
                    
                    if not os.path.exists(old_path):
                        response = {
                            'status': 'error',
                            'message': f'File "{old_name}" not found on server'
                        }
                    elif os.path.exists(new_path):
                        response = {
                            'status': 'error',
                            'message': f'File "{new_name}" already exists on server'
                        }
                    else:
                        os.rename(old_path, new_path)
                        
                        with history_lock:
                            if old_name in file_operation_history:
                                file_operation_history[new_name] = \
                                    file_operation_history.pop(old_name)
                        
                        add_to_history(
                            new_name,
                            f'rename (from "{old_name}" to "{new_name}")',
                            current_user
                        )
                        
                        response = {
                            'status': 'success',
                            'message': f'File renamed from "{old_name}" to "{new_name}"'
                        }
                        print(f"+ File renamed: {old_name} -> {new_name}")
                
                elif command == 'read_file':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)
                    
                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f'File "{filename}" not found on server'
                        }
                    else:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        add_to_history(filename, 'read', current_user)
                        
                        response = {
                            'status': 'success',
                            'message': f'File "{filename}" read successfully',
                            'content': content
                        }
                        print(f"+ File read: {filename}")
                
                elif command == 'download':
                    filename = request.get('filename')
                    filepath = os.path.join(FILES_DIR, filename)
                    
                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f'File "{filename}" not found on server'
                        }
                    else:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        add_to_history(filename, 'download', current_user)
                        
                        response = {
                            'status': 'success',
                            'message': f'File "{filename}" ready for download',
                            'filename': filename,
                            'content': content
                        }
                        print(f"+ File downloaded: {filename}")
                
                elif command == 'edit_file':
                    filename = request.get('filename')
                    new_content = request.get('content', '')
                    filepath = os.path.join(FILES_DIR, filename)
                    
                    if not os.path.exists(filepath):
                        response = {
                            'status': 'error',
                            'message': f'File "{filename}" not found on server'
                        }
                    else:
                        with open(filepath, 'w') as f:
                            f.write(new_content)
                        
                        add_to_history(filename, 'edit', current_user)
                        
                        response = {
                            'status': 'success',
                            'message': f'File "{filename}" edited successfully'
                        }
                        print(f"+ File edited: {filename}")
                
                elif command == 'see_file_operation_history':
                    filename = request.get('filename')
                    
                    with history_lock:
                        history = file_operation_history.get(filename, [])
                    
                    if not history:
                        response = {
                            'status': 'success',
                            'message': f'No history found for file "{filename}"',
                            'history': []
                        }
                    else:
                        response = {
                            'status': 'success',
                            'message': f'History for file "{filename}"',
                            'history': history
                        }
                    print(f"+ History requested for: {filename}")
                
                elif command == 'list_files':
                    files = os.listdir(FILES_DIR)
                    response = {
                        'status': 'success',
                        'files': files
                    }
                    print(f"+ Files listed: {len(files)} files found")
                
                elif command == 'logout':
                    authenticated = False
                    current_user = None
                    response = {
                        'status': 'success',
                        'message': 'Logged out successfully'
                    }
                    print(f"+ User logged out")
                
                else:
                    response = {
                        'status': 'error',
                        'message': f'Unknown command: {command}'
                    }
            
            except Exception as e:
                response = {'status': 'error', 'message': str(e)}
                print(f"- Error: {str(e)}")
            
            conn.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        print(f"- Connection error: {str(e)}")
    finally:
        conn.close()
        print(f"Client disconnected from {addr}")


def start_server():
    ensure_files_dir()
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    
    print("=" * 60)
    print("FTP SERVER STARTED")
    print("=" * 60)
    print(f"Host: {SERVER_HOST}")
    print(f"Port: {SERVER_PORT}")
    print(f"Files Directory: {FILES_DIR}")
    print(f"Default User: {DEFAULT_USER}")
    print(f"Default Password: {DEFAULT_PASSWORD}")
    print("=" * 60)
    
    try:
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(conn, addr)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == '__main__':
    start_server()