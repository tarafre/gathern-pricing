#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://business.gathern.co/login")
    print("سجّل دخولك على Gathern في النافذة...")
    print("بعد ما تسجّل الدخول بنجاح، ارجع هنا واضغط Enter")
    input()
    ctx.storage_state(path="session_state.json")
    browser.close()
    print("✅ تم حفظ الجلسة في session_state.json")
    import base64, json
    with open("session_state.json", "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    print("\n── انسخ هذا كـ GitHub Secret باسم GATHERN_SESSION ──")
    print(b64)
    print("───────────────────────────────────────────────────")
