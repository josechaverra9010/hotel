from flask import Flask, jsonify, send_from_directory
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

# --- EL PARCHE DEFINITIVO PARA LAS RUTAS ---
# Buscamos la carpeta 'dist' de forma absoluta para no fallar
current_dir = os.path.dirname(os.path.abspath(__file__)) # carpeta /backend
project_root = os.path.dirname(current_dir) # sube un nivel a la raíz /
dist_path = os.path.join(project_root, 'dist')

app = Flask(__name__, static_folder=dist_path, static_url_path='/')
CORS(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Si no encuentra el archivo o la ruta, manda el index.html
        return send_from_directory(app.static_folder, 'index.html')

# --- REGISTRO DE BLUEPRINTS (API) ---

app.register_blueprint(unified_auth_bp, url_prefix='/api/auth')
app.register_blueprint(auth_bp, url_prefix='/api/guest')
app.register_blueprint(service_bp, url_prefix='/api/guest')
app.register_blueprint(message_bp, url_prefix='/api/guest')
app.register_blueprint(notification_bp, url_prefix='/api/guest')
app.register_blueprint(catalog_bp, url_prefix='/api/guest')
app.register_blueprint(staff_bp, url_prefix='/api')

# --- HEALTH CHECK ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "hotel-robles-backend",
        "environment": "production"
    }), 200

if __name__ == '__main__':
    # Render usa la variable de entorno PORT, si no existe usamos el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

