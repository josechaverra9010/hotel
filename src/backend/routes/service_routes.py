from flask import Blueprint, request, jsonify
from database import execute_query
import uuid
from datetime import datetime

service_bp = Blueprint('service', __name__)

@service_bp.route('/services', methods=['POST'])
def create_service_request():
    data = request.get_json()
    reservation_id = data.get('reservationId')
    room_number = data.get('roomNumber')
    guest_name = data.get('guestName')
    service_type = data.get('type')
    details = data.get('details', '')
    priority = data.get('priority', 'medium')
    
    if not all([reservation_id, room_number, guest_name, service_type]):
        return jsonify({"message": "Faltan datos requeridos"}), 400
    
    request_id = str(uuid.uuid4())
    query = """
        INSERT INTO service_requests (id, reservation_id, room_number, guest_name, type, status, details, priority)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s)
    """
    params = (request_id, reservation_id, room_number, guest_name, service_type, details, priority)
    
    result = execute_query(query, params)
    
    if result is not None:
        return jsonify({
            "success": True, 
            "id": request_id, 
            "createdAt": datetime.now().isoformat()
        }), 201
    else:
        return jsonify({"message": "Error al crear la solicitud"}), 500

@service_bp.route('/services/<reservation_id>', methods=['GET'])
def get_service_history(reservation_id):
    query = "SELECT * FROM service_requests WHERE reservation_id = %s ORDER BY created_at DESC"
    results = execute_query(query, (reservation_id,), fetch=True)
    
    return jsonify(results if results else []), 200
@service_bp.route('/services/<id>/cancel', methods=['PUT'])
def cancel_service_request(id):
    # Verify it's still pending
    check_query = "SELECT status FROM service_requests WHERE id = %s"
    result = execute_query(check_query, (id,), fetch=True)
    
    if not result:
        return jsonify({"message": "Solicitud no encontrada"}), 404
    
    if result[0]['status'] != 'pending':
        return jsonify({"message": "Solo se pueden cancelar solicitudes pendientes"}), 400
        
    query = "UPDATE service_requests SET status = 'cancelled' WHERE id = %s"
    execute_query(query, (id,))
    
    return jsonify({"success": True}), 200
