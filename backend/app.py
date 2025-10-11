import os
from flask import Flask, jsonify, render_template, request
from flask_pymongo import PyMongo
from flask_cors import CORS
from bson import json_util
import json
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app, path='/metrics')
CORS(app) 
app.config["MONGO_URI"] = "mongodb://mongo_demo:admin_123@mongo1:27017,mongo2:27017,mongo3:27017/yelp_db?authSource=admin&replicaSet=rs0"
mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('index.html')

# Lấy tất cả các category để điền vào dropdown 
@app.route('/api/categories', methods=['GET'])
def get_all_categories():
    pipeline = [
        { "$unwind": "$categories_array" },
        { "$group": { 
            "_id": "$categories_array", 
            "count": { 
                "$sum": 1 
                } 
            } },
        { "$match": { 
            "count": { 
                "$gte": 50 
                } 
                } },
        { "$sort": { 
            "_id": 1 
            } },
        { "$project": { 
            "category": "$_id", 
            "_id": 0 
            } }
    ]
    try:
        categories_cursor = mongo.db.businesses.aggregate(pipeline)
        categories_list = json.loads(json_util.dumps(categories_cursor))
        return jsonify(categories_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Lấy business theo một category người dùng chọn 
@app.route('/api/businesses', methods=['GET'])
def get_businesses_by_category():
    category = request.args.get('category', default='Restaurants', type=str)
    page = request.args.get('page', default=1, type=int)
    limit = 12 
    skip = (page - 1) * limit
    query = { 'categories_array': category }

    try:
        total_count = mongo.db.businesses.count_documents(query)
        businesses_cursor = mongo.db.businesses.find(query).sort([('review_count', -1)]).skip(skip).limit(limit)
        
        projected_businesses = []
        for i in businesses_cursor:
            projected_businesses.append({
                "_id": i["_id"],
                "name": i.get("name"),
                "city": i.get("city"),
                "stars": i.get("stars"),
                "review_count": i.get("review_count"),
                "business_id": i.get("business_id")
            })

        response_data = {
            "businesses": json.loads(json_util.dumps(projected_businesses)),
            "total": total_count,
            "page": page,
            "limit": limit
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy chi tiết theo bussiness_id
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

# Lấy ảnh
@app.route('/api/businesses/<string:business_id>/photos', methods=['GET'])
def get_business_photos(business_id):
    pipeline = [
        { '$match': { 
            'business_id': business_id 
            } },
        { '$limit': 10 }
    ]
    try:
        photos_cursor = mongo.db.photos.aggregate(pipeline)
        photos_list = json.loads(json_util.dumps(photos_cursor))
        return jsonify(photos_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Lấy reviews
@app.route('/api/businesses/<string:business_id>/reviews', methods=['GET'])
def get_business_reviews(business_id):
    pipeline = [
        { '$match': { 
            'business_id': business_id 
            } },
        { '$sort': { 
            'date': -1 
            } },
        { '$limit': 5 },
        { '$lookup': { 
            'from': 'users', 
            'localField': 'user_id', 
            'foreignField': 'user_id', 
            'as': 'userInfo' 
            } },
        { '$unwind': '$userInfo' },
        { '$project': { 
            'stars': 1, 
            'text': 1, 
            'date': 1, 
            'userName': 
            '$userInfo.name', 
            '_id': 0 
            } }
    ]
    try:
        reviews_cursor = mongo.db.reviews.aggregate(pipeline)
        reviews_list = json.loads(json_util.dumps(reviews_cursor))
        return jsonify(reviews_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500  

# Lấy tips
@app.route('/api/businesses/<string:business_id>/tips', methods=['GET'])
def get_business_tips(business_id):
    page = request.args.get('page', default=1, type=int)
    limit = 5  
    skip = (page - 1) * limit
    
    query = { 'business_id': business_id }

    try:
        total_count = mongo.db.tips.count_documents(query)
        tips_cursor = mongo.db.tips.find(query).sort([('compliment_count', -1)]).skip(skip).limit(limit)

        response_data = {
            "tips": json.loads(json_util.dumps(list(tips_cursor))),
            "total": total_count,
            "page": page,
            "limit": limit
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Lấy check-ins
@app.route('/api/businesses/<string:business_id>/checkins', methods=['GET'])
def get_business_checkins(business_id):
    pipeline = [
        { '$match': { 'business_id': business_id } },
        { '$unwind': '$date' },
        { '$group': { '_id': { '$dayOfWeek': '$date' }, 'checkinCount': { '$sum': 1 } } },
        { '$sort': { '_id': 1 } }
    ]
    try:
        checkins_cursor = mongo.db.checkins.aggregate(pipeline)
        checkins_list = json.loads(json_util.dumps(checkins_cursor))
        return jsonify(checkins_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# CÁC API TÌM KIẾM NÂNG CAO 
# Text Search
@app.route('/api/reviews/search', methods=['GET'])
def search_reviews():
    search_term = request.args.get('q', default='', type=str)
    if not search_term:
        return jsonify({"error": "Missing search term 'q'"}), 400
    pipeline = [
        { '$match': { '$text': { '$search': search_term }, 'stars': { '$gte': 4 } } },
        { '$sort': { 'score': { '$meta': 'textScore' } } },
        { '$limit': 10 },
        { '$lookup': { 'from': 'businesses', 'localField': 'business_id', 'foreignField': 'business_id', 'as': 'businessInfo' } },
        { '$unwind': '$businessInfo' },
        { "$project": { "businessName": "$businessInfo.name", "reviewText": "$text", "reviewStars": "$stars", "businessId": "$business_id", "_id": 0 } }
    ]
    try:
        results_cursor = mongo.db.reviews.aggregate(pipeline)
        results_list = json.loads(json_util.dumps(results_cursor))
        return jsonify(results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Tìm gần đây
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
                "near": { "type": "Point", "coordinates": [lon, lat] },
                "distanceField": "distance_meters",
                "maxDistance": 5000,
                "query": { "categories": {"$regex": category} },
                "spherical": True
            }
        },
        { "$limit": 12 },
        { "$project": { 
            "name": 1, 
            "address": 1, 
            "stars": 1, 
            "city": 1, 
            "review_count": 1, 
            "distance_km": { "$round": [{ "$divide": ["$distance_meters", 1000] }, 2] }, 
            "business_id": 1, 
            "latitude": 1,
            "longitude": 1,
            "_id": 0 } }
    ]
    try:
        results_cursor = mongo.db.businesses.aggregate(pipeline)
        results_list = json.loads(json_util.dumps(results_cursor))
        return jsonify(results_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API cho mô hình Tham chiếu (Referencing)
@app.route('/api/test/reviews-referenced/<string:business_id>', methods=['GET'])
def test_referenced_reviews(business_id):
    try:
        reviews_cursor = mongo.db.reviews.find(
            {'business_id': business_id}).sort([('date', -1)]).limit(5)
        reviews_list = json.loads(json_util.dumps(list(reviews_cursor)))
        return jsonify(reviews_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API cho mô hình Lồng ghép (Embedding)
@app.route('/api/test/reviews-embedded/<string:business_id>', methods=['GET'])
def test_embedded_reviews(business_id):
    try:
        # Dùng $project và $slice để lấy 5 review mới nhất từ mảng
        pipeline = [
            { '$match': { 
                'business_id': business_id 
                } },
            { '$project': {
                'reviews': { '$slice': ['$reviews', -5] }
                }}
        ]
        result = list(mongo.db.businesses_embedded.aggregate(pipeline))
        reviews_list = json.loads(json_util.dumps(result[0]['reviews'] if result else []))
        return jsonify(reviews_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)