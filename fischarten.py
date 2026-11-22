"""Alle Fischarten aus Russian Fishing 4 (deutsche Namen, wie im Spiel).

Abgeschrieben aus der Fischübersicht im Spiel. Kommen durch ein Update neue
Fische dazu, hier einfach ergänzen (Reihenfolge egal, wird sortiert angezeigt).
"""

FISCHARTEN = [
    "Aal", "Aalmutter", "Adlerfisch", "Aland", "Albino Gerahmter Spiegelkarpfen",
    "Albino-Barbe", "Albino-Graskarpfen", "Albino-Lederkarpfen", "Albino-Schuppenkarpfen",
    "Albino-Spiegelkarpfen", "Albino-Wels", "Albino-Zeilkarpfen", "Alfonsino", "Alligatorhecht",
    "Amerikanischer Maifisch", "Amurwels", "Aral-Barbe", "Arktische Äsche", "Arktische Maräne",
    "Arktischer Rochen", "Atlantischer Hering", "Atlantischer Kabeljau", "Atlantischer Lachs",
    "Augenfleckenkammbarsch", "Auster", "Bachforelle", "Bachsaibling", "Bachschmerle",
    "Baikal-Maräne", "Baltischer Stör", "Barbe", "Beluga-Stör", "Blauer Seewolf",
    "Blauer Sonnenbarsch", "Blauer Wittling", "Blauflossen-Thunfisch", "Blauleng", "Brachse",
    "Brachymystax", "Braschnikow-Hering",

    "Buckellachs", "C2 SuperFreak", "Chereshnev Saibling", "Conger", "Dinkelsbühler Lederkarpfen",
    "Dinkelsbühler Spiegelkarpfen", "Dinkelsbühler Zeilenkarpfen", "Döbel", "Doggerscharbe",
    "Dolly-Varden-Forelle", "Donauhering", "Don-Kaulbarsch", "Dornhai", "Dreistachliger Stichling",
    "Dryagin-Saibling", "Esmarks Aalmutter", "Europäische Äsche", "Europäische Sardine",
    "Europäischer Seehecht", "F1 Karpfen", "Felsenbarsch", "Fernöstliches Neunauge", "Flachkopfwels",
    "Fluss - Wandermuschel", "Flussbarsch", "Flusskrebs", "Flussmuschel", "Forellenbarsch",
    "Fußballfisch", "Gefleckter Knochenhecht", "Gefleckter Seewolf", "Geister Zeilkarpfen",
    "Geister-Gerahmter Spiegelkarpfen", "Geister-Lederkarpfen", "Geister-Schuppenkarpfen",
    "Geister-Spiegelkarpfen", "Gemeine Miesmuschel", "Gemeiner Kalmar", "Gepunkteter Barsch",
    "Gerahmter Spiegelkarpfen",

    "Gestreifter Seewolf", "Getüpfelter Gabelwels", "Gewöhnlicher Leng", "Giebel", "Glatt-Stör",
    "Goldener Spiegelkarpfen", "Goldkarpfen", "Goldschleie", "Gotteslachs", "Grasfrosch",
    "Grenadierfisch", "Grönlandhai", "Große Bodenrenke", "Großmäuliger Büffelfisch", "Gründling",
    "Güster", "Hasel", "Hecht", "Heilbutt", "Heringshai", "Hi Utsuri", "Isländische Kammmuschel",
    "Japanischer Saibling", "Kaluga-Hausen", "Kamtschatka-Regenbogenforelle", "Karausche",
    "Kaspi-Maifisch", "Kaspineunauge", "Kaspische Forelle", "Kaspischer Schwarzrücken-Hering",
    "Kaulbarsch", "Keta-Lachs", "Kleine Bodenrenke", "Kleine Sibirische Maräne", "Kleiner Rotbarsch",
    "Kliesche", "Klotzsaibling", "Kohaku", "Köhler", "Königskrabbe",

    "Königslachs", "Kragenhai", "Kuori Felchen", "Kürbiskernbarsch", "Kutum", "Kvolsdorfsky-Schleie",
    "Ladoga Lachs", "Ladogasee Felchen", "Ladoga-Stör", "Langnasen-Saugdöbel", "Langohr-Aalmutter",
    "Laube", "Lederkarpfen", "Lenok", "Ludoga-Renke", "Ludoga-Saibling", "Lumb", "Makrele",
    "Makrelenhecht", "Mameshibori Goshiki", "Marmorkarpfen", "Masu-Lachs", "Masu-Lachs (Sesshaft)",
    "Midori goi", "Mongolische Rotfeder", "Muksun", "Narumi Asagi", "Nase", "Neiva", "Nelma",
    "Neunstachliger Stichling", "Orenji Ogon", "Ostbrasse", "Ostrog Felchen", "Ostsibirische Äsche",
    "Pazifisches Neunauge", "Peledmaräne", "Persischer Stör", "Prosopium", "Quappe",

    "Rapfen", "Regenbogenforelle", "Regenbogenstint", "Riesenhai", "Ripus-Maräne", "Rotauge",
    "Rotbarsch", "Rotfeder", "Rotlachs", "Rotohr-Sonnenbarsch", "Russischer Stör", "Schellfisch",
    "Scherg", "Schläfergrundel", "Schlammpeitzger", "Schleie", "Scholle", "Schuppenkarpfen",
    "Schwarzbarsch", "Schwarzer Amur", "Schwarzer Büffelfisch", "Schwarzer Crappie",
    "Schwarzer Degenfisch", "Schwarzer Heilbutt", "Schwarzes Felchen", "Schwarzfisch",
    "Schwarzmeer-Beluga", "Schwarzmeerforelle", "Schwarzmeer-Kutum", "Schwarzmeer-Seelaube",
    "Schwertfisch", "See-Elritze", "Seeforelle", "Seehase", "Seekatze", "Seelaube", "Seesaibling",
    "Seesaibling Kuorsky", "Seeskorpion", "Seeteufel",

    "Sewan-Forelle", "Sibirische Groppe", "Sibirische Plötze", "Sibirischer Gründling",
    "Sibirischer Hasel", "Sibirischer Sterlet", "Sibirischer Stör", "Sibirisches Bachneunauge",
    "Sichling", "Silberkarpfen", "Silberlachs", "Spiegelkarpfen", "Steinbutt", "Steinköhler",
    "Steinschill", "Sterlet", "Sternrochen", "Stint", "Streifenbarsch", "Südl. Neunstachliger Stichling",
    "Sumpfelritze", "Süßwassertrommler", "Svir Felchen", "Taimen", "Taschenkrebs", "Tiefenrotbarsch",
    "Tugun", "Tunguska Rotauge", "Tyulka-Sardine", "Ugui", "Ukrainisches Bachneunauge",
    "Valaam-Buckelmaräne", "Vuoksi-Renke", "Walleye", "Warmouth", "Weißbarsch", "Weißer Amur",
    "Weißer Crappie", "Weißlachs", "Wels",

    "Wildkarpfen", "Wittling", "Wobla", "Wolchow-Renke", "Wrackbarsch", "Yotsushiro", "Zährte",
    "Zander", "Zeilkarpfen", "Zobel", "Zope", "Zwergmaräne",
]
