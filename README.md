# Auto Attendance System with Geofencing

A complete attendance management system featuring automatic geofence check-in/out, holiday syncing, and monthly report summaries with OT/Absent breakdowns.

## Features
- **Sign Up / Sign In:** JWT based authentication.
- **Geofencing Auto Check-in/out:** Automatically checks in when entering office boundary (100m) and checks out on exit.
- **Smart Status Detection:** Automatically marks Sunday & Holidays as OT.
- **Monthly Report:** Shows exact days for OT, Absent, Present, and Holidays.
- **Copy to Clipboard:** One-tap copy of summary text for easy sharing.
- **Auto Sync Holidays:** Calendarific API integration.

## Tech Stack
- **Server:** Flask (Python), SQLite / PostgreSQL, PyJWT, Calendarific API
- **Android App:** Kotlin, Retrofit, Google Play Services Location (Geofence API)

## Project Structure
```
attendance-system-final.zip
├── server/
│   ├── app.py
│   ├── models.py
│   ├── auth.py
│   ├── config.py
│   ├── holidays_sync.py
│   ├── requirements.txt
│   └── README_SERVER.md
└── app/
    ├── build.gradle
    ├── src/main/AndroidManifest.xml
    ├── src/main/java/com/yourapp/attendance/
    │   ├── MainActivity.kt
    │   ├── ApiService.kt
    │   ├── GeofenceService.kt
    │   ├── GeofenceBroadcastReceiver.kt
    │   └── Config.kt
    └── src/main/res/layout/
        ├── activity_main.xml
        ├── dialog_login.xml
        └── dialog_register.xml
```

## Setup Instructions
### Server Setup
1. Open `server/` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run server: `python app.py`

### Android App Setup
1. Open `app/` in Android Studio.
2. Edit `Config.kt` to update `BASE_URL` with your server address.
3. Build & Run on your Android device.
