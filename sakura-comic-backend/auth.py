from flask import Blueprint, request, jsonify, current_app, g
from models import db, User
import jwt
from datetime import datetime, timedelta
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# --- 认证装饰器 ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 尝试从 Authorization: Bearer <token> 获取
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # 如果前端使用 params 传递 token，也兼容一下
        if not token and 'token' in request.args:
            token = request.args.get('token')

        if not token:
            return jsonify({'code': 401, 'msg': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'code': 401, 'msg': 'Token is invalid or user not found!'}), 401
            g.current_user = current_user
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'msg': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'msg': 'Token is invalid!'}), 401

        return f(*args, **kwargs)
    return decorated

# --- 认证路由 ---

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'code': 409, 'msg': '用户名已存在'}), 409

    new_user = User(username=username)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '注册成功'})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        # 生成JWT
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24) # 24小时过期
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({'code': 200, 'msg': '登录成功', 'token': token})
    else:
        return jsonify({'code': 401, 'msg': '用户名或密码错误'}), 401

@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user_info():
    # token_required 装饰器已将用户信息存储在 g.current_user 中
    return jsonify({'code': 200, 'data': g.current_user.to_dict()})
