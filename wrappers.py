from flask import request, jsonify
from models import db, User, AuthKeys
from functools import wraps
from datetime import datetime, timezone


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
                # db.session.delete(check_auth)
                # db.session.commit()
                return jsonify({'message': 'Expired token'})
            current_calls = check_auth.user.calls
            current_user = User.query.get(check_auth.user_id)
            if current_calls == 0:
                return jsonify({'message': 'You have reached the limit of requests'})
            current_user.calls = current_calls - 1
            db.session.commit()
            return func(*args, **kwargs)

        return jsonify({'message': 'Invalid token'}), 401

    return wrapper
