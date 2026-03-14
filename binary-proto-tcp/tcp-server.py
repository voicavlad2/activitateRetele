import socket
import threading
import collections
import pickle
import io

HOST = "127.0.0.1"  
PORT = 3333  

is_running = True
BUFFER_SIZE = 8

class Response:
  def __init__(self, payload):
    self.payload = payload

class Request:
  def __init__(self, command, key, resource = None):
    self.command = command
    self.key = key
    self.resource = resource

class State:
  def __init__(self):
    self.resources = {}
    self.lock = threading.Lock()

  def add(self, key, resource):
    with self.lock:
      self.resources[key] = resource
    return "OK record add"

  def remove(self, key):
    with self.lock:
      if key in self.resources:
        del self.resources[key]
        return "OK value deleted"
      return "ERROR invalid key"

  def get(self, key):
    with self.lock:
      if key in self.resources:
        return f"DATA {self.resources[key]}"
      return "ERROR invalid key"

  def list(self):
    with self.lock:
      if not self.resources:
        return "DATA|"
      items = ",".join(f"{k}={v}" for k,v in self.resources.items())
      return f"DATA|{items}"

  def count(self):
    with self.lock:
      return f"DATA {len(self.resources)}"

  def clear(self):
    with self.lock:
      self.resources.clear()
    return "all data deleted"

  def update(self, key, value):
    with self.lock:
      if key in self.resources:
        self.resources[key] = value
        return "Data updated"
      return "ERROR invalid key"

  def pop(self, key):
    with self.lock:
      if key in self.resources:
        value = self.resources.pop(key)
        return f"DATA {value}"
      return "ERROR invalid key"
state = State()

def process_command(data):
  payload = data[1:]
  stream = io.BytesIO(payload)
  request = pickle.load(stream)

  cmd = request.command.upper()
  payload = "ERROR unknown command"

  if cmd == "ADD":
    payload = state.add(request.key, request.resource)

  elif cmd == "REMOVE":
    payload = state.remove(request.key)

  elif cmd == "GET":
    payload = state.get(request.key)

  elif cmd == "LIST":
    payload = state.list()

  elif cmd == "COUNT":
    payload = state.count()

  elif cmd == "CLEAR":
    payload = state.clear()

  elif cmd == "UPDATE":
    payload = state.update(request.key, request.resource)

  elif cmd == "POP":
    payload = state.pop(request.key)

  elif cmd == "QUIT":
    payload = "Bye"

  stream = io.BytesIO()
  pickle.dump(Response(payload), stream)
  serialized_payload = stream.getvalue()

  payload_length = len(serialized_payload) + 1
  return payload_length.to_bytes(1, byteorder='big') + serialized_payload

def handle_client(client):
  with client:
    while True:
      if client == None:
        break
      is_new_command = True
      data = client.recv(BUFFER_SIZE)
      if not data:
        break
      binary_data = data
      full_data = binary_data
      message_length = binary_data[0]
      remaining = message_length - BUFFER_SIZE
      while remaining > 0:
        data = client.recv(BUFFER_SIZE)
        binary_data = data
        full_data = full_data + binary_data
        remaining = remaining - len(binary_data)
      response = process_command(full_data)
      client.send(response)

def accept(server):
  while is_running:
    client, addr = server.accept()
    print(f"{addr} has connected")
    client_thread = threading.Thread(target=handle_client, args=(client,))
    client_thread.start()

def main():
  try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    accept_thread = threading.Thread(target=accept, args=(server,))
    accept_thread.start()
    accept_thread.join()
  except BaseException as err:
    print(err)
  finally:
    if server:
      server.close()

if __name__ == '__main__':
  main()