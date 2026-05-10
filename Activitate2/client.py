import socket

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9999
BUFFER_SIZE = 1024
TIMEOUT     = 5

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.settimeout(TIMEOUT)

este_conectat = False

def trimite_comanda(mesaj: str) -> str:
    try:
        client_socket.sendto(mesaj.encode('utf-8'), (SERVER_HOST, SERVER_PORT))
        date_brute, _ = client_socket.recvfrom(BUFFER_SIZE)
        return date_brute.decode('utf-8')
    except socket.timeout:
        return "EROARE: Serverul nu raspunde (timeout)."
    except Exception as e:
        return f"EROARE: {e}"


print("=" * 55)
print("  CLIENT UDP")
print("=" * 55)

while True:
    try:
        intrare = input(">> ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nInchidere client...")
        break

    if not intrare:
        continue

    parti = intrare.split(' ', 1)
    comanda = parti[0].upper()

    if comanda == 'EXIT':
        print("Inchidere client...")
        break

    elif comanda == 'CONNECT':
        raspuns = trimite_comanda(intrare)
        print(raspuns)
        if raspuns.startswith("OK"):
            este_conectat = True

    elif comanda == 'DISCONNECT':
        raspuns = trimite_comanda(intrare)
        print(raspuns)
        if raspuns.startswith("OK"):
            este_conectat = False

    elif comanda == 'PUBLISH':
        if not este_conectat:
            print("EROARE: Nu esti conectat.")
            continue

        if len(parti) < 2 or not parti[1].strip():
            print("EROARE: Trebuie sa furnizezi un mesaj.")
            continue

        raspuns = trimite_comanda(intrare)
        print(raspuns)

    elif comanda == 'DELETE':
        if not este_conectat:
            print("EROARE: Nu esti conectat.")
            continue

        if len(parti) < 2 or not parti[1].isdigit():
            print("EROARE: ID invalid.")
            continue

        raspuns = trimite_comanda(intrare)
        print(raspuns)

    elif comanda == 'LIST':
        if not este_conectat:
            print("EROARE: Nu esti conectat.")
            continue

        raspuns = trimite_comanda(intrare)
        print(raspuns)

    else:
        print("Comanda necunoscuta.")

client_socket.close()
print("Socket inchis.")