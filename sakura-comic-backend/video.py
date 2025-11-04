from flask import Blueprint, request, jsonify
from models import Video
from sqlalchemy import desc

video_bp = Blueprint('video', __name__)

@video_bp.route('/vod_list', methods=['GET'])
def get_vod_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category', None, type=str)
    keyword = request.args.get('keyword', None, type=str)

    query = Video.query

    if category:
        query = query.filter(Video.category == category)

    if keyword:
        query = query.filter(Video.title.like(f'%{keyword}%'))

    # 按照更新时间倒序排列
    query = query.order_by(desc(Video.update_time))

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    video_list = [video.to_dict() for video in pagination.items]

    return jsonify({
        'code': 200,
        'data': {
            'list': video_list,
            'total': pagination.total,
            'page': pagination.page,
            'limit': pagination.per_page,
            'pages': pagination.pages
        }
    })

@video_bp.route('/vod_detail', methods=['GET'])
def get_vod_detail():
    vod_id = request.args.get('vod_id', type=int)

    if not vod_id:
        return jsonify({'code': 400, 'msg': '缺少 vod_id 参数'}), 400

    video = Video.query.get(vod_id)

    if not video:
        return jsonify({'code': 404, 'msg': '视频未找到'}), 404

    # 增加观看次数
    video.views += 1
    video.db.session.commit()

    return jsonify({
        'code': 200,
        'data': video.to_dict()
    })
