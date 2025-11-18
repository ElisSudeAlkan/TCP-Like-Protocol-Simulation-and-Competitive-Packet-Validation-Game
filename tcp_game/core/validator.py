from tcp_game.core.packet import Packet


class PacketValidator:
    """
    Bu sınıf gelen paketlerin mantıklı olup olmadığını kontrol eder.
    Temel kontroller:
        - seq artışı mantıklı mı
        - ack mantıklı mı
        - rwnd değerleri tutarlı mı
        - length pozitif mi
        - önceki paket bilgisi ile uyumlu mu
    """

    def __init__(self):
        # Son alınan paket bilgilerini saklayacağız
        self.last_seq = None
        self.last_ack = None
        self.last_rwnd = None

    def validate(self, packet: Packet):
        """
        Paket mantıklıysa True, mantıksızsa False döndürür.
        """

        # 1) Length negatif olamaz
        if packet.length < 0:
            return False, "Length negatif olamaz"

        # 2) rwnd negatif olamaz
        if packet.rwnd < 0:
            return False, "rwnd negatif olamaz"

        # 3) Eğer daha önce paket aldıysak sıra kontrolü yap
        if self.last_seq is not None:
            # seq artışı mantıklı mı?
            # Örn: eski seq = 10, length = 20 → yeni seq >= 30 olmalı
            expected_seq = self.last_seq + self.last_length

            if packet.seq < expected_seq:
                return False, f"seq geri gitmiş: beklenen {expected_seq}, gelen {packet.seq}"

        # 4) ack mantıklı mı? (Çok basit bir kontrol)
        if packet.ack < 0:
            return False, "ACK negatif olamaz"

        # --- Buraya kadar paket mantıklı kabul edilir ---

        # Önceki değerleri güncelle
        self.last_seq = packet.seq
        self.last_ack = packet.ack
        self.last_rwnd = packet.rwnd
        self.last_length = packet.length

        return True, "OK"
