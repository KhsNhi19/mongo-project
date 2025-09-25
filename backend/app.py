import os
from flask import Flask, jsonify, render_template, request
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import json_util
import json

app = Flask(__name__)
CORS(app) # Kích hoạt CORS cho tất cả các route

# --- Cấu hình kết nối MongoDB ---
app.config["MONGO_URI"] = "mongodb://mongo_demo:admin_123@localhost:27017/yelp_db?authSource=admin"
mongo = PyMongo(app)

# --- Route để phục vụ trang Frontend ---
@app.route('/')
def index():
    # Flask sẽ tự tìm file index.html trong thư mục 'templates'
    return render_template('index.html')

# Lấy tất cả các category để điền vào dropdown 
@app.route('/api/categories', methods=['GET'])
def get_all_categories():
    pipeline = [
        # Tách chuỗi categories thành mảng
        { "$addFields": { "categories_array": { "$split": ["$categories", ", "] } } },
        # Unwind mảng
        { "$unwind": "$categories_array" },
        # ĐẾM SỐ LƯỢNG BUSINESS CHO MỖI CATEGORY
        { 
            "$group": { 
                "_id": "$categories_array",
                "count": { "$sum": 1 } 
            } 
        },
        # CHỈ GIỮ LẠI NHỮNG CATEGORY CÓ TỪ 50 BUSINESS TRỞ LÊN
        {
            "$match": {
                "count": { "$gte": 50 }
            }
        },
        # Sắp xếp
        { "$sort": { "_id": 1 } },
        # Định dạng output
        { "$project": { "category": "$_id", "_id": 0 } }
    ]
    try:
        categories_cursor = mongo.db.businesses.aggregate(pipeline)
        categories_list = json.loads(json_util.dumps(categories_cursor))
        return jsonify(categories_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# API MỚI: Lấy thông tin chi tiết của một business
@app.route('/api/businesses/<string:business_id>', methods=['GET'])
def get_business_details(business_id):
    try:
        business = mongo.db.businesses.find_one({"business_id": business_id})
        if business:
            return json.loads(json_util.dumps(business))
        else:
            return jsonify({"error": "Business not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy business theo một category người dùng chọn
@app.route('/api/businesses', methods=['GET'])
def get_businesses_by_category():
    category = request.args.get('category', default='Restaurants', type=str)
    page = request.args.get('page', default=1, type=int)
    limit = 12 
    skip = (page - 1) * limit
    pipeline = [
        {
            "$facet": {
                "results": [
                    { '$match': 
                        { 'categories': 
                            { '$regex': category 
                            } 
                        } 
                    }, { '$sort': 
                        { 'review_count': -1 } },
                    { '$skip': skip 
                    },{ '$limit': limit 
                    },{ '$project': 
                        { 'name': 1, 'city': 1, 'stars': 1, 'review_count': 1, 'business_id': 1 }
                    }
                ],
                "totalCount": [
                    { '$match': 
                        { 'categories': 
                            { '$regex': category 
                            } 
                        } 
                    },{ '$count': 'count' }
                ]
            }
        }
    ]
    try:
        result = list(mongo.db.businesses.aggregate(pipeline))
        businesses_list = result[0]['results']
        total_count = result[0]['totalCount'][0]['count'] if result[0]['totalCount'] else 0
        
        response_data = {
            "businesses": json.loads(json_util.dumps(businesses_list)),
            "total": total_count,
            "page": page,
            "limit": limit
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Lấy 10 ảnh bất kỳ của business đã chọn
@app.route('/api/businesses/<string:business_id>/photos', methods=['GET'])
def get_business_photos(business_id):
    pipeline = [
    {
        '$match': {
            'business_id': business_id
        }
    }, {
        '$limit': 10
    }
    ]
    try:
        photos_cursor = mongo.db.photos.aggregate(pipeline)
        photos_list = json.loads(json_util.dumps(photos_cursor))
        return jsonify(photos_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy 5 review mới nhất, kèm tên người viết
@app.route('/api/businesses/<string:business_id>/reviews', methods=['GET'])
def get_business_reviews(business_id):
    pipeline = [
    {
        '$match': {
            'business_id': business_id
        }
    }, {
        '$sort': {
            'date': -1
        }
    }, {
        '$limit': 5
    }, {
        '$lookup': {
            'from': 'users', 
            'localField': 'user_id', 
            'foreignField': 'user_id', 
            'as': 'userInfo'
        }
    }, {
        '$unwind': '$userInfo'
    }, {
        '$project': {
            'stars': 1, 
            'text': 1, 
            'date': 1, 
            'userName': '$userInfo.name', 
            '_id': 0
        }
    }
    ]
    try:
        reviews_cursor = mongo.db.reviews.aggregate(pipeline)
        reviews_list = json.loads(json_util.dumps(reviews_cursor))
        return jsonify(reviews_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

# Lấy các mẹo/gợi ý được thích nhiều nhất
@app.route('/api/businesses/<string:business_id>/tips', methods=['GET'])
def get_business_tips(business_id):
    pipeline = [
    {
        '$match': {
            'business_id': business_id
        }
    }, {
        '$sort': {
            'compliment_count': -1
        }
    }, {
        '$limit': 20
    }
]
    try:
        tips_cursor = mongo.db.tips.aggregate(pipeline)
        tips_list = json.loads(json_util.dumps(tips_cursor))
        return jsonify(tips_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# Đếm số lượt check-in theo ngày trong tuần
@app.route('/api/businesses/<string:business_id>/checkins', methods=['GET'])
def get_business_checkins(business_id):
    pipeline = [
    {
        '$match': {
            'business_id': business_id
        }
    }, {
        '$unwind': '$date'
    }, {
        '$group': {
            '_id': {
                '$dayOfWeek': '$date'
            }, 
            'checkinCount': {
                '$sum': 1
            }
        }
    }, {
        '$sort': {
            '_id': 1
        }
    }
    ]
    try:
        checkins_cursor = mongo.db.checkins.aggregate(pipeline)
        checkins_list = json.loads(json_util.dumps(checkins_cursor))
        return jsonify(checkins_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Text Search trong Reviews
@app.route('/api/reviews/search', methods=['GET'])
def search_reviews():
    search_term = request.args.get('q', default='', type=str)

    if not search_term:
        return jsonify({"error": "Missing search term 'q'"}), 400

    pipeline = [
    {
        '$match': {
            '$text': {
                '$search': search_term
            }, 
            'stars': {
                '$gte': 4
            }
        }
    }, {
        '$sort': {
            'score': {
                '$meta': 'textScore'
            }
        }
    }, {
        '$limit': 10
    }, {
        '$lookup': {
            'from': 'businesses', 
            'localField': 'business_id', 
            'foreignField': 'business_id', 
            'as': 'businessInfo'
        }
    }, {
        '$unwind': '$businessInfo'
    }, {
        "$project": {
            "businessName": "$businessInfo.name",
            "reviewText": "$text",
            "reviewStars": "$stars",
            "businessId": "$business_id",
            "_id": 0
        }
    }
    ]
    try:
        results_cursor = mongo.db.reviews.aggregate(pipeline)
        results_list = json.loads(json_util.dumps(results_cursor))
        return jsonify(results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Tìm Business gần một tọa độ
@app.route('/api/businesses/nearby', methods=['GET'])
def get_businesses_nearby():
    try:
        lon = float(request.args.get('lon'))
        lat = float(request.args.get('lat'))
        category = request.args.get('category', default='Restaurants', type=str)
        
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid or missing 'lon' and 'lat' parameters"}), 400

    pipeline = [
        {
            "$geoNear": {
                "near": {
                    "type": "Point",
                    "coordinates": [lon, lat] # Lấy tọa độ động từ URL
                },
                "distanceField": "distance_meters",
                "maxDistance": 5000, # Bán kính 5km
                "query": { "categories": category 
                },
                "spherical": True
            }
        },
        { "$limit": 12 },
        {
            "$project": {
                "name": 1, 
                "address": 1, 
                "stars": 1, 
                "city": 1, 
                "review_count": 1,
                "distance_km": { "$round": [{ "$divide": ["$distance_meters", 1000] }, 2] },
                "business_id": 1,
                "_id": 0
            }
        }
    ]
    try:
        results_cursor = mongo.db.businesses.aggregate(pipeline)
        results_list = json.loads(json_util.dumps(results_cursor))
        return jsonify(results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    app.run(debug=True)

