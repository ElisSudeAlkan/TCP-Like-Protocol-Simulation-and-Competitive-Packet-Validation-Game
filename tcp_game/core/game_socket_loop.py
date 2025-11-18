import time
from core.packet import Packet
from core.validator import PacketValidator


class GameSocketLoop:
    """
    Client A ve B için ortak oyun döngüsü (turn-based).
    """

    def __init__(self, role, socket_conn, game_manager):
        self.role = role
        self.conn = socket_conn
        self.game = game_manager
        self.validator = PacketValidator()

    def send_packet(self, packet: Packet):
        json_str = packet.to_json()
        self.conn.send(json_str.encode())
        print(f"[{self.role}] Paket gönderildi → {packet}")

    def receive_packet(self):
        data = self.conn.recv(1024).decode()

        if data == "ERROR":
            print(f"[{self.role}] Karşı taraf ERROR gönderdi!")
            return "ERROR"

        try:
            packet = Packet.from_json(data)
            print(f"[{self.role}] Paket alındı → {packet}")
            return packet

        except:
            print(f"[{self.role}] JSON çözülemedi! ERROR gönderildi.")
            self.conn.send("ERROR".encode())
            return "ERROR"

    def run(self):
        print(f"\n[{self.role}] Oyun döngüsü başlıyor...\n")

        while not self.game.is_game_over():

            # ----------------------------------------------------
            # 1) SIRA BENDE → paket göndermem gerekiyor
            # ----------------------------------------------------
            if self.game.turn == self.role:

                try:
                    length = int(input(f"[{self.role}] Length gir: "))
                except:
                    print(f"[{self.role}] Geçersiz input!")
                    continue

                # Paket oluştur
                packet = Packet(seq=1, ack=0, rwnd=5, length=length)

                # Gönder
                self.send_packet(packet)

                # Karşı taraftan cevap al
                incoming = self.receive_packet()

                if incoming == "ERROR":
                    self.game.add_error_point(self.role)
                    print(f"[{self.role}] ERROR PUANI ALDI!")
                else:

                    # ----------------------------------------------------
                    # RWND = 0 ise → karşı taraf veri kabul etmiyor
                    # Bu durumda gelen cevap normaldir
                    # ----------------------------------------------------
                    if incoming.rwnd == 0:
                        print(f"[{self.role}] Karşı taraf RWND=0 gönderdi → Bekleme moduna geçiliyor!")
                        self.game.rwnd_zero_mode = True
                        # Cevap doğru kabul edilir
                        self.game.switch_turn()
                        continue

                    valid, reason = self.validator.validate(incoming)
                    if not valid:
                        print(f"[{self.role}] HATALI PAKET ALGILANDI: {reason}")
                        self.conn.send("ERROR".encode())
                        self.game.add_error_point(self.role)
                    else:
                        print(f"[{self.role}] Gelen paket mantıklı.")

                # Sıra değiştir
                self.game.switch_turn()
                continue

            # ----------------------------------------------------
            # 2) SIRA BENDE DEĞİL → karşı tarafın paket göndermesini bekle
            # ----------------------------------------------------
            else:
                print(f"[{self.role}] Beklemede... (sıra {self.game.turn} tarafında)")

                incoming = self.receive_packet()

                if incoming == "ERROR":
                    print(f"[{self.role}] Karşı taraf hatalı paketini itiraf etti! :)")
                    self.game.add_error_point(self.role)
                    continue

                # ----------------------------------------------------
                # RWND = 0 → Cevap göndermememiz normaldir
                # ACK göndermeyeceğiz, timeout olmayacak
                # ----------------------------------------------------
                if incoming.rwnd == 0:
                    print(f"[{self.role}] Karşı taraf RWND=0 gönderdi → Cevap vermek zorunda değilim.")
                    self.game.rwnd_zero_mode = True
                    # Sıra yine karşı tarafta kalır (bekleme)
                    continue

                # Normal validasyon
                valid, reason = self.validator.validate(incoming)

                if not valid:
                    print(f"[{self.role}] HATALI PAKET ALGILANDI: {reason}")
                    self.conn.send("ERROR".encode())
                    self.game.add_error_point(self.role)
                else:
                    print(f"[{self.role}] Paket mantıklı, ACK yollanacak.")

                    # ACK paketi gönder
                    ack = Packet(seq=0, ack=1, rwnd=5, length=0)
                    self.send_packet(ack)

                # Sıra bana geçsin
                self.game.switch_turn()

        print(f"[{self.role}] OYUN BİTTİ!")
        print("Skorlar:", self.game.get_scores())
