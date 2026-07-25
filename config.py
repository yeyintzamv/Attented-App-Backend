import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
    
    # Railway က DATABASE_URL ကို postgres:// နဲ့ပေးတယ်။ SQLAlchemy က postgresql:// လိုတယ်
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///attendance.db')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-67890')
    
    OFFICE_LAT = float(os.environ.get('OFFICE_LAT', 16.8409))
    OFFICE_LNG = float(os.environ.get('OFFICE_LNG', 96.1735))
    GEOFENCE_RADIUS = float(os.environ.get('GEOFENCE_RADIUS', 100))
