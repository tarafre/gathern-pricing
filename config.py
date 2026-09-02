# ============================
# إعدادات الوحدات والاستراتيجيات
# ============================

import os

GATHERN_PHONE      = os.environ.get("GATHERN_PHONE", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
AIRBNB_EMAIL       = os.environ.get("AIRBNB_EMAIL", "")
AIRBNB_PASSWORD    = os.environ.get("AIRBNB_PASSWORD", "")

CITY_ID = "1061"  # الخرج


# ساعات التشغيل
START_HOUR = 0
END_HOUR = 23
EVENING_HOUR = 19

# الوحدات
UNITS = [
    # مساكن ترف - الخزامى
    {"name": "ترف 3",  "unit_id": "171611", "chalet_id": "121833", "type": "شقة_متوسطة",  "neighborhood": "الخزامى", "airbnb_id": "1403873856157704173"},
    {"name": "ترف 4",  "unit_id": "172254", "chalet_id": "121833", "type": "شقة_متوسطة",  "neighborhood": "الخزامى", "airbnb_id": "1403880288657220158"},
    {"name": "ترف 5",  "unit_id": "177451", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى", "airbnb_id": "1403887613093990917"},
    {"name": "ترف 6",  "unit_id": "177498", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى", "airbnb_id": "1403890731610286868"},

    # مساكن ترف - المنتزه
    {"name": "ترف 7",  "unit_id": "177494", "chalet_id": "126077", "type": "استديو_عادي", "neighborhood": "المنتزه", "airbnb_id": "1403892931262753688"},
    {"name": "ترف 8",  "unit_id": "177492", "chalet_id": "126077", "type": "استديو_عادي", "neighborhood": "المنتزه", "airbnb_id": "1403895880859335789"},

    # مساكن ترف - الورود
    {"name": "ترف 9",  "unit_id": "225320", "chalet_id": "130246", "type": "شقة_مميزة",    "neighborhood": "الورود", "airbnb_id": "1578502808718815802"},
    {"name": "ترف 10", "unit_id": "183003", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "airbnb_id": "1411633638883998521"},
    {"name": "ترف 11", "unit_id": "183008", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "airbnb_id": "1411640018999571756"},
    {"name": "ترف 12", "unit_id": "183016", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "airbnb_id": "1411645674458307792"},

    # مساكن ترف - الورود 2
    {"name": "ترف 13", "unit_id": "214892", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "airbnb_id": "1526107256848780424"},
    {"name": "ترف 14", "unit_id": "214894", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "airbnb_id": "1527410361272410238"},
    {"name": "ترف 15", "unit_id": "214952", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "airbnb_id": "1527415997319803542"},
    {"name": "ترف 16", "unit_id": "214991", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "airbnb_id": "1527418360232276527"},
    {"name": "ترف 17", "unit_id": "214995", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "airbnb_id": "1527420845702037136"},

    # مساكن ترف - الهدا
    {"name": "ترف 18", "unit_id": "243848", "chalet_id": "173065", "type": "شقة_مميزة",   "neighborhood": "الهدا", "airbnb_id": ""},
    {"name": "ترف 19", "unit_id": "241775", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": "1758811686422595379"},
    {"name": "ترف 21", "unit_id": "242199", "chalet_id": "173065", "type": "شقة_مميزة",   "neighborhood": "الهدا", "airbnb_id": "1763207156054129836"},
    {"name": "ترف 22", "unit_id": "242211", "chalet_id": "173065", "type": "شقة_غرفتين",  "neighborhood": "الهدا", "airbnb_id": "1763399005668449934"},
    {"name": "ترف 23", "unit_id": "243598", "chalet_id": "173065", "type": "شقة_غرفتين",  "neighborhood": "الهدا", "airbnb_id": "1763354205940132513"},
    {"name": "ترف 26", "unit_id": "241890", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": "1759396644405598104"},
    {"name": "ترف 27", "unit_id": "242428", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": "1657221201729694360"},
    {"name": "ترف 28", "unit_id": "242505", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": "1759404954341686911"},
    {"name": "ترف 30", "unit_id": "243973", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": "1759410602069272961"},
    {"name": "ترف 31", "unit_id": "243974", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "airbnb_id": ""},
]

# الاستراتيجية الافتراضية لكل نوع (نسبة مئوية)
DEFAULT_STRATEGY = {
    "شقة_مميزة":    "+20",
    "شقة_متوسطة":  "0",
    "شقة_عادية":   "-20",
    "شقة_غرفتين":  "+30",
    "استديو_مميز": "+20",
    "استديو_متوسط": "0",
    "استديو_عادي": "-20",
}