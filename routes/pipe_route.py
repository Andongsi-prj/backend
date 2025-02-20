import requests
from flask import Blueprint, request, jsonify

pipe_route = Blueprint('pipe', __name__)
<<<<<<< HEAD
FASTAPI_URL = "http://192.168.0.163:8001/predict/"
=======
FASTAPI_URL = "http://5gears.iptime.org:8001/predict/"
>>>>>>> 58445be5501f17d08260a11cea43f0e11894eff0

@pipe_route.route("/pipe", methods=['POST'])
def predict():  
    try:
        # Base64 데이터 수신
        image_data = request.json.get('image_base64')
        if not image_data:
            return jsonify({"error": "'image_base64' field missing"}), 400

        # FastAPI 서버로 전달
        response = requests.post(FASTAPI_URL, json={"image_base64": image_data})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500