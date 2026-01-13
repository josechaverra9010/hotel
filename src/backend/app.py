from flask import Flask, jsonify
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

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')

# Register blueprints
app.register_blueprint(unified_auth_bp, url_prefix='/api/auth')
app.register_blueprint(auth_bp, url_prefix='/api/guest')
app.register_blueprint(service_bp, url_prefix='/api/guest')
app.register_blueprint(message_bp, url_prefix='/api/guest')
app.register_blueprint(notification_bp, url_prefix='/api/guest')
app.register_blueprint(catalog_bp, url_prefix='/api/guest')
app.register_blueprint(staff_bp, url_prefix='/api')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "hotel-robles-backend"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
