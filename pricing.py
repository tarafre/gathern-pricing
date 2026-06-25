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
            w.writerow([
                "date","time",
                "apt_avg","studio_avg",
                "all_apt","all_studio",
                "avail_apt","avail_studio",
                "occ_apt_pct","occ_studio_pct",
                "updated","total"
            ])
        w.writerow([
            today, now_str,
            apt_avg, std_avg,
            len(data["all_apt"]),    len(data["all_studio"]),
            len(data["avail_apt"]),  len(data["avail_studio"]),
            data["occ_apt"],         data["occ_studio"],
            updated, total
        ])

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

def _scrape_pages(page, base_url):
    """تجمع بيانات الوحدات من __NEXT_DATA__ — تنتقل لكل صفحة بـ URL مستقل."""
    apt_all, studio_all = [], []
    apt_avail, studio_avail = [], []

    for page_num in range(1, 33):
        url = f"{base_url}&page={page_num}"
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(2)
        except:
            break

        try:
            units = page.evaluate(
                "() => { const s = window.__NEXT_DATA__?.props?.pageProps?.ssr; return s ? Object.values(s) : []; }"
            )
        except:
            units = []

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
                max_price = 300 if utype == "studio" else 350
                if price < 80 or price > max_price:
                    continue

                is_avail = bool(u.get("isUnitAvailable", True))

                if utype == "studio":
                    studio_all.append(price)
                    if is_avail:
                        studio_avail.append(price)
                else:
                    apt_all.append(price)
                    if is_avail:
                        apt_avail.append(price)
            except:
                pass

        print(f"  صفحة {page_num}: {len(units)} وحدة")

    return apt_all, studio_all, apt_avail, studio_avail


def collect_prices(page):
    from datetime import timezone, timedelta
    print("جمع اسعار المنافسين...")
    ksa_now  = datetime.now(timezone.utc) + timedelta(hours=3)
    today    = ksa_now.strftime("%Y-%m-%d")
    tomorrow = (ksa_now + timedelta(days=1)).strftime("%Y-%m-%d")

    url = (f"https://gathern.co/search?chalet_types=apartment"
           f"&city={CITY_ID}&checkin={today}&checkout={tomorrow}")

    apt_all, studio_all, apt_avail, studio_avail = _scrape_pages(page, url)

    occ_apt    = round((len(apt_all)    - len(apt_avail))    / len(apt_all)    * 100) if apt_all    else 0
    occ_studio = round((len(studio_all) - len(studio_avail)) / len(studio_all) * 100) if studio_all else 0

    print(f"  شقق: {len(apt_all)} كل / {len(apt_avail)} متاحة | إشغال: {occ_apt}%")
    print(f"  استديو: {len(studio_all)} كل / {len(studio_avail)} متاحة | إشغال: {occ_studio}%")

    return {
        "all_apt":       apt_all,
        "all_studio":    studio_all,
        "avail_apt":     apt_avail,
        "avail_studio":  studio_avail,
        "occ_apt":       occ_apt,
        "occ_studio":    occ_studio,
    }

