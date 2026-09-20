# ============================
# إعدادات الوحدات والاستراتيجيات
# ============================

import os

GATHERN_PHONE      = os.environ.get("GATHERN_PHONE", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
NUZUL_PHONE        = os.environ.get("NUZUL_PHONE", "")
NUZUL_PASSWORD     = os.environ.get("NUZUL_PASSWORD", "")
NUZUL_BACKEND      = "moxihu7427.nzl-backend.com"

CITY_ID = "1061"  # الخرج


# ساعات التشغيل
START_HOUR = 0
END_HOUR = 23
EVENING_HOUR = 19

# الوحدات — nuzul_id و nuzul_rate_plan تُستخدم لتحديث Airbnb+Booking عبر نزل
UNITS = [
    # مساكن ترف - الخزامى
    {"name": "ترف 3",  "unit_id": "171611", "chalet_id": "121833", "type": "شقة_متوسطة",  "neighborhood": "الخزامى", "nuzul_id": 46556, "nuzul_rate_plan": "82b3ca47-eab1-4acd-a18c-119cf401f57a"},
    {"name": "ترف 4",  "unit_id": "172254", "chalet_id": "121833", "type": "شقة_متوسطة",  "neighborhood": "الخزامى", "nuzul_id": 46557, "nuzul_rate_plan": "f75930c6-7a86-4bab-bd43-f2be45da211e"},
    {"name": "ترف 5",  "unit_id": "177451", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى", "nuzul_id": 46558, "nuzul_rate_plan": "7721d54b-774a-4423-ac65-64c2a62d5ffa"},
    {"name": "ترف 6",  "unit_id": "177498", "chalet_id": "121833", "type": "شقة_عادية",   "neighborhood": "الخزامى", "nuzul_id": 0,     "nuzul_rate_plan": ""},

    # مساكن ترف - المنتزه
    {"name": "ترف 7",  "unit_id": "177494", "chalet_id": "126077", "type": "استديو_عادي", "neighborhood": "المنتزه", "nuzul_id": 46560, "nuzul_rate_plan": "29e3ebb7-3f90-4688-a915-5ea4a40ea10c"},
    {"name": "ترف 8",  "unit_id": "177492", "chalet_id": "126077", "type": "استديو_عادي", "neighborhood": "المنتزه", "nuzul_id": 46561, "nuzul_rate_plan": "5253967e-b498-4a00-a93d-ad12f63e3b15"},

    # مساكن ترف - الورود
    {"name": "ترف 9",  "unit_id": "225320", "chalet_id": "130246", "type": "شقة_مميزة",    "neighborhood": "الورود", "nuzul_id": 46570, "nuzul_rate_plan": "30c1d596-0842-4e53-8459-e86bf7e18f44"},
    {"name": "ترف 10", "unit_id": "183003", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "nuzul_id": 46562, "nuzul_rate_plan": "5fae5847-be64-4ec7-a8eb-4021a056c518"},
    {"name": "ترف 11", "unit_id": "183008", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "nuzul_id": 46563, "nuzul_rate_plan": "55b93f08-e527-47ce-845c-38366017ad1e"},
    {"name": "ترف 12", "unit_id": "183016", "chalet_id": "130246", "type": "استديو_متوسط", "neighborhood": "الورود", "nuzul_id": 46564, "nuzul_rate_plan": "a6b52c1b-a9cc-409d-b6d1-d7a0e9c27432"},

    # مساكن ترف - الورود 2
    {"name": "ترف 13", "unit_id": "214892", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "nuzul_id": 46565, "nuzul_rate_plan": "efc10966-6c77-49be-a98d-3ac1a8dabeab"},
    {"name": "ترف 14", "unit_id": "214894", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "nuzul_id": 46566, "nuzul_rate_plan": "5871bad5-616e-44ba-b858-fdb4f7e6fd58"},
    {"name": "ترف 15", "unit_id": "214952", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "nuzul_id": 46567, "nuzul_rate_plan": "e6f69ddf-4674-4b91-8f5c-9003e96fd32d"},
    {"name": "ترف 16", "unit_id": "214991", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "nuzul_id": 46568, "nuzul_rate_plan": "a47a60a0-7cb1-4ab6-9325-647dddda8487"},
    {"name": "ترف 17", "unit_id": "214995", "chalet_id": "153394", "type": "شقة_مميزة", "neighborhood": "الورود", "nuzul_id": 46569, "nuzul_rate_plan": "4e363e14-1a5c-4903-a253-1c1a702249fb"},

    # مساكن ترف - الهدا
    {"name": "ترف 18", "unit_id": "243848", "chalet_id": "173065", "type": "شقة_مميزة",   "neighborhood": "الهدا", "nuzul_id": 49770, "nuzul_rate_plan": ""},
    {"name": "ترف 19", "unit_id": "241775", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49771, "nuzul_rate_plan": "b661e845-8bba-4898-a635-92e9bc1edda0"},
    {"name": "ترف 21", "unit_id": "242199", "chalet_id": "173065", "type": "شقة_مميزة",   "neighborhood": "الهدا", "nuzul_id": 49774, "nuzul_rate_plan": "643db913-9c66-4a25-ba5c-937da1058984"},
    {"name": "ترف 22", "unit_id": "242211", "chalet_id": "173065", "type": "شقة_غرفتين",  "neighborhood": "الهدا", "nuzul_id": 49775, "nuzul_rate_plan": "9ee954f0-67d2-40f2-a111-f840461cd727"},
    {"name": "ترف 23", "unit_id": "243598", "chalet_id": "173065", "type": "شقة_غرفتين",  "neighborhood": "الهدا", "nuzul_id": 49776, "nuzul_rate_plan": "3b73cc07-a69e-4ddf-8941-200581ff199d"},
    {"name": "ترف 26", "unit_id": "241890", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49778, "nuzul_rate_plan": "ea8f9ee6-fba9-40ec-a89f-8868d02e59c4"},
    {"name": "ترف 27", "unit_id": "242428", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49779, "nuzul_rate_plan": "18323b78-7424-4b10-a378-7db3633cb3ae"},
    {"name": "ترف 28", "unit_id": "242505", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49780, "nuzul_rate_plan": "54e3aa09-4075-488e-b892-5112c53e8339"},
    {"name": "ترف 24", "unit_id": "",       "chalet_id": "",       "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49773, "nuzul_rate_plan": "b3b7565a-4fa4-4d84-a86d-3402c5df3802"},
    {"name": "ترف 25", "unit_id": "",       "chalet_id": "",       "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49777, "nuzul_rate_plan": "09ca9972-b769-4226-9b29-9e32506e18a4"},
    {"name": "ترف 30", "unit_id": "243973", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49782, "nuzul_rate_plan": "0012caa0-a79c-47de-9fe2-c95257052de5"},
    {"name": "ترف 31", "unit_id": "243974", "chalet_id": "173065", "type": "استديو_مميز", "neighborhood": "الهدا", "nuzul_id": 49783, "nuzul_rate_plan": "bf6052aa-e92e-4fa9-9198-6622f21755cb"},

    # وحدات مدينة أخرى — لا تحديث تلقائي (manual_only)
    {"name": "ترف 1-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 46510, "nuzul_rate_plan": "bafaad9c-057f-47c2-8959-35e2b14ce84d", "manual_only": True},
    {"name": "ترف 2-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 46511, "nuzul_rate_plan": "e475dd00-43d5-4ce5-8c35-717d50d55864", "manual_only": True},
    {"name": "ترف 3-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 46512, "nuzul_rate_plan": "827b35ed-e3e1-489f-9e77-9733ed3402ba", "manual_only": True},
    {"name": "ترف 4-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 53336, "nuzul_rate_plan": "bc4c6046-daa8-4627-80e7-e9ea89704aeb", "manual_only": True},
    {"name": "ترف 5-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 53337, "nuzul_rate_plan": "e381b636-e09f-4861-8bff-8fa800b9776d", "manual_only": True},
    {"name": "ترف 6-MJ", "unit_id": "", "chalet_id": "", "type": "شقة_مميزة", "neighborhood": "MJ", "nuzul_id": 53338, "nuzul_rate_plan": "99a74cc7-9501-4458-a693-36509f7f90d2", "manual_only": True},
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