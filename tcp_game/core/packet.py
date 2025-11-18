import json

class Packet:
    """
    Bu sınıf, TCP-benzeri paket yapısını temsil eder.
    Paket alanları:
        seq    : sequence number
        ack    : acknowledgment number
        rwnd   : receiver window
        length : veri uzunluğu
    """

    def __init__(self, seq, ack, rwnd, length):
        self.seq = seq
        self.ack = ack
        self.rwnd = rwnd
        self.length = length

    def to_dict(self):
        """Paketi sözlük (dict) formatına çevirir."""
        return {
            "seq": self.seq,
            "ack": self.ack,
            "rwnd": self.rwnd,
            "length": self.length
        }

    def to_json(self):
        """Paketi JSON string olarak döndürür (socket üzerinden gönderilebilir)."""
        return json.dumps(self.to_dict())

    @staticmethod
    def from_json(json_data):
        """
        JSON string aldığı zaman dict'e çevirip Packet nesnesi üretir.
        """
        data = json.loads(json_data)
        return Packet(
            seq=data["seq"],
            ack=data["ack"],
            rwnd=data["rwnd"],
            length=data["length"]
        )

    def __str__(self):
        """Debug için okunabilir string formatı."""
        return f"Packet(seq={self.seq}, ack={self.ack}, rwnd={self.rwnd}, length={self.length})"