def login(page):
    print("تسجيل الدخول...")
    page.goto("https://business.gathern.co/login")
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    time.sleep(3)
    page.locator("input").first.fill(GATHERN_PHONE)
    time.sleep(1)
    page.locator("button[type='submit']").first.click()
    time.sleep(4)
    if "login" not in page.url:
        print("تم تسجيل الدخول مباشرة!")
        return True
    send_telegram("مطلوب رمز OTP - ارسله هنا مباشرة")
    print("انتظار OTP...")
    r0 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": -1}).json()
    last_id = r0["result"][-1]["update_id"] if r0.get("result") else None
    for _ in range(60):
        time.sleep(5)
        if "login" not in page.url:
            print("تم تسجيل الدخول!")
            return True
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"offset": -1}).json()
            updates = r.get("result", [])
            if updates:
                update = updates[-1]
                if last_id and update["update_id"] <= last_id:
                    continue
                last_msg = update.get("message", {}).get("text", "").strip()
                if last_msg.isdigit() and 4 <= len(last_msg) <= 6:
                    boxes = page.locator("input").all()
                    for i, d in enumerate(list(last_msg)):
                        if i < len(boxes):
                            boxes[i].fill(d)
                            time.sleep(0.3)
                    page.locator("button[type='submit']").first.click()
                    time.sleep(4)
        except:
            pass
    return "login" not in page.url

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
            return False
        current_unit = page.locator("#unit-select").inner_text(timeout=3000).strip()
        unit_num = name.replace("ترف ", "").strip()
        if unit_num not in current_unit:
            select_btn = page.locator("#unit-select")
            select_btn.click()
            time.sleep(1)
            option = page.locator(f"[role='option'][data-value='{unit_id}']").first
            if option.is_visible():
                option.click()
                time.sleep(2)
            else:
                print(f"  {name}: ما لقيت الخيار في القائمة")
                page.keyboard.press("Escape")
                return False
        try:
            page.wait_for_selector("#drag-calendar", timeout=15000)
        except:
            print(f"  {name}: التقويم ما حمّل")
            return False
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
            print(f"  {name}: ما لقيت اليوم")
            return False
        target_cell.click()
        time.sleep(1.5)
        drawer = page.locator(".MuiDrawer-paper").first
        if not drawer.is_visible():
            print(f"  {name}: الـ drawer ما فتح")
            return False
        booked_indicator = drawer.locator("p:has-text('مؤكد حجز'), span:has-text('حجز مؤكد')").count()
        if booked_indicator > 0:
            print(f"  {name} محجوزة، تخطي")
            page.keyboard.press("Escape")
            return False
        pencil = drawer.locator("button.gathern-rtl-zvvl3w").first
        if not pencil.is_visible():
            pencil = drawer.locator("button.MuiIconButton-root").last
        pencil.click()

        # انتظر ظهور خانة السعر
        try:
            page.wait_for_selector("input.MuiInputBase-inputAdornedEnd", state="visible", timeout=6000)
        except Exception:
            print(f"  {name}: خانة السعر ما ظهرت بعد الضغط على القلم")
            return False

        price_input = page.locator("input.MuiInputBase-inputAdornedEnd").first
        price_input.click()
        time.sleep(0.3)
        # احذف القيمة القديمة ثم اكتب الجديدة
        price_input.fill("")
        time.sleep(0.2)
        price_input.fill(str(price))
        time.sleep(0.5)

        # تحقق أن القيمة اتكتبت صح
        current_val = price_input.input_value()
        if current_val != str(price):
            price_input.triple_click()
            time.sleep(0.2)
            price_input.fill(str(price))
            time.sleep(0.3)

        # انتظر ظهور زر تطبيق السعر
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
        return True
    except Exception as e:
        print(f"  خطأ {name}: {e}")
        return False

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

    if hour < start_hour or hour > end_hour:
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
        research_page = context.new_page()
        data = collect_prices(research_page)
        if not data["all_apt"]:
            send_telegram("فشل جمع الاسعار!")
            browser.close()
            return
        # نستخدم أسعار المتاحة للمتوسط لو كافية، وإلا نرجع للكل
        apt_src    = data["avail_apt"]    if len(data["avail_apt"])    >= 10 else data["all_apt"]
        studio_src = data["avail_studio"] if len(data["avail_studio"]) >= 5  else data["all_studio"]
        apt_avg = round(statistics.median(apt_src))
        std_avg = round(statistics.median(studio_src)) if studio_src else apt_avg
        print(f"متوسط الشقق: {apt_avg} | الاستديوهات: {std_avg} | إشغال: {data['occ_apt']}% / {data['occ_studio']}%")
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

        for unit in UNITS:
            uid = unit["unit_id"]
            utype = unit["type"]
            strategy = overrides.get(uid) or DEFAULT_STRATEGY.get(utype, "0")
            if is_evening:
                strategy = evening_downgrade(strategy)
            base = std_avg if "استديو" in utype else apt_avg
            price = calc_price(base, strategy)
            success = update_price(business_page, unit, price, today)
            if success:
                updated_count += 1
                results.append(f"✅ {unit['name']} ← {price} ر.س ({strategy})")
            else:
                results.append(f"⏭️ {unit['name']} ← محجوزة")

        save_history(today, now_str, data, apt_avg, std_avg, updated_count, len(UNITS))

        time_label = "مساء" if is_evening else now_str
        sep = "━━━━━━━━━━━━━━━"
        msg = (f"📊 تحديث {time_label}\n{sep}\n"
               f"وسيط الشقق: {apt_avg} ر.س\n"
               f"وسيط الاستديوهات: {std_avg} ر.س\n"
               f"إشغال السوق: {data['occ_apt']}% شقق | {data['occ_studio']}% استديوهات\n{sep}\n"
               + "\n".join(results)
               + f"\n{sep}\nتم تحديث {updated_count}/{len(UNITS)} وحدة")
        send_telegram(msg)
        print("انتهى التحديث!")
        browser.close()

if __name__ == "__main__":
    main()
