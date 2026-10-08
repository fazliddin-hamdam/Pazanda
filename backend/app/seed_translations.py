"""Boshlang'ich retseptlarning inglizcha va turkcha tarjimalari.

Qadamlar soni va tartibi o'zbekcha asl nusxa (seed_recipes.py) bilan bir xil bo'lishi kerak.
EXTRA_ALIASES — boshqa tillarda qidirilganda ham taom topilishi uchun.
"""

EXTRA_ALIASES: dict[str, list[str]] = {
    "osh": ["pilaf", "uzbek pilaf", "rice pilaf", "pilav", "özbek pilavı", "plov pilav"],
    "qozon-kabob": ["kazan kebab", "kazan kebabı", "kazan kebap", "cauldron kebab"],
    "lagmon": ["lağman", "laghman", "lagman noodles"],
    "mastava": ["mastava soup", "mastava çorbası", "rice soup"],
    "shorva": ["şurpa", "shurpa", "shorpa", "sorpa"],
    "dimlama": ["dımlama", "dimlama stew", "braised vegetables"],
    "manti": ["mantı", "uzbek manti", "özbek mantısı"],
    "chuchvara": ["çuçvara", "dushbara", "düşbere", "uzbek dumplings"],
    "moshxorda": ["maşhurda", "mashkhurda", "mung bean soup", "maş çorbası"],
}

