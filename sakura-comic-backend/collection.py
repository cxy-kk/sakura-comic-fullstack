from flask import Blueprint, request, jsonify, g
from models import db, Collection, Video
from auth import token_required
from sqlalchemy.exc import IntegrityError

collection_bp = Blueprint('collection', __name__)

@collection_bp.route('/collection/add', methods=['GET'])
@token_required
def add_collection():
    vod_id = request.args.get('vod_id', type=int)

    if not vod_id:
        return jsonify({'code': 400, 'msg': '缺少 vod_id 参数'}), 400

    video = Video.query.get(vod_id)
    if not video:
        return jsonify({'code': 404, 'msg': '视频不存在'}), 404

    new_collection = Collection(user_id=g.current_user.id, video_id=vod_id)

    try:
        db.session.add(new_collection)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '收藏成功'})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'code': 409, 'msg': '已收藏'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'收藏失败: {str(e)}'}), 500

@collection_bp.route('/collection/remove', methods=['GET'])
@token_required
def remove_collection():
    vod_id = request.args.get('vod_id', type=int)

    if not vod_id:
        return jsonify({'code': 400, 'msg': '缺少 vod_id 参数'}), 400

    collection = Collection.query.filter_by(user_id=g.current_user.id, video_id=vod_id).first()

    if collection:
        db.session.delete(collection)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '取消收藏成功'})
    else:
        return jsonify({'code': 404, 'msg': '未收藏'}), 404

@collection_bp.route('/collection/is_collection', methods=['GET'])
@token_required
def is_collection():
    vod_id = request.args.get('vod_id', type=int)

    if not vod_id:
        return jsonify({'code': 400, 'msg': '缺少 vod_id 参数'}), 400

    is_collected = Collection.query.filter_by(user_id=g.current_user.id, video_id=vod_id).first() is not None

    return jsonify({'code': 200, 'data': {'is_collected': is_collected}})

@collection_bp.route('/collection/show', methods=['GET'])
@token_required
def show_collect_video():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    pagination = Collection.query.filter_by(user_id=g.current_user.id).paginate(
        page=page, per_page=limit, error_out=False
    )

    collected_videos = []
    for collection in pagination.items:
        video = Video.query.get(collection.video_id)
        if video:
            collected_videos.append(video.to_dict())

    return jsonify({
        'code': 200,
        'data': {
            'list': collected_videos,
            'total': pagination.total,
            'page': pagination.page,
            'limit': pagination.per_page,
            'pages': pagination.pages
        }
    })
