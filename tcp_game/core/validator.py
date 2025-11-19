class PacketValidator:

    def __init__(self):
        self.last_A_seq = None
        self.last_A_len = None

        self.last_B_seq = None
        self.last_B_len = None

    def reset_sender(self, sender):
        if sender == "A":
            self.last_A_seq = None
            self.last_A_len = None
        else:
            self.last_B_seq = None
            self.last_B_len = None

    def validate(self, pkt, sender):

        # Negatif değerler
        if pkt.length < 0:
            return False, "length negatif"
        if pkt.rwnd < 0:
            return False, "rwnd negatif"

        # length <= rwnd zorunlu
        if pkt.length > pkt.rwnd:
            return False, "length > rwnd"

        # Sıra kontrolü
        if sender == "A":
            if self.last_A_seq is not None:
                expected = self.last_A_seq + self.last_A_len
                if pkt.seq != expected:
                    return False, f"A seq hatalı, beklenen {expected}"
            self.last_A_seq = pkt.seq
            self.last_A_len = pkt.length

        else:  # B
            if self.last_B_seq is not None:
                expected = self.last_B_seq + self.last_B_len
                if pkt.seq != expected:
                    return False, f"B seq hatalı, beklenen {expected}"
            self.last_B_seq = pkt.seq
            self.last_B_len = pkt.length

        return True, "OK"
