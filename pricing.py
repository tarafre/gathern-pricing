#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, time, re, statistics, requests, json, csv
from datetime import datetime
from playwright.sync_api import sync_playwright

# حمّل المتغيرات المحلية عند التشغيل على الجهاز
_env_file = os.path.join(os.path.dirname(__file__), ".env.local")
if os.path.exists(_env_file):
    for _line in open(_env_file):
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

BASE_DIR = os.path.dirname(__file__)

def load_runtime_config():
    path = os.path.join(BASE_DIR, "runtime_config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_history(today, now_str, data, apt_avg, std_avg, updated, total):
    path = os.path.join(BASE_DIR, "data", "history.csv")
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["date","time","apt_avg","studio_avg","apt_count","studio_count","occ_apt","occ_studio","occ_all","updated","total"])
        w.writerow([today, now_str, apt_avg, std_avg,
                    len(data["all_apt"]), len(data["all_studio"]),
                    data["occ_apt"], data["occ_studio"], data["occ_all"], updated, total])

from config import *

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"})
    except: pass

# سلّم الاستراتيجيات بالترتيب من الأعلى للأدنى
STRATEGY_LADDER = ["+30", "+20", "+10", "0", "-10", "-15", "-20", "-30"]

# توافق مع الأسماء القديمة
LEGACY_MAP = {
    "high_plus": "+30", "high": "+20", "mid": "0",
    "low": "-20", "low_extra": "-30",
}

def calc_price(base, strategy):
    strategy = LEGACY_MAP.get(strategy, strategy)
    try:
        pct = int(strategy)
        return round(base * (1 + pct / 100))
    except (ValueError, TypeError):
        return round(base)

def evening_downgrade(strategy):
    strategy = LEGACY_MAP.get(strategy, strategy)
    try:
        idx = STRATEGY_LADDER.index(strategy)
        return STRATEGY_LADDER[min(idx + 1, len(STRATEGY_LADDER) - 1)]
    except ValueError:
        return strategy

PRICE_CAP = 450  # فوق هذا السعر = محجوز فعلياً (صاحب الوحدة رفع السعر لمنع الحجز)

def trimmed_mean(prices, pct=0.10):
    """متوسط مشذّب: نحذف أعلى وأدنى pct% ونأخذ متوسط الباقي."""
    if not prices:
        return 0
    s = sorted(prices)
    cut = max(1, int(len(s) * pct))
    trimmed = s[cut:-cut] if len(s) > cut * 2 else s
    return round(sum(trimmed) / len(trimmed))

