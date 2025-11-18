from .packet import Packet

class PacketValidator:
    """
    Gelen paketlerin mantıklı olup olmadığını kontrol eder.
    Temel kontroller:
        - length negatif olamaz
        - rwnd negatif olamaz
        - length > rwnd olamaz (flow control)
        - ack geri gidemez
        - seq sadece o tarafın kendi gönderim sırasına göre kontrol edilir
    """

    def __init__(self):
        # A'nın seq hattı
        self.last_A_seq = None
        self.last_A_len = None

        # B'nin seq hattı
        self.last_B_seq = None
        self.last_B_len = None

        # Genel ACK kontrolü
        self.last_ack = None

    def validate(self, packet: Packet):

        # 1 — Length negatif olamaz
        if packet.length < 0:
            return False, "Length negatif olamaz"

        # 2 — rwnd negatif olamaz
        if packet.rwnd < 0:
            return False, "rwnd negatif olamaz"

        # 3 — Flow control
        if packet.length > packet.rwnd:
            return False, "length rwnd’den büyük olamaz (flow control ihlali)"

        # 4 — ACK geri gidemez
        if self.last_ack is not None and packet.ack < self.last_ack:
            return False, "ACK geri gidemez"

        # ACK güncelle
        self.last_ack = packet.ack

        # 5 — SEQ kontrolü AYRI AYRI

        # A → B paketi mi? (ACK > 0 AND RWND > 0 AND length > 0?)
        if packet.ack == 0:   # Bu paketi gönderen B'dir
            if self.last_B_seq is not None:
                expected = self.last_B_seq + self.last_B_len
                if packet.seq != expected:
                    return False, f"B seq bozuk: beklenen {expected}, gelen {packet.seq}"

            self.last_B_seq = packet.seq
            self.last_B_len = packet.length

        else:  # Bu paketi gönderen A'dır
            if self.last_A_seq is not None:
                expected = self.last_A_seq + self.last_A_len
                if packet.seq != expected:
                    return False, f"A seq bozuk: beklenen {expected}, gelen {packet.seq}"

            self.last_A_seq = packet.seq
            self.last_A_len = packet.length

        return True, "OK"
