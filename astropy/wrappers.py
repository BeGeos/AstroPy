from flask import request, jsonify
from .models import AuthKeys
from functools import wraps
from datetime import datetime, timezone
from .functions import update_call_count
from .env import secret_keys


def auth_key_required(func):
    """API Key check for expired keys, invalid keys or calls' limit reached"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == 'POST':
            try:
                if request.get_json()['ADMIN_KEY']:
                    if request.get_json()['ADMIN_KEY'] == secret_keys['ADMIN_KEY']:
                        return func(*args, **kwargs)
                    else:
                        return jsonify({'message': 'Invalid Admin Key'}), 403
            except:
                return jsonify({'message': 'ADMIN_KEY required'})

        if 'appid' not in request.args:
            return jsonify({'message': 'Missing token'}), 400

        api_key = request.args['appid']
        check_auth = AuthKeys.query.filter_by(key=api_key).first()

        if check_auth:
            if check_auth.expiration_date <= datetime.now(timezone.utc).timestamp():
                return jsonify({'message': 'Expired token'})
            if not check_auth.active:
                return jsonify({'message': 'This api key is not active'})
            current_calls = update_call_count(check_auth.user_id)
            if current_calls == 0:
                return jsonify({'message': 'You have reached the limit of requests'})

            return func(*args, **kwargs)

        return jsonify({'message': 'Invalid token'}), 403

    return wrapper


def admin_only(func):
    """Security control for admin only routes"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # print(request.get_json())
        if request.get_json() is None:
            return jsonify({'message': 'No valid argument'}), 404
        if 'ADMIN_KEY' in request.get_json():
            if request.get_json()['ADMIN_KEY'] == secret_keys['ADMIN_KEY']:
                return func(*args, **kwargs)
            else:
                return jsonify({'message': 'Invalid Admin Key'}), 403
        else:
            return jsonify({'message': 'No valid argument'}), 404

    return wrapper
