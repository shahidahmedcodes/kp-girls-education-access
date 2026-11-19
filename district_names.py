import re

ALIASES = {
    "abbottabad": "Abbottabad", "bannu": "Bannu", "battagram": "Battagram",
    "buner": "Bunner", "bunner": "Bunner", "charsadda": "Charsadda",
    "chitrallower": "Chitral Lower", "lowerchitral": "Chitral Lower",
    "chitralupper": "Chitral Upper", "upperchitral": "Chitral Upper",
    "dikhan": "Dera Ismail Khan", "deraismailkhan": "Dera Ismail Khan",
    "dirbala": "Dir Upper", "dirpayan": "Dir Lower", "hangu": "Hangu", "haripur": "Haripur",
    "karak": "Karak", "kohat": "Kohat",
    "kolaipalas": "Kolai Palas", "kolaipallas": "Kolai Palas",
    "lakki": "Lakki Marwat", "lakkimarwat": "Lakki Marwat",
    "lowerkohistan": "Kohistan Lower", "kohistanlower": "Kohistan Lower",
    "upperkohistan": "Kohistan Upper", "kohistanupper": "Kohistan Upper",
    "malakand": "Malakand", "mansehra": "Mansehra", "mardan": "Mardan",
    "nowshehra": "Nowshera", "nowshera": "Nowshera", "peshawar": "Peshawar",
    "shangla": "Shangla", "swabi": "Swabi", "swat": "Swat", "tank": "Tank", "torghar": "Torghar",
    "bajaur": "Bajaur", "khyber": "Khyber", "kurram": "Kurram", "kurraam": "Kurram",
    "mohmand": "Mohmand", "northwaziristan": "North Waziristan", "orakzai": "Orakzai",
    "southwaziristan": "South Waziristan",
    "subdivbettani": "SD Bhetani (Lakki Marwat)", "subdivbhetani": "SD Bhetani (Lakki Marwat)",
    "subdivdarraadamkhel": "SD Dara Adam Khel (Kohat)", "subdivdaraadamkhel": "SD Dara Adam Khel (Kohat)",
    "subdivdrazanda": "SD Darazinda (Dera Ismail Khan)", "subdivdarazinda": "SD Darazinda (Dera Ismail Khan)",
    "subdivhassankhel": "SD Hassan Khel (Peshawar)", "subdivhasankhel": "SD Hassan Khel (Peshawar)",
    "subdivjandola": "SD Jandola (Tank)", "subdivwazir": "SD Wazir (Bannu)",
}


def make_key(name):
    return re.sub(r"[^a-z]", "", name.lower())


def canonical(name):
    return ALIASES.get(make_key(name))