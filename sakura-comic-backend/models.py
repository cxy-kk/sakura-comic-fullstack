from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    collections = db.relationship('Collection', backref='collector', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat()
        }

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    cover_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    release_year = db.Column(db.Integer)
    views = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    comments = db.relationship('Comment', backref='video_item', lazy='dynamic')
    collections = db.relationship('Collection', backref='video_collected', lazy='dynamic')

    def to_dict(self):
        return {
            'vod_id': self.id,
            'title': self.title,
            'cover_url': self.cover_url,
            'video_url': self.video_url,
            'category': self.category,
            'description': self.description,
            'release_year': self.release_year,
            'views': self.views,
            'update_time': self.update_time.isoformat()
        }

class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def to_dict(self, include_replies=False):
        data = {
            'comment_id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'username': self.author.username # 假设author已加载
        }
        if include_replies:
            data['replies'] = [reply.to_dict() for reply in self.replies.all()]
        return data

class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    collected_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='_user_video_uc'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'video_id': self.video_id,
            'collected_at': self.collected_at.isoformat()
        }

# 初始化数据库
def init_db(app):
    with app.app_context():
        db.create_all()
        # 插入一些测试数据
        if Video.query.count() == 0:
            videos = [
                Video(title='测试视频1 - 动漫', cover_url='/imgs/1.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='动漫', description='这是一部精彩的动漫', release_year=2023),
                Video(title='测试视频2 - 电影', cover_url='/imgs/2.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='电影', description='这是一部精彩的电影', release_year=2022),
                Video(title='测试视频3 - 电视剧', cover_url='/imgs/b1.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='电视剧', description='这是一部精彩的电视剧', release_year=2021),
                Video(title='测试视频4 - 动漫', cover_url='/imgs/b2.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='动漫', description='这是一部精彩的动漫', release_year=2023),
                Video(title='测试视频5 - 电影', cover_url='/imgs/b3.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='电影', description='这是一部精彩的电影', release_year=2022),
                Video(title='测试视频6 - 电视剧', cover_url='/imgs/b4.jpg', video_url='http://vjs.zencdn.net/v/oceans.mp4', category='电视剧', description='这是一部精彩的电视剧', release_year=2021),
            ]
            db.session.add_all(videos)
            db.session.commit()
            print("Test videos inserted.")

        if User.query.count() == 0:
            user = User(username='testuser')
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            print("Test user inserted.")

        if Comment.query.count() == 0:
            comment1 = Comment(user_id=1, video_id=1, content='这个视频太棒了！')
            comment2 = Comment(user_id=1, video_id=1, content='期待下一集！')
            db.session.add_all([comment1, comment2])
            db.session.commit()
            # 回复
            reply1 = Comment(user_id=1, video_id=1, content='我也觉得！', parent_id=comment1.id)
            db.session.add(reply1)
            db.session.commit()
            print("Test comments inserted.")

        if Collection.query.count() == 0:
            collection1 = Collection(user_id=1, video_id=1)
            db.session.add(collection1)
            db.session.commit()
            print("Test collection inserted.")
