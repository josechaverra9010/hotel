from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Import routes
from routes.auth_routes import auth_bp
from routes.service_routes import service_bp
from routes.message_routes import message_bp
from routes.notification_routes import notification_bp
from routes.catalog_routes import catalog_bp
from routes.staff_routes import staff_bp
from routes.unified_auth_routes import unified_auth_bp

load_dotenv()

# --- FIND DIST FOLDER ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
dist_path = os.path.join(project_root, 'dist')

# Debug: Print paths on startup
print("=" * 50)
print(f"Current dir: {current_dir}")
print(f"Project root: {project_root}")
print(f"Dist path: {dist_path}")
print(f"Dist exists: {os.path.exists(dist_path)}")
if os.path.exists(dist_path):
    print(f"Contents of dist: {os.listdir(dist_path)}")
print("=" * 50)

app = Flask(__name__, static_folder=dist_path, static_url_path='')
CORS(app)

# --- DEBUG ENDPOINT ---
@app.route('/api/debug', methods=['GET'])
def debug_info():
    return jsonify({
        "current_dir": current_dir,
        "project_root": project_root,
        "dist_path": dist_path,
        "dist_exists": os.path.exists(dist_path),
        "static_folder": app.static_folder,
        "static_folder_exists": os.path.exists(app.static_folder) if app.static_folder else False,
        "dist_contents": os.listdir(dist_path) if os.path.exists(dist_path) else [],
        "cwd": os.getcwd()
    }), 200

# --- HEALTH CHECK ---
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "hotel-robles-backend",
        "environment": "production"
    }), 200

# --- REGISTRO DE BLUEPRINTS (API) ---
app.register_blueprint(unified_auth_bp, url_prefix='/api/auth')
app.register_blueprint(auth_bp, url_prefix='/api/guest')
app.register_blueprint(service_bp, url_prefix='/api/guest')
app.register_blueprint(message_bp, url_prefix='/api/guest')
app.register_blueprint(notification_bp, url_prefix='/api/guest')
app.register_blueprint(catalog_bp, url_prefix='/api/guest')
app.register_blueprint(staff_bp, url_prefix='/api')

# --- SERVE REACT APP (MUST BE LAST) ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    print(f"Requested path: {path}")
    print(f"Static folder: {app.static_folder}")
    
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        print(f"Serving file: {path}")
        return send_from_directory(app.static_folder, path)
    else:
        print("Serving index.html")
        index_path = os.path.join(app.static_folder, 'index.html')
        print(f"Index exists: {os.path.exists(index_path)}")
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
