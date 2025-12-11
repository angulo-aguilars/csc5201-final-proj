from flask import Flask, request, jsonify, g
from pymongo import MongoClient
from bson.objectid import ObjectId
from functools import wraps
import jwt
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sandra1212')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

# --- CONFIGURATION FOR IMAGE UPLOADS ---
# Define the internal folder where images will be saved inside the container
UPLOAD_FOLDER = '/app/images' 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the UPLOAD_FOLDER exists (important for container startup)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# --- Database Setup (MongoDB) ---
client = MongoClient(MONGO_URI)
db = client['recipe_manager']
recipes_collection = db['recipes']

# --- Middleware/Decorators ---

def token_required(f):
    """
    Decorator to ensure the request has a valid JWT.
    This logic verifies the token directly, assuming the SECRET_KEY is shared.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Authorization token is missing!'}), 401
        
        try:
            # Decode and verify the token using the shared secret key
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Inject the authenticated user ID into the request object (g.user_id)
            g.user_id = data.get('user_id')
        except:
            return jsonify({'message': 'Token is invalid or expired!'}), 401

        return f(*args, **kwargs)

    return decorated

@app.before_request
def start_timer():
    """Start timer for Usage Statistics"""
    g.start_time = time.time()

@app.after_request
def log_request(response):
    """Log request for Usage Statistics"""
    latency_ms = (time.time() - g.start_time) * 1000
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "service": "RecipeCatalog",
        "user_id": getattr(g, 'user_id', 'unauthenticated'),
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "latency_ms": f"{latency_ms:.2f}ms"
    }
    # This just prints to the console/container logs
    print(f"METRIC LOG: {log_entry}") 
    
    return response

# --- Routes (Requires Token) ---

@app.route('/recipes', methods=['POST'])
@token_required
def create_recipe():
    title = request.form.get('title')
    instructions = request.form.get('instructions', '')
    image_url = None

    if not title:
        return jsonify({'message': 'Missing title in form data'}), 400
    if 'image' in request.files:
        image_file = request.files['image']
        # Check if a file was actually selected and has a filename
        if image_file.filename != '':
            # 1. Sanitize the filename for security
            filename = secure_filename(image_file.filename)
            # 2. Define the full save path inside the container
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # 3. Save the file
            image_file.save(save_path)
            # 4. Store the internal URL/path for the database
            image_url = f"app/images/{filename}"
    recipe = {
        'title': title,
        'instructions': instructions,
	'image_url': image_url,
        'user_id': g.user_id # Associate recipe with authenticated user
    }
    result = recipes_collection.insert_one(recipe)
    return jsonify({'message': 'Recipe created', 'id': str(result.inserted_id), 'image_url': image_url}), 201

@app.route('/recipes', methods=['GET'])
@token_required
def get_recipes():
    # Only show recipes belonging to the authenticated user
    user_recipes = list(recipes_collection.find({'user_id': g.user_id}, {'_id': 0})) 
    return jsonify(user_recipes), 200

@app.route('/recipes/<recipe_id>', methods=['PUT'])
@token_required
def update_recipe(recipe_id):
    data = request.get_json()
    try:
        # Find and update only if it belongs to the authenticated user
        result = recipes_collection.update_one(
            {'_id': ObjectId(recipe_id), 'user_id': g.user_id},
            {'$set': data}
        )
        if result.matched_count == 0:
            return jsonify({'message': 'Recipe not found or unauthorized'}), 404
        return jsonify({'message': 'Recipe updated'}), 200
    except Exception:
        return jsonify({'message': 'Invalid Recipe ID format'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
