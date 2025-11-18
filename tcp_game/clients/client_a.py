import socket
import json
from tcp_game.core.packet import Packet
from tcp_game.core import PacketValidator

HOST = "127.0.0.1"
PORT = 5000

validator = PacketValidator()   # Validator nesnesi oluşturduk


def start_listener():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    print(f"[A] Dinleniyor: {HOST}:{PORT}")
    conn, addr = s.accept()
    print(f"[A] Bağlantı kuruldu: {addr}")

    while True:

        raw_data = conn.recv(1024).decode()
        if not raw_data:
            break

        try:
            incoming = Packet.from_json(raw_data)
            print(f"[A] Gelen Paket: {incoming}")

            # VALIDITY CHECK!
            valid, reason = validator.validate(incoming)

            if not valid:
                print(f"[A] HATALI PAKET! Sebep: {reason}")
                conn.send("ERROR".encode())
                continue

            # Eğer paket mantıklı ise ACK paketi üret
            ack_packet = Packet(
                seq=incoming.ack + 1,
                ack=incoming.seq + incoming.length,
                rwnd=5,
                length=0
            )

            conn.send(ack_packet.to_json().encode())
            print(f"[A] ACK gönderildi: {ack_packet}")

        except json.JSONDecodeError:
            print("[A] JSON çözülemedi.")
            conn.send("ERROR".encode())

    conn.close()
    s.close()
