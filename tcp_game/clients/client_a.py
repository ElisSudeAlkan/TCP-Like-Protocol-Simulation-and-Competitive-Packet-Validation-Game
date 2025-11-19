import socket
import json
from tcp_game.core.packet import Packet
from tcp_game.core.validator import PacketValidator
from tcp_game.core.game_logic import GameManager

HOST = "127.0.0.1"
PORT = 5000

validator = PacketValidator()
gm = GameManager()

def safe_recv(conn):
    try:
        raw = conn.recv(1024)
        if not raw:
            return None
        return raw.decode().strip()
    except:
        return None


def start_listener():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    print("[A] Bekliyor...")
    conn, addr = s.accept()
    print("[A] Bağlandı:", addr)

    seq = 1
    ack = 0
    rwnd = 100

    recv_count = 0
    my_turn = True

    while not gm.is_game_over():

        loser = gm.check_timeout()
        if loser:
            print(f"⏳ TIMEOUT: {loser} -1")
            gm.switch_turn()

        # ---------------------------------------
        # A → B GÖNDERİYOR
        # ---------------------------------------
        if my_turn:

            length = int(input("[A] Length: "))
            pkt = Packet(seq=seq, ack=ack, rwnd=rwnd, length=length)

            ok, _ = validator.validate(pkt, sender="A")
            if not ok:
                gm.pending_invalid_A = True

            conn.send(pkt.to_json().encode())
            print(f"A → B  SEQ={seq} LEN={length} RWND={rwnd}")

            gm.switch_turn()

            raw = safe_recv(conn)
            if raw is None:
                continue

            if raw == "ERROR":
                print("❌ A HATALI → B +1")
                gm.add_error_point("B")
                validator.reset_sender("A")
                my_turn = False
                continue

            try:
                ack_pkt = Packet.from_json(raw)
            except:
                print("JSON HATASI → A +1")
                gm.add_error_point("A")
                conn.send("ERROR".encode())
                validator.reset_sender("B")
                continue

            if ack_pkt.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(ack_pkt, sender="B")
            if not ok:
                print("ACK hatalı:", reason)
                conn.send("ERROR".encode())
                gm.add_error_point("A")
                validator.reset_sender("B")
            else:
                if gm.pending_invalid_A:
                    gm.add_missed_error_point("A")
                    gm.pending_invalid_A = False

                print(f"B → A ACK={ack_pkt.ack} RWND={ack_pkt.rwnd}")
                seq += length
                ack = ack_pkt.ack

            my_turn = False
            continue

        # ---------------------------------------
        # B → A GELİYOR
        # ---------------------------------------
        else:

            raw = safe_recv(conn)
            if raw is None:
                continue

            try:
                incoming = Packet.from_json(raw)
            except:
                print("B JSON HATASI → A +1")
                gm.add_error_point("A")
                conn.send("ERROR".encode())
                validator.reset_sender("B")
                continue

            if incoming.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(incoming, sender="B")
            if not ok:
                print("B hatalı:", reason)
                conn.send("ERROR".encode())
                gm.add_error_point("A")
                validator.reset_sender("B")
                gm.switch_turn()
                my_turn = True
                continue

            print(f"B → A SEQ={incoming.seq} LEN={incoming.length} RWND={incoming.rwnd}")

            # FLOW CONTROL ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
            rwnd -= incoming.length
            if rwnd < 0:
                rwnd = 0

            recv_count += 1
            if recv_count == 4:
                rwnd = min(1000, rwnd + 50)
                recv_count = 0
            # FLOW CONTROL ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

            ack_pkt = Packet(
                seq=seq,
                ack=incoming.seq + incoming.length,
                rwnd=rwnd,
                length=0
            )
            conn.send(ack_pkt.to_json().encode())
            print(f"A → B ACK={ack_pkt.ack} RWND={rwnd}")

            if gm.pending_invalid_B:
                gm.add_missed_error_point("B")
                gm.pending_invalid_B = False

            gm.switch_turn()
            my_turn = True

    print("GAME OVER → A:", gm.score_A, " B:", gm.score_B)


if __name__ == "__main__":
    start_listener()