def collect_prices(_page=None):
    """تجمع أسعار السوق مباشرة من API قاذرإن بدون متصفح."""
    from datetime import timezone, timedelta
    print("جمع اسعار المنافسين...")
    ksa_now  = datetime.now(timezone.utc) + timedelta(hours=3)
    today    = ksa_now.strftime("%Y-%m-%d")
    tomorrow = (ksa_now + timedelta(days=1)).strftime("%Y-%m-%d")

    apt_all, studio_all, apt_avail, studio_avail = [], [], [], []
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json",
        "Referer": "https://gathern.co/",
    }

    for page_num in range(1, 33):
        params = {
            "chalet_cats[]": ["6", "7", "8", "9"],
            "city": CITY_ID,
            "checkin": today,
            "checkout": tomorrow,
            "page": page_num,
            "orderby": "points",
            "lang": "ar",
        }
        try:
            r = requests.get(
                "https://msapi.gathern.co/search/api/v1/search-units",
                params=params, headers=headers, timeout=15
            )
            units = r.json().get("items", [])
        except Exception as e:
            print(f"  خطأ صفحة {page_num}: {e}")
            break

        if not units:
            break

        for u in units:
            try:
                title = (u.get("unit_custom_title") or u.get("chalet_title") or "").strip()
                if "استديو" in title or "استوديو" in title:
                    utype = "studio"
                elif "شقة" in title or "شقه" in title:
                    utype = "apt"
                else:
                    continue

                reviews = int(u.get("total_reviews") or u.get("total_present") or 0)
                if reviews < 3:
                    continue

                price = float(u.get("cancel_price") or u.get("final_price") or 0)
                if price < 80:
                    continue

                # فوق 450 = صاحب الوحدة رفع السعر ليمنع الحجز → تُعدّ محجوزة
                is_avail = bool(u.get("isUnitAvailable", True)) and price <= PRICE_CAP

                # نضيف فقط الوحدات ضمن نطاق سعري معقول للإحصاء
                if price > PRICE_CAP:
                    continue

                if utype == "studio":
                    studio_all.append(price)
                    if is_avail: studio_avail.append(price)
                else:
                    apt_all.append(price)
                    if is_avail: apt_avail.append(price)
            except:
                pass

        print(f"  صفحة {page_num}: {len(units)} وحدة")

    apt_booked    = len(apt_all)    - len(apt_avail)
    studio_booked = len(studio_all) - len(studio_avail)
    total_all     = len(apt_all) + len(studio_all)
    total_booked  = apt_booked + studio_booked
    occ_apt    = round(apt_booked    / len(apt_all)    * 100) if apt_all    else 0
    occ_studio = round(studio_booked / len(studio_all) * 100) if studio_all else 0
    occ_all    = round(total_booked  / total_all       * 100) if total_all  else 0
    print(f"  شقق: {len(apt_all)} محجوز {apt_booked} ({occ_apt}%) | استديوهات: {len(studio_all)} محجوز {studio_booked} ({occ_studio}%) | الإجمالي: {occ_all}%")
    return {
        "all_apt": apt_all, "all_studio": studio_all,
        "avail_apt": apt_avail, "avail_studio": studio_avail,
        "occ_apt": occ_apt, "occ_studio": occ_studio, "occ_all": occ_all,
        "apt_booked": apt_booked, "studio_booked": studio_booked,
        "total_booked": total_booked, "total_all": total_all,
    }

def on_app(page):
    """هل نحن داخل لوحة التحكم؟ بدون تنقل."""
    return "business.gathern.co/app" in page.url and "/login" not in page.url

def login(page):
    print("تسجيل الدخول...")
    # فحص الجلسة بالانتقال للتقويم
    page.goto("https://business.gathern.co/app/calendar")
    page.wait_for_load_state("domcontentloaded", timeout=30000)
    time.sleep(2)
    if on_app(page):
        print("الجلسة لا تزال نشطة")
        return True

    # نسجّل دخول
    page.goto("https://business.gathern.co/login")
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    time.sleep(3)
    page.locator("input").first.fill(GATHERN_PHONE)
    time.sleep(1)
    page.locator("button[type='submit']").first.click()
    time.sleep(4)

    # دخل مباشرة بدون OTP؟
    if on_app(page):
        print("تم تسجيل الدخول مباشرة!")
        return True

    # نحتاج OTP — نبقى على صفحة OTP ولا ننتقل منها
    send_telegram("مطلوب رمز OTP - ارسله هنا مباشرة")
    print(f"انتظار OTP... URL: {page.url}")
    r0 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": -1}).json()
    last_id = r0["result"][-1]["update_id"] if r0.get("result") else None

    for _ in range(60):
        time.sleep(5)
        if on_app(page):
            print("تم تسجيل الدخول!")
            return True
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": -1}).json()
            updates = r.get("result", [])
            if not updates:
                continue
            update = updates[-1]
            if last_id and update["update_id"] <= last_id:
                continue
            last_msg = update.get("message", {}).get("text", "").strip()
            if last_msg.isdigit() and 4 <= len(last_msg) <= 6:
                last_id = update["update_id"]
                print(f"  OTP: {last_msg} | URL: {page.url}")
                boxes = page.locator("input").all()
                print(f"  inputs: {len(boxes)}")
                for i, d in enumerate(list(last_msg)):
                    if i < len(boxes):
                        boxes[i].fill(d)
                        time.sleep(0.3)
                page.locator("button[type='submit']").first.click()
                time.sleep(4)
                if on_app(page):
                    print("تم تسجيل الدخول!")
                    return True
        except Exception as e:
            print(f"خطأ OTP: {e}")
    return on_app(page)

