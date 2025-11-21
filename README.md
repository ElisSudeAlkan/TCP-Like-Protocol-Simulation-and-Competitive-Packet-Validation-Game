TCP Oyunu: Rekabetçi Protokol Simülasyonu
📌 Proje Özeti
Bu proje, soket bağlantısı üzerinden haberleşen iki istemci (Client A ve Client B) arasında basitleştirilmiş bir TCP protokol simülasyonunu gerçekleştirir. Standart bir mesajlaşma uygulamasından farklı olarak, bu proje iletişimi sıra tabanlı ve rekabetçi bir oyuna dönüştürür.

Amaç sadece veri göndermek değil, protokolün bütünlüğünü doğrulamaktır (validate). Oyuncular kurallara uygun paketler gönderebileceği gibi, karşı tarafın doğrulama mekanizmasını (Validator) test etmek için "Blöf" yapıp hatalı paketler de gönderebilirler.

🎯 Ana Özellikler
TCP Durum Makinesi: Sıra Numaraları (SEQ), Onay Numaraları (ACK) ve Alıcı Penceresi (RWND) takibi yapılır.

Akış Kontrolü (Flow Control): Veri geldikçe azalan, uygulama veriyi okudukça (işledikçe) artan bir rwnd (buffer) simülasyonu içerir.

Paket Doğrulama (Validation): Gelen paketlerin mantıksal tutarlılığını denetleyen katı bir doğrulama motoru vardır (Örn: SEQ sırası doğru mu?).

Hata Enjeksiyonu (Blöf Modu): Oyuncular kasıtlı olarak hatalı paketler (Örn: Yanlış SEQ, RWND limitini aşan veri) göndererek karşı tarafı şaşırtmaya çalışabilir.

Puanlama Sistemi: Hataları yakalayan veya karşı tarafa hatalı paket yutturan puan kazanır.


🚀 Nasıl Çalıştırılır?
Simülasyonu başlatmak için iki ayrı terminal penceresi açmanız gerekir.

1. Adım: Client A'yı Başlat (Listener)
Client A sunucu gibi davranır ve bağlantı bekler.


python -m tcp_game.clients.client_a

2. Adım: Client B'yi Başlat (Connector)
Client B, Client A'ya bağlanarak oturumu başlatır.

python -m tcp_game.clients.client_b


🎮 Nasıl Oynanır?
Oyun sıra tabanlıdır (turn-based). Sıra size geldiğinde terminalde bir menü açılır:

1. Normal Paket Gönder
Matematiksel olarak doğru bir TCP paketi gönderir. seq ve ack numaraları protokol geçmişine göre otomatik hesaplanır.

2. Hacking / Blöf Seçenekleri (Hata Enjeksiyonu)
Karşı tarafın kodunu test etmek (veya puan kazanmak) için bilerek hatalı paket gönderebilirsiniz:

Hatalı SEQ: Beklenenden çok farklı bir sıra numarası gönderir.

Hatalı ACK: Henüz alınmamış bir veriyi onaylıyormuş gibi yapar.

Length > RWND: Alıcının pencere boyutundan (buffer) daha büyük veri gönderir (Flow Control İhlali).

3. Paket Alma ve Doğrulama
Size bir paket geldiğinde Validator bunu analiz eder ve size sorar:

[1] ERROR Gönder: Eğer pakette bir hata (hile) fark ettiyseniz bunu seçin. Haklıysanız +1 Puan kazanırsınız.

[2] ERROR Gönderme (Kabul Et): Paket düzgün görünüyorsa bunu seçin.

⚠️ Uyarı: Eğer hatalı bir paketi kabul ederseniz (hatayı fark edemezseniz), hileyi yapan taraf +1 Puan kazanır.

🛠️ Teknik Detaylar
Paket Yapısı
Paketler basitlik açısından JSON formatında iletilir:

JSON

{
    "seq": 100,
    "ack": 200,
    "rwnd": 50,
    "length": 10,
    "data": ""
}
Doğrulama Mantığı (Validator)
PacketValidator sınıfı bağlantının durumunu (state) takip eder ve şunları zorunlu kılar:

Sıra Sürekliliği: Gelen SEQ == Son SEQ + Son Uzunluk

Pencere Bütünlüğü: Length <= Mevcut RWND

Mantık Kontrolü: RWND ve Length değerleri negatif olamaz.


