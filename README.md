# O'zbek Pazanda Bot — Telegram Mini App (MVP)

Mutfaktaki malzemeleri takip eden, stoğa göre Özbek yemeği öneren, seçilen yemeğin eksiklerini
hesaplayıp adım adım tarif veren Telegram Mini App. Arayüz %100 Özbekçe.
Spesifikasyon: [gemini-code-1791482941921.md](gemini-code-1791482941921.md)

## Mimari

```
frontend/  React + Vite + Telegram WebApp SDK  (Dashboard, chat, alışveriş listesi)
backend/   FastAPI + SQLAlchemy  (SQLite lokal, PostgreSQL prod)
  app/ingredients.py   masalliq kataloğu, ad normalizasyonu, birim → gram (1 ta piyoz ≈ 150 g)
  app/parser.py        kural tabanlı metin ayrıştırıcı (API anahtarı yoksa yedek)
  app/llm.py           Gemini API: stok ayrıştırma (JSON şema), Google aramalı tarif bulma (RAG), sohbet
  app/kitchen.py       stok analizi, öneri sıralaması, "Taom tayyor" stok düşümü
  app/recipes.py       tarif arama (yazım hatasına toleranslı), yoksa Gemini + Google Search → DB'ye kayıt
  app/seed_recipes.py  9 hazır tarif: osh, qozon kabob, lag'mon, mastava, sho'rva, dimlama, manti, chuchvara, moshxo'rda
  app/auth.py          Telegram initData HMAC doğrulaması
  bot.py               /start → Mini App butonu
```

**Akış:** stok metni → A) "Bugun nima ovqat qilsam ekan?" (stoğa göre 3 öneri) veya
B) "O'zim ovqat tanlayman" (listeden seç / yaz) → kişi sayısı → eksik analizi
("…yana 750 gramm kartoshka kerak. Xarid ro'yxatiga qo'shaymi?") → adım adım tarif → "Taom tayyor" → stoktan düşüm.

## Diller (Özbekçe / İngilizce / Türkçe)

- İlk açılışta dil seçim ekranı gelir (Telegram dili ön seçili); seçim `users.language`'a kaydedilir,
  başlıktaki bayrak butonuyla değiştirilebilir. Bot `/start` mesajı da bu dilde gelir.
- Seçilen dil her yerde kullanılır: arayüz (`frontend/src/i18n.js`), persona mesajları (`app/persona.py`),
  malzeme/kategori/birim adları (`app/ingredients.py`), tarif adı ve adımları (`app/seed_translations.py`),
  Gemini sohbeti.
- Stok girişi üç dilde anlaşılır: "2 kg guruch, 10 ta piyoz" / "2 kg pirinç, 10 adet soğan" / "2 kg rice, 10 onions".
- Veritabanında malzemeler kanonik Özbekçe adla tutulur, sadece gösterim çevrilir; dil değiştirmek stoku etkilemez.
- Gemini'nin bulduğu yeni tarifler tek çağrıda üç dilde birden üretilip kaydedilir.
- Yeni bir hazır tarif eklerken `seed_translations.py`'ye en/tr çevirisini aynı adım sayısıyla ekleyin
  (`tests/test_i18n.py` bunu kontrol eder).

## Lokal çalıştırma

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Tarayıcıda http://localhost:5173 — sadece lokal denemede `backend/.env` içinde `DEV_MODE=true` yaparsan Telegram
olmadan "Mehmon" kullanıcısıyla çalışır (internete açıkken asla).

Testler:

```bash
cd backend
.venv/Scripts/python -m pytest -q
```

## Gemini API

Anahtar: https://aistudio.google.com/apikey → `backend/.env` içinde `GEMINI_API_KEY`. Model `GEMINI_MODEL`
(varsayılan `gemini-3.8-flash`, ücretsiz katmanda). Anahtar boşsa uygulama kural tabanlı ayrıştırıcı ve hazır tariflerle çalışır.

Ücretsiz kotayı korumak için Gemini sadece gerektiğinde çağrılır:
- **Stok girişi:** önce ücretsiz kural tabanlı ayrıştırıcı çalışır; Gemini'ye sadece onun anlamadığı parçalar gider
  ("bir quti xurmo", Kiril/Rusça girdiler). Tipik "2 kg guruch, 10 ta piyoz" girişleri hiç API çağrısı yapmaz.
