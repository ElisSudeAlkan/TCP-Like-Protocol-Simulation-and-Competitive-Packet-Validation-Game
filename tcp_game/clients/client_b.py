import socket
from tcp_game.core.packet import Packet
from tcp_game.core import PacketValidator

HOST = "127.0.0.1"
PORT = 5000

# Client B için validator (ACK paketlerini doğrulamak için)
validator = PacketValidator()


def start_connector():
    """
    Client B, bağlanan taraf olarak çalışır.
    Kullanıcıdan length bilgisi alır, A tarafına paket yollar.
    A'dan gelen ACK paketlerini doğrular.
    """

    # TCP soketi oluştur
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("[B] Listener'a bağlanıldı.")

    seq = 1  # Başlangıç sequence numarası

    while True:
        # Kullanıcıdan veri uzunluğu al
        length = int(input("[B] Gönderilecek veri uzunluğu (length): "))

        # Normal paket oluştur
        packet = Packet(
            seq=seq,
            ack=0,      # B başlangıçta ACK yollamaz
            rwnd=5,
            length=length
        )

        # JSON olarak gönder
        s.send(packet.to_json().encode())
        print(f"[B] Paket gönderildi → {packet}")

        # A tarafından gönderilen ACK paketini al
        raw_data = s.recv(1024).decode()
        print(f"[B] ACK JSON alındı: {raw_data}")

        # ACK hatalı ise ERROR olarak gelmiş olur
        if raw_data == "ERROR":
            print("[B] A tarafından ERROR cevabı geldi! (Gönderdiğimiz paket hatalıydı)")
            continue

        try:
            # JSON → Packet
            ack_packet = Packet.from_json(raw_data)
            print(f"[B] ACK paketi çözüldü → {ack_packet}")

            # VALIDITY CHECK (ACK paketi mantıklı mı?)
            valid, reason = validator.validate(ack_packet)

            if not valid:
                print(f"[B] HATALI ACK ALGILANDI! Sebep: {reason}")
                # A tarafına hatayı ilet
                s.send("ERROR".encode())
                continue

            print("[B] ACK mantıklı. İletişim devam ediyor.")

            # Yeni seq numarası ACK'e göre güncellenir
            seq = ack_packet.ack

        except Exception as e:
            print("[B] JSON parse edilemedi veya ACK geçersiz!")
            print("Hata:", e)
            s.send("ERROR".encode())

    s.close()
