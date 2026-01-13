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

# CONFIGURACIÓN DEL FRONTEND:
# 'static_folder' apunta a '../dist' porque este archivo vive en 'backend/'
# y el build de Vite genera 'dist/' en la raíz del proyecto.
app = Flask(__name__, static_folder='../dist', static_url_path='/')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# --- RUTAS PARA SERVIR EL FRONTEND (SPA) ---

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Intentamos encontrar el archivo físico en la carpeta dist (js, css, png, etc.)
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Si la ruta no es un archivo (es una ruta de React como /login),
        # servimos el index.html para que el frontend maneje el ruteo.
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