def is_booked(page, today):
    try:
        day = str(int(today.split("-")[2]))
        day_cells = page.locator("#drag-calendar > div").all()
        for cell in day_cells:
            try:
                span = cell.locator("span").first
                if span.inner_text(timeout=1000).strip() == day:
                    booked = cell.locator("[class*='dit1lc'], [class*='1glaw3f']").count()
                    return booked > 0
            except:
                continue
        return False
    except:
        return False

def close_popup(page):
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except: pass
    try:
        btns = page.locator("button").all()
        for btn in btns:
            txt = btn.inner_text()
            if any(x in txt for x in ["ذكرني", "لاحقا", "اغلق", "×", "X"]):
                btn.click()
                time.sleep(0.5)
                break
    except: pass

def close_dialog(page):
    try:
        page.keyboard.press("Escape")
        time.sleep(0.5)
    except: pass
    try:
        drawer = page.locator(".MuiDrawer-paper").first
        if drawer.is_visible():
            drawer.locator("button").first.click()
            time.sleep(0.5)
    except: pass
    try:
        dialog = page.locator("[role='dialog']").first
        if dialog.is_visible():
            dialog.locator("button").first.click()
            time.sleep(0.5)
    except: pass

def select_unit(page, unit_id, chalet_id):
    try:
        page.goto(f"https://business.gathern.co/app/calendar/unit?chalet={chalet_id}&unit_id={unit_id}")
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        time.sleep(2)
        dropdown = page.locator("div[role='button']:has-text('ترف'), div[role='combobox']").first
        if dropdown.is_visible():
            dropdown.click()
            time.sleep(1)
            option = page.locator(f"li[data-value='{unit_id}'], [role='option']:has-text('{unit_id}')").first
            if option.is_visible():
                option.click()
                time.sleep(2)
                return True
        return True
    except:
        return True

def update_price(page, unit, price, today):
    unit_id = unit["unit_id"]
    name = unit["name"]
    chalet_id = unit["chalet_id"]
    try:
        page.goto(f"https://business.gathern.co/app/calendar/unit?chalet={chalet_id}&unit_id={unit_id}")
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        time.sleep(3)
        close_dialog(page)
        try:
            page.wait_for_selector("#unit-select", timeout=15000)
        except:
            print(f"  {name}: الصفحة ما حمّلت")
            return "err_load"
        current_unit = page.locator("#unit-select").inner_text(timeout=3000).strip()
        unit_num = name.replace("ترف ", "").strip()
        if unit_num not in current_unit:
            select_btn = page.locator("#unit-select")
            select_btn.click()
            option = page.locator(f"[role='option'][data-value='{unit_id}']").first
            try:
                option.wait_for(state="visible", timeout=8000)
                option.click()
                time.sleep(1)
            except:
                print(f"  {name}: ما لقيت الخيار في القائمة")
                page.keyboard.press("Escape")
                return "err_option"
        try:
            page.wait_for_selector("#drag-calendar", timeout=15000)
        except:
            print(f"  {name}: التقويم ما حمّل")
            return "err_calendar"
        day = str(int(today.split("-")[2]))
        day_cells = page.locator("#drag-calendar > div[role='button']").all()
        target_cell = None
        for cell in day_cells:
            try:
                span_text = cell.locator("p span").first.inner_text(timeout=500).strip()
                if span_text == day:
                    target_cell = cell
                    break
            except:
                continue
        if not target_cell:
            print(f"  {name}: ما لقيت اليوم في التقويم")
            return "err_day"
        target_cell.click()
        time.sleep(1.5)
        drawer = page.locator(".MuiDrawer-paper").first
        if not drawer.is_visible():
            print(f"  {name}: الـ drawer ما فتح")
            return "err_drawer"
        guest_booked = drawer.locator("p:has-text('مؤكد حجز'), span:has-text('حجز مؤكد')").count()
        if guest_booked > 0:
            print(f"  {name}: محجوزة بضيف")
            page.keyboard.press("Escape")
            return "booked_guest"
        manual_blocked = drawer.locator("p:has-text('الوحدة مشغولة')").count()
        if manual_blocked > 0:
            print(f"  {name}: مشغولة يدوياً")
            page.keyboard.press("Escape")
            return "blocked_manual"
        pencil = drawer.locator("button.gathern-rtl-zvvl3w").first
        if not pencil.is_visible():
            pencil = drawer.locator("button.MuiIconButton-root").last
        pencil.click()
        try:
            page.wait_for_selector("input.MuiInputBase-inputAdornedEnd", state="visible", timeout=6000)
        except Exception:
            # إذا ما ظهرت خانة السعر = الغالب الشقة محجوزة
            print(f"  {name}: محجوزة (drawer بدون خانة سعر)")
            page.keyboard.press("Escape")
            return "booked"
        price_input = page.locator("input.MuiInputBase-inputAdornedEnd").first
        price_input.click()
        time.sleep(0.3)
        price_input.fill("")
        time.sleep(0.2)
        price_input.fill(str(price))
        time.sleep(0.5)
        current_val = price_input.input_value()
        if current_val != str(price):
            price_input.triple_click()
            time.sleep(0.2)
            price_input.fill(str(price))
            time.sleep(0.3)
        try:
            page.wait_for_selector("button:has-text('تطبيق السعر')", state="visible", timeout=4000)
        except Exception:
            pass
        apply = page.locator("button:has-text('تطبيق السعر')").first
        if not apply.is_visible():
            apply = page.locator("button.MuiButton-containedPrimary").first
        apply.click()
        time.sleep(2)
        print(f"  {name} -> {price} ر.س")
        return "ok"
    except Exception as e:
        print(f"  خطأ {name}: {e}")
        return "err_ex"

