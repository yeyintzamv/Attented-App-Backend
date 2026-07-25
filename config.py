import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-67890')

    # Office Geofence (ခင်ဗျားရုံးနေရာနဲ့အစားထိုးပါ)
    OFFICE_LAT = float(os.environ.get('OFFICE_LAT', 16.8409))
    OFFICE_LNG = float(os.environ.get('OFFICE_LNG', 96.1735))
    GEOFENCE_RADIUS = float(os.environ.get('GEOFENCE_RADIUS', 100))  # meters