from flask import Blueprint, request, jsonify, g
from models import db, Comment, User
from auth import token_required
from sqlalchemy import desc

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/publish/comment/<int:vod_id>', methods=['POST'])
@token_required
def publish_comment(vod_id):
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'code': 400, 'msg': '评论内容不能为空'}), 400

    new_comment = Comment(
        user_id=g.current_user.id,
        video_id=vod_id,
        content=content,
        parent_id=None # 主评论
    )

    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '评论成功'})

@comment_bp.route('/reply/comment/<int:comment_id>', methods=['POST'])
@token_required
def reply_comment(comment_id):
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'code': 400, 'msg': '回复内容不能为空'}), 400

    parent_comment = Comment.query.get(comment_id)
    if not parent_comment:
        return jsonify({'code': 404, 'msg': '原评论不存在'}), 404

    # 确保回复的 video_id 和原评论一致
    new_reply = Comment(
        user_id=g.current_user.id,
        video_id=parent_comment.video_id,
        content=content,
        parent_id=comment_id
    )

    db.session.add(new_reply)
    db.session.commit()

    return jsonify({'code': 200, 'msg': '回复成功'})

@comment_bp.route('/show/comment/<int:vod_id>', methods=['GET'])
def show_comments(vod_id):
    # 只查询主评论 (parent_id is NULL)
    main_comments_query = Comment.query.filter(
        Comment.video_id == vod_id,
        Comment.parent_id.is_(None)
    ).order_by(desc(Comment.created_at))

    # 简单的分页，前端没有传分页参数，这里默认返回所有主评论
    # 如果需要分页，可以根据前端请求调整
    comments = main_comments_query.all()

    result_list = []
    for comment in comments:
        # 预加载用户信息
        user = User.query.get(comment.user_id)
        comment.author = user # 临时设置，方便 to_dict 调用

        comment_data = comment.to_dict(include_replies=True)
        
        # 处理回复的用户名
        replies_data = []
        for reply in comment.replies.all():
            reply_user = User.query.get(reply.user_id)
            reply_data = reply.to_dict()
            reply_data['username'] = reply_user.username
            replies_data.append(reply_data)
        
        comment_data['replies'] = replies_data
        result_list.append(comment_data)

    return jsonify({
        'code': 200,
        'data': {
            'list': result_list,
            'total': len(result_list)
        }
    })
