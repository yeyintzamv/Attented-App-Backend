import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from config import Config
from models import User

SECRET = Config.JWT_SECRET

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')

def decode_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=['HS256'])
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Authorization token required'}), 401
        token = token.replace('Bearer ', '')
        data = decode_token(token)
        if not data:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # user_id ကို database ထဲက is_admin ပါ ယူမယ်
        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 401

        data['is_admin'] = user.is_admin
        return f(data, *args, **kwargs)
    return decorated