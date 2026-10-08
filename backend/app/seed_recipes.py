"""Boshlang'ich retseptlar bazasi. Miqdorlar 1 kishi uchun, grammda.

Bazada yo'q taom so'ralganda u Gemini + Google qidiruvi orqali topilib, xuddi shu sxemada saqlanadi.
"""


def ing(name: str, grams: float, optional: bool = False) -> dict:
    return {"name": name, "grams_per_person": grams, "optional": optional}


SEED_RECIPES: list[dict] = [
    {
        "slug": "osh",
        "name": "Osh (palov)",
        "aliases": ["osh", "palov", "plov", "to'y oshi", "toshkent oshi", "oshi palov"],
        "description": "O'zbek dasturxonining shohi — zirvagi to'q, guruchi donador osh.",
        "time_minutes": 120,
        "ingredients": [
            ing("guruch", 125), ing("go'sht", 100), ing("sabzi", 125), ing("piyoz", 50),
            ing("o'simlik yog'i", 40), ing("sarimsoq", 10, True), ing("no'xat", 20, True),
            ing("mayiz", 10, True), ing("zira", 1, True), ing("tuz", 5, True),
        ],
        "steps": [
            "Guruchni 3-4 marta tiniq suv chiqquncha yuving va iliq tuzli suvda kamida 1 soatga ivitib qo'ying. No'xat bo'lsa, uni kechasi ivitib qo'ygan bo'lishingiz kerak.",
            "Sabzini somoncha qilib uzun-uzun to'g'rang — qirg'ichdan o'tkazmang, oshning chiroyi ketadi! Piyozni yarim halqa qilib, go'shtni yong'oqdek-yong'oqdek bo'laklarga bo'ling.",
            "Qozonga yog'ni quyib, yengil tutun chiqquncha yaxshilab qizdiring. Go'shtni solib, har tomoni qizarib qobiq bog'laguncha qovuring.",
            "Piyozni qo'shing va kapgir bilan aralashtirib, oltin rangga kirguncha qovuring.",
            "Endi sabzini soling. 5-7 daqiqa davomida tez-tez aralashtirib turing, keyin zira, tuz, no'xat va butun sarimsoq boshlarini qo'shing — mana shu zirvak oshning joni!",
            "Zirvakka go'shtni 1-2 barmoq qoplaguncha qaynoq suv quying va o'rta olovda 30-40 daqiqa qaynating. Tuzini tatib ko'ring — zirvak sal sho'rroq bo'lishi kerak.",
            "Guruchning suvini to'kib, zirvak ustiga tekis yoying, aralashtirmang. Ustidan guruchdan 1,5-2 sm baland qilib qaynoq suv quying va olovni kuchaytiring.",
            "Suv singib ketgach, guruchni o'rtaga to'plab, kapgir dastasi bilan bir necha teshik oching. Qopqog'ini mahkam yopib, eng past olovda 25-30 daqiqa damlang.",
            "Oshni yaxshilab aralashtiring va laganga suzing: avval guruch, ustiga sabzi, go'sht va sarimsoq. Achchiq-chuchuk salat bilan dasturxonga torting. Osh bo'lsin!",
        ],
    },
    {
        "slug": "qozon-kabob",
        "name": "Qozon kabob",
        "aliases": ["qozon kabob", "kozon kabob", "qozonkabob", "qozon kabobi"],
        "description": "Qozonda qizartirilgan go'sht va qarsildoq kartoshka — oddiy, lekin mazasi zo'r.",
        "time_minutes": 75,
        "ingredients": [
            ing("go'sht", 200), ing("kartoshka", 250), ing("piyoz", 50),
            ing("o'simlik yog'i", 30), ing("sarimsoq", 5, True), ing("zira", 1, True),
            ing("tuz", 5, True), ing("qora murch", 1, True), ing("kashnich", 10, True),
        ],
        "steps": [
            "Go'shtni (qovurg'ali bo'lsa yanada yaxshi) katta-katta bo'laklarga bo'lib, tuz va murch sepib qo'ying.",
            "Kartoshkani tozalab, yirik bo'laklarga yoki butunligicha qoldiring. Piyozni halqa qilib to'g'rang.",
            "Qozonda yog'ni qizdiring, kartoshkani solib, ustki qismi oltinrang qobiq bog'laguncha qovuring va olib qo'ying.",
            "Shu yog'da go'shtni har tomondan qizartirib qovuring. Keyin 1 piyola suv quyib, qopqog'ini yopib, past olovda 30-40 daqiqa dimlang.",
            "Go'sht yumshagach, kartoshkani qozonga qaytaring, zira va sarimsoq qo'shib, yana 15-20 daqiqa qopqoq ostida damlang.",
            "Laganga go'sht va kartoshkani chiroyli qilib tering, ustidan piyoz halqalari va kashnich seping. Issiq non bilan torting!",
        ],
    },
    {
        "slug": "lagmon",
        "name": "Lag'mon",
        "aliases": ["lag'mon", "lagmon", "lagman", "chuzma lag'mon", "uyg'ur lag'mon"],
        "description": "Qo'lda cho'zilgan xamir va to'q vajali lag'mon.",
        "time_minutes": 90,
        "ingredients": [
            ing("un", 120), ing("go'sht", 100), ing("bulg'or qalampiri", 50), ing("pomidor", 80),
            ing("piyoz", 40), ing("sarimsoq", 10), ing("o'simlik yog'i", 25),
            ing("sabzi", 30, True), ing("turp", 40, True), ing("tuxum", 20, True),
            ing("tuz", 5, True), ing("zira", 1, True),
        ],
        "steps": [
            "Unga tuz va iliq suv qo'shib qattiqroq xamir qoring. Ustini yopib 30 daqiqa tindiring, keyin yana bir bor qorib, tindiring — xamir qanchalik ko'p dam olsa, shunchalik yaxshi cho'ziladi.",
            "Vaja uchun go'shtni ingichka uzunchoq qilib to'g'rang. Piyoz, bulg'or qalampiri, sabzi va turpni ham somoncha qilib to'g'rang, pomidorni mayda kubik qiling.",
            "Qozonda yog'ni qizdirib, go'shtni qovuring. Ketidan piyoz, sabzi va turpni qo'shing, so'ng bulg'or qalampiri, pomidor va maydalangan sarimsoqni soling.",
            "Tuz va zira qo'shib, ozgina suv quying va vajani past olovda 20-25 daqiqa qaynatib qo'ying.",
            "Xamirni barmoqdek bo'laklarga bo'lib, yog'lab chiqing va qo'lda ingichka qilib cho'zing. Qaynab turgan tuzli suvda 3-4 daqiqa qaynatib, sovuq suvda chayib oling.",
            "Lag'monni kosaga solib, ustidan mo'l qilib vaja quying. Xohlasangiz sarimsoqli sirka bilan torting!",
        ],
    },
    {
        "slug": "mastava",
        "name": "Mastava",
        "aliases": ["mastava", "mastoba"],
        "description": "Guruchli, qatiq bilan tortiladigan to'yimli suyuq osh.",
        "time_minutes": 60,
        "ingredients": [
            ing("guruch", 50), ing("go'sht", 80), ing("kartoshka", 100), ing("sabzi", 50),
            ing("piyoz", 40), ing("pomidor", 60), ing("o'simlik yog'i", 15),
            ing("qatiq", 50, True), ing("shivit", 5, True), ing("tuz", 4, True), ing("zira", 1, True),
        ],
        "steps": [
            "Go'shtni mayda kubik qilib, sabzi, kartoshka va piyozni ham kubik shaklda to'g'rang. Guruchni yuvib qo'ying.",
            "Qozonda yog'ni qizdirib, go'shtni qovuring, keyin piyozni qo'shib qizartiring.",
            "Sabzi va pomidorni qo'shib 5 daqiqa qovuring, so'ng kishi boshiga 1,5 kosadan suv quying.",
            "Qaynab chiqqach, kartoshka va guruchni soling, tuz va zira qo'shib, past olovda 25-30 daqiqa qaynating.",
            "Kosalarga suzib, ustiga bir qoshiq qatiq va mayda to'g'ralgan shivit seping. Osh bo'lsin!",
        ],
    },
    {
        "slug": "shorva",
        "name": "Sho'rva",
        "aliases": ["sho'rva", "shorva", "shurva", "shurpa", "qaynatma sho'rva"],
        "description": "Tiniq, yengil va shifobaxsh qaynatma sho'rva.",
        "time_minutes": 120,
        "ingredients": [
            ing("go'sht", 200), ing("kartoshka", 150), ing("sabzi", 80), ing("piyoz", 50),
            ing("pomidor", 60, True), ing("bulg'or qalampiri", 40, True), ing("no'xat", 20, True),
            ing("kashnich", 5, True), ing("tuz", 5, True), ing("qora murch", 1, True),
        ],
        "steps": [
            "Suyakli go'shtni yuvib, sovuq suvli qozonga soling (no'xat bo'lsa, oldindan ivitilgani bilan birga) va qaynashini kuting.",
            "Qaynab chiqqanda ko'pigini kapgir bilan sinchiklab olib tashlang — sho'rvaning tiniqligi shunga bog'liq.",
            "Butun piyozni tashlab, olovni pasaytiring va 1-1,5 soat sekin qaynating.",
            "Sabzi va kartoshkani yirik to'g'rab, pomidor va bulg'or qalampiri bilan qo'shing. Tuz, murch solib, yana 25-30 daqiqa qaynating.",
            "Kosalarga go'sht va sabzavotlarni solib, ustidan sho'rva quying, kashnich seping. Issiq non bilan — rohat!",
        ],
    },
    {
        "slug": "dimlama",
        "name": "Dimlama",
        "aliases": ["dimlama", "bosma", "dimlama sabzavotli"],
        "description": "Go'sht va sabzavotlar o'z bug'ida dimlanadi — bahor-yozning sevimli taomi.",
        "time_minutes": 90,
        "ingredients": [
            ing("go'sht", 150), ing("kartoshka", 150), ing("karam", 150), ing("sabzi", 80),
            ing("piyoz", 60), ing("pomidor", 80), ing("bulg'or qalampiri", 60),
            ing("o'simlik yog'i", 15), ing("baqlajon", 80, True), ing("sarimsoq", 5, True),
            ing("tuz", 5, True), ing("zira", 1, True),
        ],
        "steps": [
            "Hamma sabzavotlarni yirik bo'laklarga to'g'rang, go'shtni o'rtacha bo'laklarga bo'ling.",
            "Qozon tagiga yog' quyib, go'shtni soling, ustidan piyoz halqalarini tering va tuz, zira seping.",
            "Keyin qatlam-qatlam qilib sabzi, kartoshka, baqlajon, bulg'or qalampiri va pomidorni tering. Har qatlamga ozgina tuz seping.",
            "Eng ustiga karam barglarini yopib qo'ying — ular qopqoq vazifasini bajaradi. Suv qo'shmang, sabzavotlar o'z suvini chiqaradi.",
            "Qopqog'ini mahkam yopib, past olovda 1-1,5 soat dimlang. Qopqoqni tez-tez ochmang!",
            "Laganga ehtiyotkorlik bilan ag'darib, sarimsoq va ko'katlar bilan torting.",
        ],
    },
    {
        "slug": "manti",
        "name": "Manti",
        "aliases": ["manti", "monti", "manty"],
        "description": "Kaskanda bug'da pishirilgan, sersuv go'shtli manti.",
        "time_minutes": 100,
        "ingredients": [
            ing("un", 120), ing("go'sht", 130), ing("piyoz", 110), ing("dumba yog'i", 20, True),
            ing("qovoq", 60, True), ing("tuxum", 15, True), ing("tuz", 4, True),
            ing("zira", 1, True), ing("qora murch", 1, True), ing("qatiq", 50, True),
        ],
        "steps": [
            "Un, tuz, tuxum va suvdan qattiqroq xamir qorib, 30 daqiqa tindirib qo'ying.",
            "Go'sht va dumbani pichoqda mayda qilib to'g'rang (qiymalagichdan o'tkazmasangiz, manti sersuv bo'ladi). Piyozni ham mayda to'g'rab, go'shtga qo'shing.",
            "Qiymaga tuz, zira, murch va 2-3 qoshiq sovuq suv qo'shib yaxshilab aralashtiring. Qovoq bo'lsa, mayda kubik qilib qo'shing.",
            "Xamirni yupqa yoyib, 10x10 sm kvadratlarga bo'ling. Har biriga bir qoshiq qiyma solib, chetlarini chiroyli qilib tuging.",
            "Kaskan qavatlarini yog'lab, mantilarni tering va qaynab turgan suv ustida 40-45 daqiqa bug'da pishiring.",
            "Issiq-issiq qatiq yoki qaymoq bilan torting. Osh bo'lsin!",
        ],
    },
    {
        "slug": "chuchvara",
        "name": "Chuchvara",
        "aliases": ["chuchvara", "chuchvara sho'rva", "chuchpara"],
        "description": "Mayda-mayda tugilgan, qatiq bilan tortiladigan chuchvara.",
        "time_minutes": 80,
        "ingredients": [
            ing("un", 80), ing("go'sht", 80), ing("piyoz", 40), ing("tuxum", 15),
            ing("qatiq", 50, True), ing("shivit", 5, True), ing("tuz", 4, True), ing("qora murch", 1, True),
        ],
        "steps": [
            "Un, tuxum, tuz va suvdan qattiq xamir qorib, 20-30 daqiqa tindiring.",
            "Go'sht va piyozni qiymalab, tuz va murch qo'shib aralashtiring.",
            "Xamirni yupqa yoyib, 4x4 sm kvadratchalarga kesing. Har biriga ozgina qiyma solib, uchburchak qilib buklang va ikki uchini birlashtiring.",
            "Qaynab turgan tuzli suvga chuchvaralarni tashlab, yuzaga qalqib chiqqanidan keyin yana 5-7 daqiqa qaynating.",
            "Kosaga sho'rvasi bilan yoki suvsiz suzib, ustiga qatiq va shivit qo'shib torting.",
        ],
    },
    {
        "slug": "moshxorda",
        "name": "Moshxo'rda",
        "aliases": ["moshxo'rda", "moshxorda", "mashxurda", "moshkichiri"],
        "description": "Mosh va guruchli quyuqroq, to'yimli sho'rva.",
        "time_minutes": 70,
        "ingredients": [
            ing("mosh", 40), ing("guruch", 40), ing("go'sht", 70), ing("sabzi", 40),
            ing("piyoz", 40), ing("o'simlik yog'i", 15), ing("kartoshka", 60, True),
            ing("pomidor", 40, True), ing("qatiq", 50, True), ing("tuz", 4, True), ing("zira", 1, True),
        ],
        "steps": [
            "Moshni yuvib, alohida qozonchada yarim pishguncha (20 daqiqa) qaynatib qo'ying.",
            "Qozonda yog'ni qizdirib, mayda to'g'ralgan go'shtni, so'ng piyoz va sabzini qovuring. Pomidor bo'lsa, shu yerda qo'shing.",
            "Suv quyib, qaynagach moshni suvi bilan birga qo'shing.",
            "Guruch va kartoshkani solib, tuz-zira qo'shing va past olovda 25-30 daqiqa, guruch ezilguncha qaynating.",
            "Kosaga suzib, ustiga qatiq qo'shib torting. Kuzgi-qishki kunlar uchun ayni muddao!",
        ],
    },
]
