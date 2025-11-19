import time

class GameManager:
    def __init__(self):
        self.turn = "A"

        self.score_A = 0
        self.score_B = 0

        self.game_start_time = time.time()
        self.turn_start_time = time.time()

        # rwnd = 0 olduğunda timeout çalışmasın
        self.rwnd_zero_mode = False

        # “hatalı paket yakalanmazsa +1” flagleri
        self.pending_invalid_A = False
        self.pending_invalid_B = False

    # ------------------------------
    # PUANLAMA
    # ------------------------------
    def add_error_point(self, detector):
        if detector == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    def add_missed_error_point(self, sender):
        if sender == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    # ------------------------------
    # SIRA YÖNETİMİ
    # ------------------------------
    def switch_turn(self):
        self.turn = "A" if self.turn == "B" else "B"
        self.turn_start_time = time.time()
        self.rwnd_zero_mode = False

    # ------------------------------
    # TIMEOUT
    # ------------------------------
    def check_timeout(self):
        if self.rwnd_zero_mode:
            return None

        if time.time() - self.turn_start_time > 30:
            if self.turn == "A":
                self.score_A -= 1
                return "A"
            else:
                self.score_B -= 1
                return "B"
        return None

    # ------------------------------
    # RWND = 0
    # ------------------------------
    def notify_rwnd_zero(self):
        self.rwnd_zero_mode = True

    # ------------------------------
    # BİTİŞ
    # ------------------------------
    def is_game_over(self):
        return (time.time() - self.game_start_time) > 300

    def get_scores(self):
        return self.score_A, self.score_B