AIRBNB_SESSION_FILE = os.path.join(BASE_DIR, "airbnb_session_state.json")

def airbnb_login(page):
    """تسجيل الدخول على Airbnb وحفظ الجلسة."""
    print("Airbnb: فحص الجلسة...")
    page.goto("https://www.airbnb.com/hosting/listings", wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    if "hosting/listings" in page.url and "login" not in page.url:
        print("Airbnb: الجلسة نشطة")
        return True

    print("Airbnb: تسجيل الدخول...")
    page.goto("https://www.airbnb.com/login", wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)
    # أدخل الإيميل
    email_input = page.locator("input[name='user[email]'], input[type='email'], input[placeholder*='email' i], input[placeholder*='phone' i]").first
    email_input.fill(AIRBNB_EMAIL)
    time.sleep(0.5)
    page.locator("button[type='submit'], button:has-text('Continue'), button:has-text('متابعة')").first.click()
    time.sleep(2)
    # أدخل كلمة المرور
    try:
        pwd_input = page.locator("input[type='password']").first
        pwd_input.wait_for(state="visible", timeout=8000)
        pwd_input.fill(AIRBNB_PASSWORD)
        time.sleep(0.5)
        page.locator("button[type='submit']").first.click()
        time.sleep(4)
    except:
        pass
    # تحقق من النجاح
    if "hosting" in page.url or page.locator("[data-testid='main-nav']").count() > 0:
        print("Airbnb: تم تسجيل الدخول")
        return True
    # انتظر لو كان فيه 2FA
    send_telegram("Airbnb: مطلوب تحقق ثنائي - أكمل يدوياً في المتصفح")
    for _ in range(24):
        time.sleep(5)
        if "hosting" in page.url:
            print("Airbnb: تم تسجيل الدخول بعد التحقق")
            return True
    return False

def airbnb_update_price(page, unit, price, today):
    """يحدث سعر يوم واحد على Airbnb عبر تقويم المضيف."""
    airbnb_id = unit.get("airbnb_id", "")
    name = unit["name"]
    if not airbnb_id:
        return "no_airbnb"
    try:
        url = f"https://www.airbnb.com/hosting/listings/{airbnb_id}/calendar"
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        # لو أعاد للـ login فالجلسة انتهت
        if "login" in page.url:
            print(f"  Airbnb {name}: الجلسة انتهت")
            return "err_session"
        # ابحث عن تاريخ اليوم في التقويم
        # Airbnb يعرض التاريخ كـ data-testid="calendar-day-YYYY-MM-DD" أو aria-label
        day_cell = page.locator(
            f"[data-testid='calendar-day-{today}'], "
            f"[aria-label*='{today}'], "
            f"td[data-date='{today}']"
        ).first
        try:
            day_cell.wait_for(state="visible", timeout=10000)
            day_cell.click()
            time.sleep(1.5)
        except:
            # جرب البحث بشكل مختلف — رقم اليوم فقط
            day_num = str(int(today.split("-")[2]))
            # تأكد أن الشهر الصح ظاهر أولاً
            month_year = datetime.strptime(today, "%Y-%m-%d").strftime("%B %Y")
            cells = page.locator(f"[role='gridcell']:has-text('{day_num}'), td:has-text('{day_num}')").all()
            clicked = False
            for cell in cells:
                try:
                    lbl = cell.get_attribute("aria-label") or ""
                    if today in lbl or month_year in lbl:
                        cell.click()
                        clicked = True
                        time.sleep(1.5)
                        break
                except:
                    continue
            if not clicked:
                print(f"  Airbnb {name}: ما لقيت التاريخ")
                return "err_day"
        # بعد الضغط على اليوم، يظهر panel لتعديل السعر
        # Airbnb يستخدم input داخل panel/dialog
        price_input = page.locator(
            "input[id*='price'], input[name*='price'], "
            "[data-testid*='price'] input, "
            "input[inputmode='numeric']"
        ).first
        try:
            price_input.wait_for(state="visible", timeout=6000)
        except:
            # ربما الوحدة محجوزة أو ما فتح الـ panel
            print(f"  Airbnb {name}: ما فتح panel السعر")
            page.keyboard.press("Escape")
            return "err_panel"
        price_input.triple_click()
        time.sleep(0.2)
        price_input.fill(str(price))
        time.sleep(0.5)
        # حفظ
        save_btn = page.locator(
            "button:has-text('Save'), button:has-text('حفظ'), "
            "button:has-text('Apply'), button:has-text('تطبيق'), "
            "[data-testid='save-button']"
        ).first
        try:
            save_btn.wait_for(state="visible", timeout=4000)
            save_btn.click()
            time.sleep(2)
            print(f"  Airbnb {name} -> {price} ر.س")
            return "ok"
        except:
            page.keyboard.press("Escape")
            return "err_save"
    except Exception as e:
        print(f"  Airbnb خطأ {name}: {e}")
        return "err_ex"


def release_unit(page, unit, today):
    """يضغط زر 'إتاحة' للوحدات المشغولة يدوياً."""
    unit_id = unit["unit_id"]
    name = unit["name"]
    chalet_id = unit["chalet_id"]
    try:
        page.goto(f"https://business.gathern.co/app/calendar/unit?chalet={chalet_id}&unit_id={unit_id}")
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        time.sleep(3)
        close_dialog(page)
        try:
            page.wait_for_selector("#unit-select", timeout=15000)
        except:
            return "err_load"
        current_unit = page.locator("#unit-select").inner_text(timeout=3000).strip()
        unit_num = name.replace("ترف ", "").strip()
        if unit_num not in current_unit:
            select_btn = page.locator("#unit-select")
            select_btn.click()
            option = page.locator(f"[role='option'][data-value='{unit_id}']").first
            try:
                option.wait_for(state="visible", timeout=8000)
                option.click()
                time.sleep(1)
            except:
                page.keyboard.press("Escape")
                return "err_option"
        try:
            page.wait_for_selector("#drag-calendar", timeout=15000)
        except:
            return "err_calendar"
        day = str(int(today.split("-")[2]))
        day_cells = page.locator("#drag-calendar > div[role='button']").all()
        target_cell = None
        for cell in day_cells:
            try:
                if cell.locator("p span").first.inner_text(timeout=500).strip() == day:
                    target_cell = cell
                    break
            except:
                continue
        if not target_cell:
            return "err_day"
        target_cell.click()
        time.sleep(1.5)
        drawer = page.locator(".MuiDrawer-paper").first
        if not drawer.is_visible():
            return "err_drawer"
        # لو ما عادت مشغولة (ربما تغيرت الحالة) تجاهل
        if drawer.locator("p:has-text('الوحدة مشغولة')").count() == 0:
            page.keyboard.press("Escape")
            return "not_blocked"
        release_btn = drawer.locator("button:has-text('إتاحة')").first
        try:
            release_btn.wait_for(state="visible", timeout=5000)
            release_btn.click()
            time.sleep(2)
            print(f"  {name}: تم الإتاحة ✅")
            return "released"
        except:
            page.keyboard.press("Escape")
            return "err_release"
    except Exception as e:
        print(f"  خطأ إتاحة {name}: {e}")
        return "err_ex"


def main():
    cfg = load_runtime_config()
    start_hour   = cfg.get("start_hour",   START_HOUR)
    end_hour     = cfg.get("end_hour",     END_HOUR)
    evening_hour = cfg.get("evening_hour", EVENING_HOUR)
    overrides    = cfg.get("unit_overrides", {})

    from datetime import timezone, timedelta
    utc_now = datetime.now(timezone.utc)
    ksa_now = utc_now + timedelta(hours=3)
    now = ksa_now
    hour = now.hour
    today = now.strftime("%Y-%m-%d")
    now_str = now.strftime("%H:%M")
    print(f"تشغيل الاداة {now_str} {today}")

    minute = now.minute
    # وضع الإتاحة: 11:50 - 11:59 مساءً بتوقيت السعودية
    is_midnight_release = (hour == 23 and minute >= 50)

    if not is_midnight_release and (hour < start_hour or hour > end_hour):
        print(f"خارج ساعات التشغيل ({start_hour}:00 - {end_hour}:00)")
        return

    is_evening = hour >= evening_hour

    SESSION_FILE = os.path.join(BASE_DIR, "session_state.json")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # حمّل الجلسة المحفوظة إذا وُجدت
        if os.path.exists(SESSION_FILE):
            context = browser.new_context(storage_state=SESSION_FILE)
            print("تم استعادة الجلسة المحفوظة")
        else:
            context = browser.new_context()
        data = collect_prices()
        if not data["all_apt"]:
            send_telegram("فشل جمع الاسعار!")
            browser.close()
            return
        # متوسط مشذّب 10% من المتاحة فقط (المحجوزة وفوق 450 مستبعدة)
        apt_avg = trimmed_mean(data["avail_apt"], pct=0.10) or trimmed_mean(data["all_apt"], pct=0.10)
        std_avg = trimmed_mean(data["avail_studio"], pct=0.10) or trimmed_mean(data["all_studio"], pct=0.10) or apt_avg
        print(f"متوسط الشقق (متاح): {apt_avg} ({len(data['avail_apt'])} وحدة) | الاستديوهات: {std_avg} ({len(data['avail_studio'])} وحدة)")
        business_page = context.new_page()
        logged_in = login(business_page)
        if not logged_in:
            send_telegram("فشل تسجيل الدخول!")
            browser.close()
            return
        # احفظ الجلسة بعد تسجيل الدخول الناجح
        try:
            context.storage_state(path=SESSION_FILE)
            print("تم حفظ الجلسة")
        except:
            pass

        results = []
        updated_count = 0

        released_count = 0
        for unit in UNITS:
            uid = unit["unit_id"]
            utype = unit["type"]
            strategy = overrides.get(uid) or DEFAULT_STRATEGY.get(utype, "0")
            if is_evening:
                strategy = evening_downgrade(strategy)
            base = std_avg if "استديو" in utype else apt_avg
            price = calc_price(base, strategy)
            status = update_price(business_page, unit, price, today)
            if status == "ok":
                updated_count += 1
                results.append(f"✅ {unit['name']} ← {price} ر.س ({strategy})")
            elif status == "booked_guest":
                results.append(f"⏭️ {unit['name']} ← محجوزة")
            elif status == "blocked_manual":
                if is_midnight_release:
                    rel = release_unit(business_page, unit, today)
                    if rel == "released":
                        released_count += 1
                        results.append(f"🔓 {unit['name']} ← تم الإتاحة")
                    else:
                        results.append(f"❌ {unit['name']} ← فشل الإتاحة ({rel})")
                else:
                    results.append(f"🔒 {unit['name']} ← مشغولة يدوياً")
            else:
                err_map = {"err_load":"ما حمّلت","err_option":"ما لقيت","err_calendar":"تقويم","err_day":"يوم؟","err_drawer":"drawer","err_ex":"خطأ"}
                results.append(f"❌ {unit['name']} ← {err_map.get(status, status)}")

        save_history(today, now_str, data, apt_avg, std_avg, updated_count, len(UNITS))

        time_label = "منتصف الليل - إتاحة" if is_midnight_release else ("مساء" if is_evening else now_str)
        sep = "━━━━━━━━━━━━━━━"
        msg = (f"📊 تحديث {time_label}\n{sep}\n"
               f"متوسط الشقق: {apt_avg} ر.س ({len(data['avail_apt'])} متاحة)\n"
               f"متوسط الاستديوهات: {std_avg} ر.س ({len(data['avail_studio'])} متاحة)\n"
               f"إشغال السوق: {data['occ_all']}% (إجمالي)\n"
               f"  شقق: {data['occ_apt']}% ({data['apt_booked']}/{len(data['all_apt'])} مؤجرة)\n"
               f"  استديوهات: {data['occ_studio']}% ({data['studio_booked']}/{len(data['all_studio'])} مؤجرة)\n{sep}\n"
               + "\n".join(results)
               + f"\n{sep}\nتم تحديث {updated_count}/{len(UNITS)} وحدة"
               + (f" | تم إتاحة {released_count} 🔓" if is_midnight_release and released_count else "")
               )
        send_telegram(msg)
        print("انتهى تحديث Gathern!")

        # ── Airbnb ──────────────────────────────────────────
        if not AIRBNB_EMAIL or not AIRBNB_PASSWORD:
            send_telegram("⚠️ Airbnb: بيانات الدخول غير موجودة (تحقق من الـ Secrets)")
            print("Airbnb: لا توجد بيانات دخول، تخطي")
            browser.close()
            return

        print("بدء تحديث Airbnb...")
        if os.path.exists(AIRBNB_SESSION_FILE):
            ab_context = browser.new_context(storage_state=AIRBNB_SESSION_FILE)
            print("Airbnb: تم استعادة الجلسة")
        else:
            ab_context = browser.new_context()

        ab_page = ab_context.new_page()
        ab_logged = airbnb_login(ab_page)

        if ab_logged:
            try:
                ab_context.storage_state(path=AIRBNB_SESSION_FILE)
            except:
                pass

            ab_results = []
            ab_updated = 0
            for unit in UNITS:
                airbnb_id = unit.get("airbnb_id", "")
                if not airbnb_id:
                    continue
                uid = unit["unit_id"]
                utype = unit["type"]
                strategy = overrides.get(uid) or DEFAULT_STRATEGY.get(utype, "0")
                if is_evening:
                    strategy = evening_downgrade(strategy)
                base = std_avg if "استديو" in utype else apt_avg
                price = calc_price(base, strategy)
                status = airbnb_update_price(ab_page, unit, price, today)
                if status == "ok":
                    ab_updated += 1
                    ab_results.append(f"✅ {unit['name']} ← {price} ر.س")
                elif status == "no_airbnb":
                    pass
                else:
                    err_map = {"err_session":"جلسة منتهية","err_day":"تاريخ؟","err_panel":"panel","err_save":"حفظ","err_ex":"خطأ"}
                    ab_results.append(f"❌ {unit['name']} ← {err_map.get(status, status)}")

            ab_sep = "━━━━━━━━━━━━━━━"
            ab_msg = (f"🏠 Airbnb تحديث {time_label}\n{ab_sep}\n"
                      + "\n".join(ab_results)
                      + f"\n{ab_sep}\nتم تحديث {ab_updated} وحدة على Airbnb")
            send_telegram(ab_msg)
        else:
            send_telegram("❌ Airbnb: فشل تسجيل الدخول")

        browser.close()
        print("انتهى التحديث الكامل!")

if __name__ == "__main__":
    main()
