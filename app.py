from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, bcrypt, User, Attendance, Holiday
from auth import generate_token, token_required
from config import Config
from holidays_sync import sync_holidays
from datetime import datetime, date, timedelta
import math
import os

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
bcrypt.init_app(app)

# ---- Helper: Haversine Distance ----
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# ---- Create Tables & Admin ----
with app.app_context():
    db.create_all()
    sync_holidays()  # Auto sync from API

    # Admin ကို .env ကနေဖတ်ပြီး ဆောက်ပေးမယ်
    admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if not User.query.filter_by(username=admin_user).first():
        admin = User(username=admin_user, full_name='System Admin', is_admin=True)
        admin.set_password(admin_pass)
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Admin created: {admin_user} / {admin_pass}")
    else:
        print(f"✅ Admin user already exists: {admin_user}")

# ===================== AUTH ROUTES =====================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    if User.query.filter_by(username=data.get('username')).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(
        username=data.get('username'),
        full_name=data.get('full_name', ''),
        email=data.get('email', '')
    )
    user.set_password(data.get('password'))
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    user = User.query.filter_by(username=data.get('username')).first()
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_token(user.id)
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'is_admin': user.is_admin
        }
    })

# ===================== USER MANAGEMENT (ADMIN) =====================
@app.route('/api/users', methods=['GET'])
@token_required
def get_users(data):
    if not data.get('is_admin'):
        return jsonify({'error': 'Admin required'}), 403
    users = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'full_name': u.full_name,
        'email': u.email,
        'is_admin': u.is_admin
    } for u in users])

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(data, user_id):
    if not data.get('is_admin'):
        return jsonify({'error': 'Admin required'}), 403
    user = User.query.get_or_404(user_id)
    if user.id == data['user_id']:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

# ===================== ATTENDANCE ROUTES =====================
@app.route('/api/attendance/checkin', methods=['POST'])
@token_required
def check_in(data):
    user_id = data['user_id']
    req = request.json or {}
    lat, lng = req.get('latitude'), req.get('longitude')
    today = date.today()

    # Geofence check
    if lat is not None and lng is not None:
        dist = haversine(lat, lng, Config.OFFICE_LAT, Config.OFFICE_LNG)
        if dist > Config.GEOFENCE_RADIUS:
            return jsonify({
                'error': f'You are {int(dist)}m away. Office is within {Config.GEOFENCE_RADIUS}m.'
            }), 400

    existing = Attendance.query.filter_by(user_id=user_id, date=today).first()
    if existing and existing.check_in:
        return jsonify({'error': 'Already checked in today'}), 400

    is_sunday = today.weekday() == 6
    is_holiday = Holiday.query.filter_by(date=today).first() is not None
    status = 'OT' if (is_sunday or is_holiday) else 'Present'

    if existing:
        existing.check_in = datetime.utcnow()
        existing.status = status
        existing.latitude = lat
        existing.longitude = lng
        existing.location_name = req.get('location_name', 'Office')
    else:
        att = Attendance(
            user_id=user_id,
            date=today,
            check_in=datetime.utcnow(),
            status=status,
            latitude=lat,
            longitude=lng,
            location_name=req.get('location_name', 'Office')
        )
        db.session.add(att)

    db.session.commit()
    return jsonify({'message': f'Checked in ({status})', 'status': status})

@app.route('/api/attendance/checkout', methods=['POST'])
@token_required
def check_out(data):
    user_id = data['user_id']
    today = date.today()
    att = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if not att or not att.check_in:
        return jsonify({'error': 'No check-in found for today'}), 400
    if att.check_out:
        return jsonify({'error': 'Already checked out'}), 400

    att.check_out = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Checked out successfully'})

@app.route('/api/attendance/today', methods=['GET'])
@token_required
def today_status(data):
    user_id = data['user_id']
    today = date.today()
    att = Attendance.query.filter_by(user_id=user_id, date=today).first()

    if att:
        return jsonify({
            'checked_in': bool(att.check_in),
            'checked_out': bool(att.check_out),
            'status': att.status,
            'check_in': att.check_in.isoformat() if att.check_in else None,
            'check_out': att.check_out.isoformat() if att.check_out else None,
            'location': att.location_name
        })
    return jsonify({'checked_in': False, 'checked_out': False, 'status': 'Absent'})

# ===================== MONTHLY REPORT =====================
@app.route('/api/attendance/monthly/<int:year>/<int:month>', methods=['GET'])
@token_required
def monthly_report(data, year, month):
    user_id = data['user_id']
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    holidays = {h.date for h in Holiday.query.filter(
        Holiday.date >= start_date,
        Holiday.date <= end_date
    ).all()}

    records = {att.date: att for att in Attendance.query.filter_by(user_id=user_id).filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).all()}

    ot_dates, absent_dates, present_dates, holiday_dates = [], [], [], []
    current = start_date

    while current <= end_date:
        is_sunday = current.weekday() == 6
        is_holiday = current in holidays
        is_off_day = is_sunday or is_holiday

        if current in records:
            att = records[current]
            if is_off_day or att.status == 'OT':
                ot_dates.append(current)
            else:
                present_dates.append(current)
        else:
            if is_off_day:
                holiday_dates.append(current)
            elif current <= date.today():
                absent_dates.append(current)

        current += timedelta(days=1)

    month_name = start_date.strftime('%B')
    lines = [f"{month_name} {year}"]

    if ot_dates:
        ot_str = ', '.join([d.strftime('%d.%m.%y') for d in ot_dates])
        lines.append(f"OT - {ot_str} ({len(ot_dates)} day{'s' if len(ot_dates)>1 else ''})")
    else:
        lines.append("OT - No overtime")

    if absent_dates:
        abs_str = ', '.join([d.strftime('%d.%m.%y') for d in absent_dates])
        lines.append(f"Absent - {abs_str} ({len(absent_dates)} day{'s' if len(absent_dates)>1 else ''})")
    else:
        lines.append("Absent - No absence")

    summary = "\n".join(lines)

    return jsonify({
        'summary': summary,
        'ot_dates': [d.isoformat() for d in ot_dates],
        'absent_dates': [d.isoformat() for d in absent_dates],
        'present_dates': [d.isoformat() for d in present_dates],
        'holiday_dates': [d.isoformat() for d in holiday_dates],
        'month': month_name,
        'year': year
    })

# ===================== HOLIDAY MANAGEMENT (ADMIN) =====================
@app.route('/api/holidays', methods=['POST'])
@token_required
def add_holiday(data):
    if not data.get('is_admin'):
        return jsonify({'error': 'Admin required'}), 403
    req = request.json or {}
    dt = datetime.strptime(req['date'], '%Y-%m-%d').date()
    if Holiday.query.filter_by(date=dt).first():
        return jsonify({'error': 'Holiday already exists'}), 400
    h = Holiday(date=dt, name=req.get('name', 'Public Holiday'))
    db.session.add(h)
    db.session.commit()
    return jsonify({'message': 'Holiday added'})

@app.route('/api/holidays', methods=['GET'])
def get_holidays():
    holidays = Holiday.query.order_by(Holiday.date).all()
    return jsonify([{'date': h.date.isoformat(), 'name': h.name} for h in holidays])

# ===================== MAIN =====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)