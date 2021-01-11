from flask import request, jsonify
from models import AuthKeys
from functools import wraps
from datetime import datetime, timezone
from functions import update_call_count


def auth_key_required(func):
    """API Key check for expired keys, invalid keys or calls' limit reached"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'appid' not in request.args:
            return jsonify({'message': 'Missing token'})

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

        return jsonify({'message': 'Invalid token'}), 401

    return wrapper
