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
    my_turn = True  # A başlar

    while not gm.is_game_over():

        loser = gm.check_timeout()
        if loser:
            print(f"⏳ TIMEOUT → {loser} -1 puan")
            gm.switch_turn()

        # =====================================================
        # A → B PAKET GÖNDERİYOR
        # =====================================================
        if my_turn:

            print("\n📦 Paket Gönderme Menüsü:")
            print("[1] Normal paket gönder")
            print("[2] Hatalı seq gönder")
            print("[3] Hatalı ack gönder")
            print("[4] length > rwnd gönder")
            print("[5] Rastgele hatalı paket gönder")

            choice = input("Seçim: ")

            length = int(input("[A] Length: "))
            pkt = Packet(seq=seq, ack=ack, rwnd=rwnd, length=length)

            # CHEAT LOGIC (A bilerek hatalı paket oluşturabilir)
            if choice == "2":          # hatalı seq
                pkt.seq += 9999
                gm.pending_invalid_A = True
            elif choice == "3":        # hatalı ack
                pkt.ack -= 500
                gm.pending_invalid_A = True
            elif choice == "4":        # length > rwnd
                pkt.length = pkt.rwnd + 50
                gm.pending_invalid_A = True
            elif choice == "5":        # rastgele saçma paket
                import random
                pkt.seq += random.randint(100, 800)
                pkt.ack -= random.randint(50, 200)
                pkt.length = pkt.rwnd + random.randint(10, 200)
                gm.pending_invalid_A = True

            print(f"\nA → B   SEQ={pkt.seq} LEN={pkt.length} RWND={pkt.rwnd}")
            conn.send(pkt.to_json().encode())

            gm.switch_turn()  # sıra B'ye geçti

            # -------------------- ACK AL ---------------------
            raw = safe_recv(conn)
            if raw is None:
                continue

            # ERROR geldiyse, B hatalı buldu demektir
            if raw == "ERROR":
                print("❌ A'nın gönderdiği paket hatalı bulundu → B +1")
                gm.add_error_point("B")
                validator.reset_sender("A")
                gm.pending_invalid_A = False  # bu hatalı girişim yakalandı
                my_turn = False
                continue

            # JSON parse etmeyi dene
            try:
                ack_pkt = Packet.from_json(raw)
            except:
                print("❌ JSON Parsing hatası → A hatayı tespit etti")
                gm.add_error_point("A")
                validator.reset_sender("B")
                conn.send("ERROR".encode())
                my_turn = False
                continue

            if ack_pkt.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(ack_pkt, sender="B")

            if not ok:
                print(f"\n🚨 ACK Hatalı: {reason}")
                print("[1] ERROR gönder (+1 puan)")
                print("[2] ERROR gönderme (kabul et)")

                c = input("Seçim: ")
                if c == "1":
                    conn.send("ERROR".encode())
                    gm.add_error_point("A")
                    validator.reset_sender("B")
                    my_turn = False
                    continue
                else:
                    # ACK hatalı ama A kabul ediyor -> burada ekstra puan
                    # kuralda açık yazmıyor, o yüzden puan yazmıyoruz.
                    pass
            else:
                # Eğer A daha önce bilerek hatalı gönderdiyse ve B ERROR demediyse → A +1
                if gm.pending_invalid_A:
                    gm.add_missed_error_point("A")
                    print("🎉 B hatayı fark etmedi → A +1")
                    gm.pending_invalid_A = False

                print(f"B → A   ACK={ack_pkt.ack} RWND={ack_pkt.rwnd}")
                seq += pkt.length
                ack = ack_pkt.ack

            my_turn = False
            continue

        # =====================================================
        # B → A PAKETİ GELİYOR (RECEIVE)
        # =====================================================
        else:

            raw = safe_recv(conn)
            if raw is None:
                continue

            # JSON parse etmeyi dene
            try:
                incoming = Packet.from_json(raw)
            except:
                print("❌ B JSON hatası → A hatayı tespit etti")
                gm.add_error_point("A")
                validator.reset_sender("B")
                conn.send("ERROR".encode())
                # sıra hiç veri işlenmeden tekrar A'ya geçsin
                gm.switch_turn()
                my_turn = True
                continue

            print(f"\nB → A   SEQ={incoming.seq} LEN={incoming.length} RWND={incoming.rwnd}")

            if incoming.rwnd == 0:
                gm.notify_rwnd_zero()

            ok, reason = validator.validate(incoming, sender="B")

            if ok:
                print("✅ Paket mantıklı.")
            else:
                print(f"\n🚨 Hatalı Paket: {reason}")

            # HER PAKET İÇİN (doğru/yanlış) ERROR KARARI SORULUR
            print("Bu pakete ERROR göndermek istiyor musun?")
            print("[1] ERROR gönder")
            print("[2] ERROR gönderme (kabul et)")

            ch = input("Seçim: ")

            if ch == "1":
                # ERROR gönderiliyor
                conn.send("ERROR".encode())

                if not ok:
                    # gerçekten hatalı paketi yakaladı → A +1
                    gm.add_error_point("A")
                else:
                    # paket mantıklıydı ama A "pretend" yaptı (fake error)
                    # kuralda ekstra puan yazmıyor, o yüzden sadece oyun akışını bozuyor.
                    print("⚠️ A doğru pakete karşı ERROR gönderdi (fake error).")

                validator.reset_sender("B")
                # ERROR bir cevap paketi, veri değil; sıra A'ya geçsin
                gm.switch_turn()
                my_turn = True
                continue

            # Eğer buraya geldiysek, A paketi KABUL EDİYOR
            # Eğer paket mantıksızsa ama A yine de kabul ettiyse,
            # kural gereği: B yanlış paket gönderdi, A fark etmedi ⇒ B +1
            if not ok:
                gm.add_missed_error_point("B")
                print("🎉 A hatayı fark etmedi → B +1 (hatalı paket kabul edildi)")

            # =========================
            # FLOW CONTROL
            # =========================
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

            print(f"A → B   ACK={ack_pkt.ack} RWND={ack_pkt.rwnd}")
            conn.send(ack_pkt.to_json().encode())

            gm.switch_turn()
            my_turn = True

    print("\n===== OYUN BİTTİ =====")
    print("A:", gm.score_A, " | B:", gm.score_B)


if __name__ == "__main__":
    start_listener()
