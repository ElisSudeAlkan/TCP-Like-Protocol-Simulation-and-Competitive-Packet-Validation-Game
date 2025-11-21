import socket
from tcp_game.core.packet import Packet
from tcp_game.core.validator import PacketValidator
from tcp_game.core.game_logic import GameManager

HOST = "127.0.0.1"
PORT = 5000

validator = PacketValidator()
gm = GameManager()

def safe_recv(conn):
    try:
        raw = conn.recv(2048)
        if not raw:
            return None
        return raw.decode().strip()
    except:
        return None


def start_connector():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("[B] A'ya bağlanıldı.")

    seq = 1
    ack = 0
    rwnd = 100

    recv_count = 0
    my_turn = False  # A başlar

    while not gm.is_game_over():

        loser = gm.check_timeout()
        if loser:
            print(f"⏳ TIMEOUT → {loser} -1 puan")
            gm.switch_turn()

        # =====================================================
        # B → A PAKET GÖNDERİYOR
        # =====================================================
        if my_turn:

            print("\n📦 Paket Gönderme Menüsü:")
            print("[1] Normal paket gönder")
            print("[2] Hatalı seq gönder")
            print("[3] Hatalı ack gönder")
            print("[4] length > rwnd gönder")
            print("[5] Rastgele hatalı paket gönder")

            choice = input("Seçim: ")

            length = int(input("[B] Length: "))
            pkt = Packet(seq=seq, ack=ack, rwnd=rwnd, length=length)

            # BİLEREK HATALI GÖNDERME
            if choice == "2":      # seq
                pkt.seq += 9999
                gm.pending_invalid_B = True
            elif choice == "3":    # ack
                pkt.ack -= 500
                gm.pending_invalid_B = True
            elif choice == "4":    # length > rwnd
                pkt.length = pkt.rwnd + 50
                gm.pending_invalid_B = True
            elif choice == "5":    # random saçma
                import random
                pkt.seq += random.randint(100, 800)
                pkt.ack -= random.randint(50, 200)
                pkt.length = pkt.rwnd + random.randint(10, 200)
                gm.pending_invalid_B = True

            print(f"\nB → A   SEQ={pkt.seq} LEN={pkt.length} RWND={pkt.rwnd}")
            s.send(pkt.to_json().encode())

            gm.switch_turn()

            # -------------------- ACK AL ---------------------
            raw = safe_recv(s)
            if raw is None:
                continue

            # ERROR geldiyse → A hatayı buldu
            if raw == "ERROR":
                print("❌ B'nin gönderdiği paket hatalı bulundu → A +1")
                gm.add_error_point("A")
                validator.reset_sender("B")
                gm.pending_invalid_B = False
                my_turn = False
                continue

            # JSON parselenmiyorsa
            try:
                ack_pkt = Packet.from_json(raw)
            except:
                print("❌ JSON Parsing hatası → B hatayı tespit etti")
                gm.add_error_point("B")
                s.send("ERROR".encode())
                validator.reset_sender("A")
                my_turn = False
                continue

            if ack_pkt.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(ack_pkt, sender="A")

            if not ok:
                print(f"\n🚨 ACK Hatalı: {reason}")
                print("[1] ERROR gönder (+1)")
                print("[2] ERROR gönderme")

                c = input("Seçim: ")
                if c == "1":
                    s.send("ERROR".encode())
                    gm.add_error_point("B")
                    validator.reset_sender("A")
                    my_turn = False
                    continue
                else:
                    # hatalı ACK ama kabul
                    pass
            else:
                if gm.pending_invalid_B:
                    gm.add_missed_error_point("B")
                    print("🎉 A hatayı fark etmedi → B +1")
                    gm.pending_invalid_B = False

                print(f"A → B   ACK={ack_pkt.ack} RWND={ack_pkt.rwnd}")
                seq += pkt.length
                ack = ack_pkt.ack

            my_turn = False
            continue

        # =====================================================
        # A → B PAKETİ GELİYOR
        # =====================================================
        else:

            raw = safe_recv(s)
            if raw is None:
                continue

            try:
                incoming = Packet.from_json(raw)
            except:
                print("❌ A JSON hatası → B hatayı tespit etti")
                gm.add_error_point("B")
                validator.reset_sender("A")
                s.send("ERROR".encode())
                gm.switch_turn()
                my_turn = False
                continue

            print(f"\nA → B   SEQ={incoming.seq} LEN={incoming.length} RWND={incoming.rwnd}")

            if incoming.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(incoming, sender="A")

            if ok:
                print("✅ Paket mantıklı.")
            else:
                print(f"\n🚨 Hatalı Paket: {reason}")

            # HER PAKET İÇİN ERROR MENÜSÜ
            print("Bu pakete ERROR göndermek istiyor musun?")
            print("[1] ERROR gönder")
            print("[2] ERROR gönderme (kabul et)")

            ch = input("Seçim: ")

            if ch == "1":
                s.send("ERROR".encode())

                if not ok:
                    gm.add_error_point("B")   # B hatayı buldu
                else:
                    print("⚠️ B doğru pakete ERROR gönderdi (fake error).")

                validator.reset_sender("A")
                gm.switch_turn()
                my_turn = True
                continue

            # PAKET KABUL EDİLDİ
            if not ok:
                gm.add_missed_error_point("A")
                print("🎉 B hatayı fark etmedi → A +1")

            # FLOW CONTROL
            rwnd -= incoming.length
            if rwnd < 0:
                rwnd = 0

            recv_count += 1
            if recv_count == 4:
                rwnd = min(1000, rwnd + 50)
                recv_count = 0

            # ACK gönder
            ack_pkt = Packet(
                seq=seq,
                ack=incoming.seq + incoming.length,
                rwnd=rwnd,
                length=0
            )

            print(f"B → A   ACK={ack_pkt.ack} RWND={ack_pkt.rwnd}")
            s.send(ack_pkt.to_json().encode())

            gm.switch_turn()
            my_turn = True

    print("\n===== OYUN BİTTİ =====")
    print("A:", gm.score_A, " | B:", gm.score_B)


if __name__ == "__main__":
    start_connector()
