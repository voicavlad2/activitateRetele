import socket

HOST        = '127.0.0.1'
PORT        = 9999
BUFFER_SIZE = 1024

clienti_conectati = {}
mesaje = {}          # id -> { "text": ..., "autor": ... }
urmator_id = 1

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("=" * 50)
print(f"  SERVER UDP pornit pe {HOST}:{PORT}")
print("  Asteptam mesaje de la clienti...")
print("=" * 50)

while True:
    try:
        date_brute, adresa_client = server_socket.recvfrom(BUFFER_SIZE)
        mesaj_primit = date_brute.decode('utf-8').strip()

        parti = mesaj_primit.split(' ', 1)
        comanda = parti[0].upper()
        argumente = parti[1] if len(parti) > 1 else ''

        print(f"\n[PRIMIT] De la {adresa_client}: '{mesaj_primit}'")

        if comanda == 'CONNECT':
            if adresa_client in clienti_conectati:
                raspuns = "EROARE: Esti deja conectat la server."
            else:
                clienti_conectati[adresa_client] = True
                raspuns = f"OK: Conectat. Clienti activi: {len(clienti_conectati)}"

        elif comanda == 'DISCONNECT':
            if adresa_client in clienti_conectati:
                del clienti_conectati[adresa_client]
                raspuns = "OK: Deconectat cu succes."
            else:
                raspuns = "EROARE: Nu esti conectat."

        elif comanda == 'PUBLISH':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat."
            elif not argumente.strip():
                raspuns = "EROARE: Mesajul nu poate fi gol."
            else:
                mesaje[urmator_id] = {
                    "text": argumente,
                    "autor": adresa_client
                }
                raspuns = f"OK: Mesaj publicat cu ID={urmator_id}"
                urmator_id += 1

        elif comanda == 'DELETE':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat."
            elif not argumente.isdigit():
                raspuns = "EROARE: ID invalid."
            else:
                id_mesaj = int(argumente)

                if id_mesaj not in mesaje:
                    raspuns = "EROARE: ID inexistent."
                elif mesaje[id_mesaj]["autor"] != adresa_client:
                    raspuns = "EROARE: Nu poti sterge mesajul altui utilizator."
                else:
                    del mesaje[id_mesaj]
                    raspuns = f"OK: Mesajul {id_mesaj} a fost sters."

        elif comanda == 'LIST':
            if adresa_client not in clienti_conectati:
                raspuns = "EROARE: Nu esti conectat."
            elif not mesaje:
                raspuns = "Nu exista mesaje."
            else:
                lista = []
                for id_mesaj, info in mesaje.items():
                    lista.append(f"{id_mesaj}: {info['text']}")
                raspuns = "\n".join(lista)

        else:
            raspuns = f"EROARE: Comanda '{comanda}' necunoscuta."

        server_socket.sendto(raspuns.encode('utf-8'), adresa_client)
        print(f"[TRIMIS]  Catre {adresa_client}: '{raspuns}'")

    except KeyboardInterrupt:
        print("\n[SERVER] Oprire server...")
        break
    except Exception as e:
        print(f"[EROARE] {e}")

server_socket.close()
print("[SERVER] Socket inchis.")