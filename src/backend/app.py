from flask import Flask, jsonify, send_from_directory # Agregamos send_from_directory
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

# Configuramos Flask para que busque el front en la carpeta 'dist' que está un nivel arriba
app = Flask(__name__, static_folder='../dist', static_url_path='/')
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# --- RUTAS PARA SERVIR EL FRONTEND ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    # Si el archivo existe en dist (css, js, imagenes), lo sirve
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Si no existe o es la raíz, manda el index.html de React
        return send_from_directory(app.static_folder, 'index.html')
# -------------------------------------

# Register blueprints
app.register_blueprint(unified_auth_bp, url_prefix='/api/auth')
app.register_blueprint(auth_bp, url_prefix='/api/guest')
app.register_blueprint(service_bp, url_prefix='/api/guest')
app.register_blueprint(message_bp, url_prefix='/api/guest')
app.register_blueprint(notification_bp, url_prefix='/api/guest')
app.register_blueprint(catalog_bp, url_prefix='/api/guest')
app.register_blueprint(staff_bp, url_prefix='/api')

@app.route('/api/health', methods=['GET']) # Cambié a /api/health para no chocar
def health_check():
    return jsonify({"status": "healthy", "service": "hotel-robles-backend"}), 200

if __name__ == '__main__':
    # Usamos el puerto de Render si existe, si no, el 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
