# ============================
# إعدادات الوحدات والاستراتيجيات
# ============================

import os

GATHERN_PHONE      = os.environ.get("GATHERN_PHONE", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

CITY_ID = "1061"  # الخرج


# ساعات التشغيل
START_HOUR = 11  # 11 صباحاً
END_HOUR = 23     # 11 مساءً
EVENING_HOUR = 19 # 7 مساءً - تغيير الاستراتيجية

# الوحدات
UNITS = [
    # مساكن ترف - الخزامى
    {"name": "ترف 3", "unit_id": "171611", "chalet_id": "121833", "type": "شقة_متوسطة", "neighborhood": "الخزامى"},
    {"name": "ترف 4", "unit_id": "172254", "chalet_id": "121833", "type": "شقة_متوسطة", "neighborhood": "الخزامى"},
    {"name": "ترف 5", "unit_id": "177451", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى"},
    {"name": "ترف 6", "unit_id": "177498", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى"},

    # مساكن ترف - المنتزه
    {"name": "ترف 7",  "unit_id": "177494", "chalet_id": "126077", "type": "استديو_عادي",  "neighborhood": "المنتزه"},
    {"name": "ترف 8",  "unit_id": "177492", "chalet_id": "126077", "type": "استديو_عادي",  "neighborhood": "المنتزه"},

    # مساكن ترف - الورود
    {"name": "ترف 9",  "unit_id": "225320", "chalet_id": "130246", "type": "شقة_مميزة",    "neighborhood": "الورود"},
    {"name": "ترف 10", "unit_id": "183003", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود"},
    {"name": "ترف 11", "unit_id": "183008", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود"},
    {"name": "ترف 12", "unit_id": "183016", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود"},

    # مساكن ترف - الورود 2
    {"name": "ترف 13", "unit_id": "214892", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود"},
    {"name": "ترف 14", "unit_id": "214894", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود"},
    {"name": "ترف 15", "unit_id": "214952", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود"},
    {"name": "ترف 16", "unit_id": "214991", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود"},
    {"name": "ترف 17", "unit_id": "214995", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود"},

    # مساكن ترف - الهدا
    {"name": "ترف 18", "unit_id": "243848", "chalet_id": "173065", "type": "شقة_مميزة",      "neighborhood": "الهدا"},
    {"name": "ترف 19", "unit_id": "241775", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
    {"name": "ترف 21", "unit_id": "242199", "chalet_id": "173065", "type": "شقة_مميزة",      "neighborhood": "الهدا"},
    {"name": "ترف 22", "unit_id": "242211", "chalet_id": "173065", "type": "شقة_غرفتين",     "neighborhood": "الهدا"},
    {"name": "ترف 23", "unit_id": "243598", "chalet_id": "173065", "type": "شقة_غرفتين",     "neighborhood": "الهدا"},
    {"name": "ترف 26", "unit_id": "241890", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
    {"name": "ترف 27", "unit_id": "242428", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
    {"name": "ترف 28", "unit_id": "242505", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
    {"name": "ترف 30", "unit_id": "243973", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
    {"name": "ترف 31", "unit_id": "243974", "chalet_id": "173065", "type": "استديو_مميز",    "neighborhood": "الهدا"},
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