- **Bilinmeyen yemek:** Google Search ile araştırılır (1 çağrı) + JSON şemaya dönüştürülür (1 çağrı), sonra DB'ye
  kaydedilir; aynı yemek bir daha sorulduğunda API çağrısı yapılmaz.
- **Sohbet:** pişirme ekranında "Oshpazga savol bering" — her soru 1 çağrı.

Ücretsiz katman notları: dakikalık/günlük istek sınırı vardır (projenizin güncel kotası AI Studio'da görünür);
aşılırsa uygulama çökmez, kibar bir hata mesajı gösterir. Ücretsiz katmanda gönderilen veriler Google tarafından
ürün geliştirmede kullanılabilir.

## Telegram'a bağlama

1. @BotFather → yeni bot → token'ı `.env` içinde `TELEGRAM_BOT_TOKEN`'a yaz.
2. Frontend'i HTTPS bir adrese deploy et (`npm run build` → `dist/`; API farklı domaindeyse `VITE_API_URL` ayarla) ve adresi `WEBAPP_URL`'e yaz.
3. Prod'da `DEV_MODE=false` yap.
4. `python bot.py` (veya `docker compose --profile bot up`).

## Otomatik çalışma (Windows)

`backend/run_all.py` her şeyi tek başına yönetir: frontend'i gerekirse derler, API'yi (frontend'i de sunar)
127.0.0.1:8000'de başlatır, Cloudflare quick tunnel açar ve bulunan `https://….trycloudflare.com` adresiyle botu
başlatır (menü butonu otomatik güncellenir). Çöken parçayı yeniden başlatır.

- Oturum açılınca otomatik başlar: `shell:startup` içindeki `Pazanda.lnk` kısayolu (silmek otomatik başlatmayı kapatır).
- Elle durdurmak: `backend/.venv/Scripts/python run_all.py --stop`
- Loglar: `backend/logs/` (`run_all.log`, `api.log`, `bot.log`, `tunnel.log`)
- Tünel adresi her başlatmada değişir; Telegram'daki menü butonu ve `/start` butonu yeni adresi kullanır.
  Kalıcı adres için bir alan adıyla Cloudflare named tunnel veya sunucuya deploy gerekir.

## Docker (PostgreSQL ile)

Kök klasörde `.env` dosyası oluşturup güçlü bir veritabanı şifresi ver (bu dosya git'e girmez):

```
POSTGRES_PASSWORD=<uzun-rastgele-şifre>
```

```bash
docker compose up --build
```

API sadece `127.0.0.1:8000`'de dinler; dışarıya reverse proxy veya tünel ile açın.

## n8n entegrasyonu

Harici bir n8n workflow'u tarif toplayıp `POST /api/admin/recipes` adresine (`X-Admin-Token: $ADMIN_TOKEN`)
şu JSON'u gönderebilir:

```json
{"name": "Norin", "aliases": ["naryn"], "description": "...", "time_minutes": 180,
 "ingredients": [{"name": "un", "grams_per_person": 100, "optional": false}],
 "steps": ["...", "..."]}
```

## Sonraki adımlar (MVP dışı)

- Vektör DB (pgvector) ile anlamsal tarif arama — şu an ad/alias + bulanık eşleşme kullanılıyor.
- "2 ta piyoz ishlatdim" gibi serbest metinle stoktan düşme.
- Kullanıcıya özel tarif geçmişi / favoriler (`cook_logs` tablosu hazır).

## Güvenlik

- Anahtarlar (`TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `ADMIN_TOKEN`) sadece `backend/.env` içinde durur;
  `.env`, veritabanları ve loglar `.gitignore` ile repoya girmez. Örnek ayarlar: `backend/.env.example`.
- Her istek Telegram `initData` imzasıyla doğrulanır (HMAC, 24 saat geçerlilik). `DEV_MODE=true` bu kontrolü
  kapatır — sadece lokal deneme içindir.
- `DEV_MODE` kapalıyken Swagger (`/docs`) kapalıdır; `/api/admin/recipes` sadece `ADMIN_TOKEN` ayarlıysa çalışır.
- Bot logları istek adreslerini yazmaz (Telegram API adresi token'ı içerir).
- Bir anahtar yanlışlıkla paylaşılırsa hemen yenileyin: Telegram için @BotFather → `/revoke`,
  Gemini için https://aistudio.google.com/apikey.
- Güvenlik açığı bulursanız lütfen herkese açık issue yerine repo sahibine özel olarak bildirin
  (GitHub → Security → Report a vulnerability).
