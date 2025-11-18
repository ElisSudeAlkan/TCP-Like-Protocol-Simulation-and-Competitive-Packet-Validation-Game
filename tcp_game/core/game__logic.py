import time

class GameManager:
    """
    Turn-based oyun yöneticisi.
    Oyunun temel sorumlulukları:
        - sıra yönetimi
        - puan yönetimi
        - oyun süresini takip etmek (5 dakika)
        - 30 saniye bekleme kuralı
    """

    def __init__(self):
        self.turn = "B"        # İlk hamleyi B başlatıyor (istersen A yaparız)
        self.score_A = 0
        self.score_B = 0
        self.game_start_time = time.time()
        self.turn_start_time = time.time()

    def switch_turn(self):
        """Sıra değiştirir."""
        self.turn = "A" if self.turn == "B" else "B"
        self.turn_start_time = time.time()

    def add_error_point(self, who):
        """ERROR tespit eden +1 alır."""
        if who == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    def missed_error_point(self, who):
        """Hatalı paket gönderip karşı taraf anlamazsa +1 puan."""
        if who == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    def check_turn_timeout(self):
        """
        Eğer 30 saniye içerisinde karşı taraf cevap göndermezse
        sıra kimdeyse o -1 puan alır.
        """
        now = time.time()
        if now - self.turn_start_time > 30:
            if self.turn == "A":
                self.score_A -= 1
                return "A"
            else:
                self.score_B -= 1
                return "B"
        return None

    def is_game_over(self):
        """5 dakika geçti mi?"""
        return (time.time() - self.game_start_time) >= 300  # 5 dakika = 300 sn

    def get_scores(self):
        return self.score_A, self.score_B
