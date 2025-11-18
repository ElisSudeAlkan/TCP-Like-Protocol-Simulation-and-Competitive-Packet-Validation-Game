import time
from core.packet import Packet
from core.validator import PacketValidator


class GameSocketLoop:
    """
    Bu sınıf client A ve client B için ortak kullanılan oyun döngüsünü temsil eder.
    Parametreler:
        role = "A" veya "B"
        socket_conn = aktif socket bağlantısı
        game = GameManager nesnesi
    """

    def __init__(self, role, socket_conn, game_manager):
        self.role = role          # A mı, B mi
        self.conn = socket_conn   # socket nesnesi
        self.validator = PacketValidator()
        self.game = game_manager

    def send_packet(self, packet: Packet):
        """Packet nesnesini JSON olarak gönderir."""
        json_str = packet.to_json()
        self.conn.send(json_str.encode())
        print(f"[{self.role}] Paket gönderildi → {packet}")

    def receive_packet(self):
        """Paket alır ve Packet nesnesine çevirir."""
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
        """Ana oyun döngüsü."""

        print(f"\n[{self.role}] Oyun döngüsü başlıyor...\n")

        while not self.game.is_game_over():

            # 1) Sıra değilse sadece bekle
            if self.game.turn != self.role:
                continue

            # 2) Kullanıcıdan paket bilgisi al (şimdilik length)
            try:
                length = int(input(f"[{self.role}] Length gir: "))
            except:
                print(f"[{self.role}] Geçersiz input!")
                continue

            # 3) Paket oluştur
            packet = Packet(
                seq=1,
                ack=0,
                rwnd=5,
                length=length
            )

            # 4) Gönder
            self.send_packet(packet)

            # 5) Al ve doğrula
            incoming = self.receive_packet()

            # Hatalıysa puan ver
            if incoming == "ERROR":
                self.game.add_error_point(self.role)
                print(f"[{self.role}] ERROR PUANI ALDI!")
            else:
                # Geçerli paket mi?
                valid, reason = self.validator.validate(incoming)
                if not valid:
                    print(f"[{self.role}] HATALI PAKET ALGILANDI: {reason}")
                    self.conn.send("ERROR".encode())
                    self.game.add_error_point(self.role)
                else:
                    print(f"[{self.role}] Gelen paket mantıklı: {incoming}")

            # 6) Sıra değiştir
            self.game.switch_turn()

        print(f"[{self.role}] OYUN BİTTİ!")
        print("Skorlar:", self.game.get_scores())