TRANSLATIONS: dict[str, dict[str, dict]] = {
    "osh": {
        "en": {
            "name": "Plov (Osh)",
            "description": "The king of the Uzbek table — a rich zirvak and fluffy, separate grains of rice.",
            "steps": [
                "Wash the rice 3-4 times until the water runs clear, then soak it in warm salted water for at least an hour. If you're using chickpeas, they should have soaked overnight.",
                "Cut the carrots into long matchsticks — don't grate them, or the plov loses its beauty! Slice the onions into half rings and cut the meat into walnut-sized pieces.",
                "Pour the oil into the qozon (a heavy cast-iron cauldron) and heat it until it just starts to smoke. Add the meat and fry until every side is browned and sealed.",
                "Add the onions and fry, stirring with a kapgir (a wide slotted spoon), until golden.",
                "Now add the carrots. Stir often for 5-7 minutes, then add cumin, salt, the chickpeas and whole heads of garlic — this is the zirvak, the soul of the plov!",
                "Pour boiling water over the zirvak to cover the meat by 1-2 fingers and simmer on medium heat for 30-40 minutes. Taste it — the zirvak should be a little on the salty side.",
                "Drain the rice and spread it evenly over the zirvak — don't stir. Pour boiling water over it to 1.5-2 cm above the rice and turn the heat up.",
                "Once the water is absorbed, gather the rice into a dome and poke a few holes with the handle of the kapgir. Close the lid tightly and let it steam on the lowest heat for 25-30 minutes.",
                "Mix the plov well and serve on a large platter: rice first, then carrots, meat and garlic on top. Bring it to the table with a fresh tomato-onion salad. Enjoy your meal!",
            ],
        },
        "tr": {
            "name": "Özbek Pilavı (Osh)",
            "description": "Özbek sofrasının padişahı — bol zirvaklı, taneleri dağılan pilav.",
            "steps": [
                "Pirinci suyu berraklaşana kadar 3-4 kez yıkayın ve ılık tuzlu suda en az 1 saat bekletin. Nohut kullanacaksanız onu bir gece önceden ıslatmış olmalısınız.",
                "Havuçları uzun uzun kibrit çöpü gibi doğrayın — rendelemeyin, pilavın güzelliği gider! Soğanı yarım ay şeklinde doğrayın, eti ceviz büyüklüğünde parçalara ayırın.",
                "Kazana (qozon — dökme demir kazan) yağı koyun ve hafif duman çıkana kadar iyice kızdırın. Eti ekleyip her tarafı kızarıp kabuk bağlayana kadar kavurun.",
                "Soğanı ekleyin ve kevgirle (kapgir) karıştırarak altın rengini alana kadar kavurun.",
                "Şimdi havuçları ekleyin. 5-7 dakika sık sık karıştırın, sonra kimyon, tuz, nohut ve bütün sarımsak başlarını ekleyin — işte bu zirvak, pilavın ruhu!",
                "Zirvakın üzerine eti 1-2 parmak geçecek kadar kaynar su dökün ve orta ateşte 30-40 dakika pişirin. Tadına bakın — zirvak biraz tuzlu olmalı.",
                "Pirincin suyunu süzüp zirvakın üzerine eşit şekilde yayın, karıştırmayın. Üzerine pirinci 1,5-2 cm geçecek kadar kaynar su dökün ve ateşi açın.",
                "Su çekilince pirinci ortada toplayın ve kevgirin sapıyla birkaç delik açın. Kapağı sıkıca kapatıp en kısık ateşte 25-30 dakika demlendirin.",
                "Pilavı iyice karıştırıp büyük tabağa alın: önce pirinç, üstüne havuç, et ve sarımsak. Domatesli soğan salatasıyla sofraya getirin. Afiyet olsun!",
            ],
        },
    },
    "qozon-kabob": {
        "en": {
            "name": "Qozon Kabob (Cauldron Kebab)",
            "description": "Meat browned in the qozon with crispy potatoes — simple, but so tasty.",
            "steps": [
                "Cut the meat (ribs are even better) into large pieces and sprinkle with salt and black pepper.",
                "Peel the potatoes and leave them whole or cut them into large chunks. Slice the onion into rings.",
                "Heat the oil in the qozon, add the potatoes and fry until the outside turns golden, then set them aside.",
                "In the same oil, brown the meat on all sides. Add a cup of water, cover and braise on low heat for 30-40 minutes.",
                "When the meat is tender, return the potatoes to the qozon, add cumin and garlic and steam under the lid for another 15-20 minutes.",
                "Arrange the meat and potatoes nicely on a platter and top with onion rings and coriander. Serve with warm bread!",
            ],
        },
        "tr": {
            "name": "Kazan Kebabı",
            "description": "Kazanda kızartılmış et ve çıtır patates — sade ama çok lezzetli.",
            "steps": [
                "Eti (kaburgalı olursa daha da iyi) iri parçalara ayırın, tuz ve karabiber serpin.",
                "Patatesleri soyun, bütün bırakın ya da iri parçalara bölün. Soğanı halka halka doğrayın.",
                "Kazanda yağı kızdırın, patatesleri ekleyip dışı altın rengi olana kadar kızartın ve kenara alın.",
                "Aynı yağda eti her tarafı kızarana kadar kavurun. Bir bardak su ekleyip kapağını kapatın ve kısık ateşte 30-40 dakika pişirin.",
                "Et yumuşayınca patatesleri kazana geri koyun, kimyon ve sarımsak ekleyip kapak altında 15-20 dakika daha demlendirin.",
                "Eti ve patatesleri tabağa güzelce dizin, üzerine soğan halkaları ve kişniş serpin. Sıcak ekmekle servis edin!",
            ],
        },
    },
    "lagmon": {
        "en": {
            "name": "Lagman",
            "description": "Hand-pulled noodles with a rich meat and vegetable sauce.",
            "steps": [
                "Knead a firm dough from flour, salt and warm water. Cover and rest for 30 minutes, knead again and rest once more — the longer the dough rests, the better it stretches.",
                "For the sauce (vaja), cut the meat into thin strips. Slice the onion, bell pepper, carrot and radish into matchsticks and dice the tomatoes.",
                "Heat the oil in the qozon and fry the meat. Add the onion, carrot and radish, then the bell pepper, tomatoes and chopped garlic.",
                "Season with salt and cumin, add a little water and let the sauce simmer on low heat for 20-25 minutes.",
                "Divide the dough into finger-thick pieces, oil them and stretch them by hand into thin noodles. Boil in salted water for 3-4 minutes and rinse in cold water.",
                "Put the noodles in a bowl and pour plenty of sauce on top. Serve with garlic vinegar if you like!",
            ],
        },
        "tr": {
            "name": "Lağman",
            "description": "Elde çekilmiş hamur ve bol etli sebzeli sosuyla lağman.",
            "steps": [
                "Un, tuz ve ılık sudan sertçe bir hamur yoğurun. Üzerini örtüp 30 dakika dinlendirin, bir kez daha yoğurup tekrar dinlendirin — hamur ne kadar dinlenirse o kadar iyi uzar.",
                "Sos (vaja) için eti ince uzun şeritler halinde doğrayın. Soğan, dolmalık biber, havuç ve turpu da kibrit çöpü gibi, domatesi küp küp doğrayın.",
                "Kazanda yağı kızdırıp eti kavurun. Ardından soğan, havuç ve turpu, sonra biber, domates ve doğranmış sarımsağı ekleyin.",
                "Tuz ve kimyon ekleyip biraz su koyun, sosu kısık ateşte 20-25 dakika pişirin.",
                "Hamuru parmak kalınlığında parçalara bölün, yağlayın ve elle ince ince çekin. Kaynayan tuzlu suda 3-4 dakika haşlayıp soğuk suyla durulayın.",
                "Lağmanı kaseye alıp üzerine bol sos dökün. İsterseniz sarımsaklı sirkeyle servis edin!",
            ],
        },
    },
    "mastava": {
        "en": {
            "name": "Mastava (Rice Soup)",
            "description": "A hearty rice soup served with a spoonful of qatiq (yogurt).",
            "steps": [
                "Dice the meat, and cut the carrots, potatoes and onion into cubes. Wash the rice.",
                "Heat the oil in the qozon, fry the meat, then add the onion and brown it.",
                "Add the carrots and tomatoes and fry for 5 minutes, then pour in 1.5 bowls of water per person.",
                "When it boils, add the potatoes and rice, season with salt and cumin and simmer on low heat for 25-30 minutes.",
                "Ladle into bowls and top with a spoonful of qatiq and chopped dill. Enjoy!",
            ],
        },
        "tr": {
            "name": "Mastava (Pirinçli Çorba)",
            "description": "Bir kaşık yoğurtla (qatiq) servis edilen doyurucu pirinçli çorba.",
            "steps": [
                "Eti küçük küpler halinde doğrayın; havuç, patates ve soğanı da küp küp doğrayın. Pirinci yıkayın.",
                "Kazanda yağı kızdırıp eti kavurun, ardından soğanı ekleyip kızartın.",
                "Havuç ve domatesi ekleyip 5 dakika kavurun, sonra kişi başına 1,5 kase su ekleyin.",
                "Kaynayınca patates ve pirinci ekleyin, tuz ve kimyonla tatlandırıp kısık ateşte 25-30 dakika pişirin.",
                "Kaselere alıp üzerine bir kaşık yoğurt ve ince doğranmış dereotu ekleyin. Afiyet olsun!",
            ],
        },
    },
    "shorva": {
        "en": {
            "name": "Shurpa",
            "description": "A clear, light and soothing boiled meat soup.",
            "steps": [
                "Rinse the bone-in meat and put it in a qozon of cold water (with the pre-soaked chickpeas, if using). Bring to the boil.",
                "As it comes to the boil, carefully skim off all the foam with a kapgir — that's the secret to a clear shurpa.",
                "Add a whole onion, lower the heat and simmer gently for 1-1.5 hours.",
                "Cut the carrots and potatoes into large pieces and add them with the tomato and bell pepper. Season with salt and pepper and simmer for another 25-30 minutes.",
                "Place meat and vegetables in bowls, pour the broth over and sprinkle with coriander. With warm bread — pure comfort!",
            ],
        },
        "tr": {
            "name": "Şurpa",
            "description": "Berrak, hafif ve şifalı haşlama et çorbası.",
            "steps": [
                "Kemikli eti yıkayıp soğuk sulu kazana koyun (nohut varsa önceden ıslatılmış nohutla birlikte) ve kaynamaya bırakın.",
                "Kaynamaya başlayınca köpüğünü kevgirle (kapgir) özenle alın — şurpanın berraklığı buna bağlı.",
                "Bütün bir soğan ekleyin, ateşi kısın ve 1-1,5 saat yavaş yavaş pişirin.",
                "Havuç ve patatesi iri doğrayıp domates ve biberle birlikte ekleyin. Tuz ve karabiber koyup 25-30 dakika daha pişirin.",
                "Kaselere et ve sebzeleri koyun, üzerine çorbayı dökün ve kişniş serpin. Sıcak ekmekle — keyfine doyum olmaz!",
            ],
        },
    },
    "dimlama": {
        "en": {
            "name": "Dimlama (Braised Meat & Vegetables)",
            "description": "Meat and vegetables steamed in their own juices — a spring and summer favourite.",
            "steps": [
                "Cut all the vegetables into large pieces and the meat into medium chunks.",
                "Pour oil into the bottom of the qozon, add the meat, lay onion rings on top and sprinkle with salt and cumin.",
                "Layer the carrots, potatoes, eggplant, bell pepper and tomatoes on top, sprinkling a little salt on each layer.",
                "Cover the top with cabbage leaves — they act as a lid. Don't add water; the vegetables release their own juices.",
                "Close the lid tightly and braise on low heat for 1-1.5 hours. Don't keep lifting the lid!",
                "Carefully turn it out onto a platter and serve with garlic and fresh herbs.",
            ],
        },
        "tr": {
            "name": "Dımlama (Sebzeli Et Buğulama)",
            "description": "Et ve sebzeler kendi buharında pişer — baharın ve yazın sevilen yemeği.",
            "steps": [
                "Bütün sebzeleri iri, eti orta boy parçalar halinde doğrayın.",
                "Kazanın dibine yağ koyun, eti yerleştirin, üzerine soğan halkalarını dizip tuz ve kimyon serpin.",
                "Ardından kat kat havuç, patates, patlıcan, biber ve domatesi dizin. Her kata biraz tuz serpin.",
                "En üste lahana yapraklarını örtün — kapak görevi görürler. Su eklemeyin, sebzeler kendi suyunu salar.",
                "Kapağı sıkıca kapatıp kısık ateşte 1-1,5 saat pişirin. Kapağı sık sık açmayın!",
                "Dikkatlice tabağa ters çevirin ve sarımsak, taze yeşilliklerle servis edin.",
            ],
        },
    },
    "manti": {
        "en": {
            "name": "Manti",
            "description": "Juicy meat dumplings steamed in a kaskan (multi-tier steamer).",
            "steps": [
                "Knead a firm dough from flour, salt, egg and water and let it rest for 30 minutes.",
                "Finely chop the meat and tail fat with a knife (skip the mincer and the manti will be juicier). Finely chop the onion and add it to the meat.",
                "Add salt, cumin, pepper and 2-3 tablespoons of cold water to the filling and mix well. If you have pumpkin, dice it small and add it too.",
                "Roll the dough out thin and cut it into 10x10 cm squares. Put a spoonful of filling on each and pinch the edges together neatly.",
                "Oil the kaskan tiers, arrange the manti and steam them over boiling water for 40-45 minutes.",
                "Serve hot with qatiq (yogurt) or sour cream. Enjoy!",
            ],
        },
        "tr": {
            "name": "Özbek Mantısı",
            "description": "Kaskanda (katlı buharda pişirme kabı) pişen bol sulu etli mantı.",
            "steps": [
                "Un, tuz, yumurta ve sudan sertçe bir hamur yoğurup 30 dakika dinlendirin.",
                "Eti ve kuyruk yağını bıçakla ince ince doğrayın (kıyma makinesinden geçirmezseniz mantı daha sulu olur). Soğanı da ince doğrayıp ete ekleyin.",
                "İç harca tuz, kimyon, karabiber ve 2-3 kaşık soğuk su ekleyip iyice karıştırın. Balkabağı varsa küçük küpler halinde ekleyin.",
                "Hamuru ince açıp 10x10 cm karelere kesin. Her birine bir kaşık iç koyup kenarlarını güzelce kapatın.",
                "Kaskan katlarını yağlayıp mantıları dizin ve kaynayan suyun buharında 40-45 dakika pişirin.",
                "Sıcak sıcak yoğurt ya da kaymakla servis edin. Afiyet olsun!",
            ],
        },
    },
    "chuchvara": {
        "en": {
            "name": "Chuchvara (Uzbek Dumplings)",
            "description": "Tiny folded dumplings served with qatiq (yogurt).",
            "steps": [
                "Knead a firm dough from flour, egg, salt and water and let it rest for 20-30 minutes.",
                "Mince the meat and onion together and season with salt and pepper.",
                "Roll the dough out thin and cut it into 4x4 cm squares. Put a little filling on each, fold into a triangle and join the two corners.",
                "Drop the chuchvara into boiling salted water and cook for another 5-7 minutes after they float to the surface.",
                "Serve in bowls with or without the broth, topped with qatiq and dill.",
            ],
        },
        "tr": {
            "name": "Çuçvara (Özbek Mantısı)",
            "description": "Minik minik kapatılan, yoğurtla servis edilen çuçvara.",
            "steps": [
                "Un, yumurta, tuz ve sudan sert bir hamur yoğurup 20-30 dakika dinlendirin.",
                "Eti ve soğanı birlikte kıyma haline getirip tuz ve karabiberle tatlandırın.",
                "Hamuru ince açıp 4x4 cm karelere kesin. Her birine biraz iç koyup üçgen şeklinde katlayın ve iki ucunu birleştirin.",
                "Çuçvaraları kaynayan tuzlu suya atın, yüzeye çıktıktan sonra 5-7 dakika daha haşlayın.",
                "Suyuyla ya da süzerek kaseye alın, üzerine yoğurt ve dereotu ekleyip servis edin.",
            ],
        },
    },
    "moshxorda": {
        "en": {
            "name": "Mashkhurda (Mung Bean Soup)",
            "description": "A thick, hearty soup of mung beans and rice.",
            "steps": [
                "Wash the mung beans and boil them in a separate pot until half-cooked (about 20 minutes).",
                "Heat the oil in the qozon and fry the finely chopped meat, then the onion and carrot. Add the tomatoes here if you have them.",
                "Pour in water and, once it boils, add the mung beans together with their cooking water.",
                "Add the rice and potatoes, season with salt and cumin and simmer on low heat for 25-30 minutes, until the rice is soft.",
                "Ladle into bowls and top with qatiq (yogurt). Perfect for chilly autumn and winter days!",
            ],
        },
        "tr": {
            "name": "Maşhurda (Maş Fasulyeli Çorba)",
            "description": "Maş fasulyesi ve pirinçle yapılan koyu, doyurucu çorba.",
            "steps": [
                "Maş fasulyesini yıkayıp ayrı bir tencerede yarı pişene kadar (20 dakika) haşlayın.",
                "Kazanda yağı kızdırıp küçük doğranmış eti, ardından soğan ve havucu kavurun. Domates varsa bu aşamada ekleyin.",
                "Su ekleyin, kaynayınca maş fasulyesini suyuyla birlikte ilave edin.",
                "Pirinç ve patatesi ekleyip tuz ve kimyonla tatlandırın, pirinç dağılana kadar kısık ateşte 25-30 dakika pişirin.",
                "Kaselere alıp üzerine yoğurt ekleyin. Serin sonbahar ve kış günleri için birebir!",
            ],
        },
    },
}
