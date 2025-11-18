import socket
from tcp_game.core.packet import Packet
from tcp_game.core.validator import PacketValidator

HOST = "127.0.0.1"
PORT = 5000

validator = PacketValidator()

RWND_START = 100
RWND_INC_EVERY = 4
RWND_INC_AMOUNT = 50
RWND_MAX = 1000


def start_listener():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    print("[A] Dinleniyor…")
    conn, addr = s.accept()
    print(f"[A] Bağlantı kuruldu: {addr}\n")

    seq_a = 1
    ack_a = 0

    rwnd_a = RWND_START
    recv_count = 0

    my_turn = True

    while True:

        # -------------------- A veri gönderiyor --------------------
        if my_turn:

            length = int(input("[A] Gönderilecek veri LEN: "))

            pkt = Packet(seq=seq_a, ack=ack_a, rwnd=rwnd_a, length=length)
            conn.send(pkt.to_json().encode())

            print(f"A → B : SEQ={seq_a} LEN={length} RWND={rwnd_a}")

            raw = conn.recv(1024).decode()

            if raw == "ERROR":
                print("❌ A: B hatalı paket dedi.")
                my_turn = False
                continue

            ack = Packet.from_json(raw)

            ok, reason = validator.validate(ack)
            if not ok:
                print(f"❌ ERROR: {reason}")
                continue

            print(f"B → A : ACK={ack.ack} RWND={ack.rwnd}")

            seq_a += length
            ack_a = ack.ack

            my_turn = False
            continue

        # -------------------- B veri gönderiyor --------------------
        else:

            raw = conn.recv(1024).decode()
            incoming = Packet.from_json(raw)

            ok, reason = validator.validate(incoming)
            if not ok:
                print(f"❌ ERROR: {reason}")
                conn.send("ERROR".encode())
                my_turn = True
                continue

            print(f"B → A : SEQ={incoming.seq} LEN={incoming.length} RWND={incoming.rwnd}")

            # FLOW CONTROL
            rwnd_a -= incoming.length
            if rwnd_a < 0:
                rwnd_a = 0

            recv_count += 1
            if recv_count == RWND_INC_EVERY:
                rwnd_a = min(RWND_MAX, rwnd_a + RWND_INC_AMOUNT)
                recv_count = 0

            ack_pkt = Packet(
                seq=seq_a,
                ack=incoming.seq + incoming.length,
                rwnd=rwnd_a,
                length=0
            )
            conn.send(ack_pkt.to_json().encode())

            print(f"A → B : ACK={incoming.seq + incoming.length} RWND={rwnd_a}\n")

            ack_a = incoming.seq + incoming.length
            my_turn = True


if __name__ == "__main__":
    start_listener()
