import os
import requests
from models import db, Holiday
from datetime import datetime

CALENDARIFIC_API_KEY = os.environ.get('CALENDARIFIC_API_KEY', '')
COUNTRY = 'MM'
YEAR = datetime.now().year

def sync_holidays():
    """အစိုးရရုံးပိတ်ရက်များကို API မှ အလိုအလျောက် ရယူသိမ်းဆည်းပေးသည်"""
    if not CALENDARIFIC_API_KEY:
        print("⚠️ CALENDARIFIC_API_KEY not set. Skipping auto sync.")
        return

    url = "https://calendarific.com/api/v2/holidays"
    params = {
        'api_key': CALENDARIFIC_API_KEY,
        'country': COUNTRY,
        'year': YEAR
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if data.get('meta', {}).get('code') == 200:
            holidays = data.get('response', {}).get('holidays', [])
            count = 0
            for h in holidays:
                date_str = h.get('date', {}).get('iso')
                name = h.get('name')
                if date_str and name:
                    dt = datetime.strptime(date_str, '%Y-%m-%d').date()
                    if not Holiday.query.filter_by(date=dt).first():
                        db.session.add(Holiday(date=dt, name=name))
                        count += 1
            db.session.commit()
            print(f"✅ Synced {count} new holidays from Calendarific")
        else:
            print(f"❌ API error: {data.get('meta', {}).get('message')}")
    except Exception as e:
        print(f"❌ Holiday sync failed: {e}")