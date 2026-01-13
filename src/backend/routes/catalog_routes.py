from flask import Blueprint, jsonify
from database import execute_query

catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/catalog/<service_type>', methods=['GET'])
def get_catalog(service_type):
    query = "SELECT * FROM service_catalog WHERE type = %s AND available = TRUE"
    results = execute_query(query, (service_type,), fetch=True)
    return jsonify(results if results else []), 200

@catalog_bp.route('/wifi/<int:floor>', methods=['GET'])
def get_wifi_info(floor):
    query = "SELECT ssid, password FROM wifi_zones WHERE floor = %s"
    results = execute_query(query, (floor,), fetch=True)
    
    if results:
        return jsonify(results[0]), 200
    else:
        # Fallback to lobby wifi if floor specific not found
        query = "SELECT ssid, password FROM wifi_zones WHERE floor = 1"
        results = execute_query(query, fetch=True)
        return jsonify(results[0] if results else {"ssid": "Robles_Guest", "password": "WelcomeRobles"}), 200
