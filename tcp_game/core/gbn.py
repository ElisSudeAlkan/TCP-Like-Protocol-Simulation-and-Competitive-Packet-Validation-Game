from collections import deque


class GoBackNHandler:
    def __init__(self, window_size=5):
        self.window_size = window_size
        # Gönderilen ama henüz ACK gelmemiş paketleri burada tutun
        # Format: {seq_num: PacketObj}
        self.sent_buffer = {}
        self.base = 0
        self.next_seq_num = 0
        self.last_ack_received = -1
        self.duplicate_ack_count = 0

    def can_send(self, current_rwnd):
        """
        Eğer gönderim penceresi (window) dolu değilse True döner.
        rwnd (Receiver Window) ve window_size'ı kontrol etmelisiniz.
        """
        # BURAYI DOLDURUN
        pass

    def add_packet(self, packet):
        """
        Yeni bir paket gönderildiğinde bunu buffer'a ekler.
        """
        # BURAYI DOLDURUN
        pass

    def process_ack(self, ack_num):
        """
        Gelen ACK numarasına göre:
        1. Buffer'dan onaylanan paketleri siler (sliding window).
        2. Double ACK (aynı ack üst üste gelirse) durumunu sayar.

        Return:
        - 'NEW': Yeni bir paket onaylandı, pencere kaydı.
        - 'DUP': Duplicate ACK geldi (retransmission gerekebilir).
        - 'IGNORE': Eski veya geçersiz ACK.
        """
        # BURAYI DOLDURUN
        # İpucu: Proje kuralına göre Double ACK retransmission tetikler.
        pass

    def get_packets_to_retransmit(self):
        """
        Double ACK vb. durumlarda tekrar gönderilmesi gereken
        paketlerin listesini döner.
        """
        # BURAYI DOLDURUN
        pass