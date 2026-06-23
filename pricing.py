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

def save_history(today, now_str, apt_avg, std_avg, apt_count, std_count, updated, total):
    path = os.path.join(BASE_DIR, "data", "history.csv")
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["date","time","apt_avg","studio_avg","apt_count","studio_count","updated","total"])
        w.writerow([today, now_str, apt_avg, std_avg, apt_count, std_count, updated, total])

from config import *

def send_telegram(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"})
    except: pass

def calc_price(base, strategy):
    if strategy == "high":      return round(base * (1 + PCT_HIGH/100))
    if strategy == "mid":       return round(base)
    if strategy == "low":       return round(base * (1 - PCT_LOW/100))
    if strategy == "low_extra": return round(base * (1 - (PCT_LOW*2)/100))
    if strategy == "high_plus": return round(base * (1 + (PCT_HIGH+20)/100))
    return round(base)

def collect_prices(page):
    print("جمع اسعار المنافسين...")
    apt_prices, studio_prices = [], []
    url = f"https://gathern.co/search?chalet_types=apartment&city={CITY_ID}"
    page.goto(url)
    page.wait_for_load_state("domcontentloaded", timeout=60000)
    time.sleep(3)
    for page_num in range(1, 33):
        print(f"  صفحة {page_num}...")
        cards = page.locator("a[href*='/view/']").all()
        for card in cards:
            try:
                title = card.locator("h3.e1dgygz88").inner_text(timeout=2000).strip()
                if not title:
                    continue
                if "استديو" in title or "استوديو" in title:
                    unit_type = "studio"
                elif "غرفتين" in title or "غرفتان" in title:
                    unit_type = "apt_2br"
                elif "شقة" in title or "شقه" in title:
                    unit_type = "apt_1br"
                else:
                    continue
                rating_el = card.locator("span.e1dgygz810")
                if rating_el.count() > 0:
                    spans = rating_el.locator("span").all()
                    count_text = spans[-1].inner_text(timeout=1000) if spans else "0"
                    review_count = int(re.sub(r"[^\d]", "", count_text) or "0")
                else:
                    review_count = 0
                if review_count < 3:
                    continue
                price_text = card.locator("p span.rtl-1hukj43").first.inner_text(timeout=2000).strip()
                price_clean = re.sub(r"[^\d.]", "", price_text)
                if not price_clean:
                    continue
                price = float(price_clean)
                max_price = 300 if unit_type == 'studio' else 350
                if price < 80 or price > max_price:
                    continue
                if unit_type == "studio":
                    studio_prices.append(price)
                elif unit_type == "apt_1br":
                    apt_prices.append(price)
            except:
                pass
        print(f"    شقق: {len(apt_prices)} | استديوهات: {len(studio_prices)}")
        pass  # تمر على كل الصفحات
        try:
            nxt = page.locator("button[aria-label='Go to next page']").first
            if nxt.is_visible() and nxt.is_enabled():
                nxt.click()
                time.sleep(2)
            else:
                break
        except:
            break
    print(f"  اجمالي شقق: {len(apt_prices)} | استديوهات: {len(studio_prices)}")
    return apt_prices, studio_prices

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

    now = datetime.now()
    hour = now.hour
    today = now.strftime("%Y-%m-%d")
    now_str = now.strftime("%H:%M")
    print(f"تشغيل الاداة {now_str} {today}")

    if hour < start_hour or hour > end_hour:
        print(f"خارج ساعات التشغيل ({start_hour}:00 - {end_hour}:00)")
        return

    is_evening = hour >= evening_hour

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        research_page = context.new_page()
        apt_prices, studio_prices = collect_prices(research_page)
        if not apt_prices:
            send_telegram("فشل جمع الاسعار!")
            browser.close()
            return
        apt_avg = round(statistics.median(apt_prices))
        std_avg = round(statistics.median(studio_prices)) if studio_prices else apt_avg
        print(f"متوسط الشقق: {apt_avg} | الاستديوهات: {std_avg}")
        business_page = context.new_page()
        logged_in = login(business_page)
        if not logged_in:
            send_telegram("فشل تسجيل الدخول!")
            browser.close()
            return

        results = []
        updated_count = 0
        strategy_map = EVENING_STRATEGY if is_evening else DEFAULT_STRATEGY

        for unit in UNITS:
            uid = unit["unit_id"]
            utype = unit["type"]
            # override يأخذ الأولوية على الاستراتيجية التلقائية
            strategy = overrides.get(uid) or strategy_map.get(utype, "mid")
            base = std_avg if "استديو" in utype else apt_avg
            price = calc_price(base, strategy)
            success = update_price(business_page, unit, price, today)
            if success:
                updated_count += 1
                results.append(f"✅ {unit['name']} ← {price} ر.س ({strategy})")
            else:
                results.append(f"⏭️ {unit['name']} ← محجوزة")

        save_history(today, now_str, apt_avg, std_avg,
                     len(apt_prices), len(studio_prices),
                     updated_count, len(UNITS))

        time_label = "مساء" if is_evening else now_str
        sep = "━━━━━━━━━━━━━━━"
        msg = (f"📊 تحديث {time_label}\n{sep}\n"
               f"وسيط الشقق: {apt_avg} ر.س\n"
               f"وسيط الاستديوهات: {std_avg} ر.س\n{sep}\n"
               + "\n".join(results)
               + f"\n{sep}\nتم تحديث {updated_count}/{len(UNITS)} وحدة")
        send_telegram(msg)
        print("انتهى التحديث!")
        browser.close()

if __name__ == "__main__":
    main()
