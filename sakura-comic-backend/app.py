from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, init_db, User, Video, Comment, Collection
from auth import auth_bp, token_required
from video import video_bp
from comment import comment_bp
from collection import collection_bp

def create_app():
    app = Flask(__name__)
    
    # 使用SQLite数据库，文件名为site.db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'a_very_secret_key_for_jwt' # 用于JWT签名

    # 允许跨域请求
    CORS(app)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(video_bp) # 视频列表和详情
    app.register_blueprint(comment_bp) # 评论
    app.register_blueprint(collection_bp) # 收藏

    # 根路由，用于健康检查
    @app.route('/')
    def index():
        return jsonify({"message": "Sakura Comic Backend is running!"})

    return app

if __name__ == '__main__':
    app = create_app()
    # 首次运行时创建数据库和表，并插入测试数据
    with app.app_context():
        init_db(app)
    app.run(debug=True, host='0.0.0.0', port=5000)
