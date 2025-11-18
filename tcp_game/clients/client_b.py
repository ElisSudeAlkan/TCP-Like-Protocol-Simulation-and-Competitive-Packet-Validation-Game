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


def start_connector():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    print("[B] A'ya bağlanıldı.\n")

    seq_b = 1
    ack_b = 0
    rwnd_b = RWND_START
    recv_count = 0

    my_turn = False

    while True:

        # -------------------- B veri gönderiyor --------------------
        if my_turn:

            length = int(input("[B] Gönderilecek veri LEN: "))

            pkt = Packet(seq=seq_b, ack=ack_b, rwnd=rwnd_b, length=length)
            s.send(pkt.to_json().encode())

            print(f"B → A : SEQ={seq_b} LEN={length} RWND={rwnd_b}")

            raw = s.recv(1024).decode()

            if raw == "ERROR":
                print("❌ B: A hatalı paket dedi.")
                my_turn = False
                continue

            ack = Packet.from_json(raw)

            ok, reason = validator.validate(ack)
            if not ok:
                print(f"❌ ERROR: {reason}")
                continue

            print(f"A → B : ACK={ack.ack} RWND={ack.rwnd}")

            seq_b += length
            ack_b = ack.ack

            my_turn = False
            continue

        # -------------------- A veri gönderiyor --------------------
        else:

            raw = s.recv(1024).decode()
            incoming = Packet.from_json(raw)

            ok, reason = validator.validate(incoming)
            if not ok:
                print(f"❌ ERROR: {reason}")
                s.send("ERROR".encode())
                my_turn = True
                continue

            print(f"A → B : SEQ={incoming.seq} LEN={incoming.length} RWND={incoming.rwnd}")

            rwnd_b -= incoming.length
            if rwnd_b < 0:
                rwnd_b = 0

            recv_count += 1
            if recv_count == RWND_INC_EVERY:
                rwnd_b = min(RWND_MAX, rwnd_b + RWND_INC_AMOUNT)
                recv_count = 0

            ack_pkt = Packet(
                seq=seq_b,
                ack=incoming.seq + incoming.length,
                rwnd=rwnd_b,
                length=0
            )
            s.send(ack_pkt.to_json().encode())

            print(f"B → A : ACK={incoming.seq + incoming.length} RWND={rwnd_b}\n")

            ack_b = incoming.seq + incoming.length
            my_turn = True


if __name__ == "__main__":
    start_connector()
