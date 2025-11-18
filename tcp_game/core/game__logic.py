import time

class GameManager:
    """
    Turn-based oyun yöneticisi.

    Görevleri:
        - Sıra yönetimi (A / B)
        - 5 dakikalık oyun süresini takip etmek
        - Hata tespit puanları eklemek
        - Hatalı paket gönderip yakalanmayanlara puan vermek
        - 30 saniyelik cevap süresi kuralını uygulamak
        - RWND = 0 durumunda bekleme modunu etkinleştirmek (timeout iptali)

    Not:
        rwnd_zero_mode = True olduğunda
        -> 30 saniyelik timeout uygulanmaz
        -> karşı tarafın cevap vermemesi normal kabul edilir
    """

    def __init__(self):
        # Oyun B'nin hamlesiyle başlar (istersen A yapabiliriz)
        self.turn = "B"

        # Puanlar
        self.score_A = 0
        self.score_B = 0

        # Zaman yöneticileri
        self.game_start_time = time.time()   # oyun başlangıç zamanı
        self.turn_start_time = time.time()   # sıra değiştiğinde sıfırlanır

        # Eğer rwnd = 0 alınırsa:
        # -> karşı taraf veri kabul edemiyor
        # -> 30 saniyelik cevap zorunluluğu iptal edilir
        self.rwnd_zero_mode = False

    def switch_turn(self):
        """
        Sıra değiştirir (A <-> B).
        Her sıra değiştiğinde zaman sıfırlanır.
        Ayrıca rwnd=0 modu kapanır (normal moda geçilir).
        """
        self.turn = "A" if self.turn == "B" else "B"
        self.turn_start_time = time.time()

        # Yeni tur başladığı için rwnd=0 modu devre dışı
        self.rwnd_zero_mode = False

    def add_error_point(self, who):
        """
        Karşı tarafın hatalı paketini tespit eden kişiye +1 puan verilir.
        """
        if who == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    def missed_error_point(self, who):
        """
        Hatalı paket gönderen kişi yakalanmazsa +1 puan alır.
        """
        if who == "A":
            self.score_A += 1
        else:
            self.score_B += 1

    def check_turn_timeout(self):
        """
        Eğer 30 saniye boyunca hamle yapılmazsa hamlesi gelen taraf -1 puan kaybeder.

        Ancak:
            Eğer rwnd_zero_mode = True ise
            -> Cevap vermemek normaldir
            -> Ceza uygulanmaz
        """
        # RWND = 0 → Bekleme modunda ceza yok
        if self.rwnd_zero_mode:
            return None

        now = time.time()

        # 30 saniye geçti mi?
        if now - self.turn_start_time > 30:
            if self.turn == "A":
                self.score_A -= 1
                return "A"  # cezayı yiyen
            else:
                self.score_B -= 1
                return "B"

        return None

    def is_game_over(self):
        """
        Oyun 5 dakika (300 saniye) sonra sona erer.
        """
        return (time.time() - self.game_start_time) >= 300

    def get_scores(self):
        """
        Her iki tarafın puanlarını döndürür.
        """
        return self.score_A, self.score_B
