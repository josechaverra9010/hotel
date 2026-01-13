from flask import Blueprint, request, jsonify
from database import execute_query

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def guest_login():
    data = request.get_json()
    doc_type = data.get('documentType')
    doc_number = data.get('documentNumber')
    
    if not doc_type or not doc_number:
        return jsonify({"message": "Faltan datos de documento"}), 400
    
    # Check if guest exists and has an active reservation
    query = """
        SELECT g.*, r.id as reservation_id, r.room_id, r.check_in, r.check_out, 
               rm.number as room_number, rm.type as room_type, rm.floor as room_floor
        FROM guests g
        JOIN reservations r ON g.id = r.guest_id
        JOIN rooms rm ON r.room_id = rm.id
        WHERE g.document_type = %s AND g.document_number = %s AND r.status = 'checked-in'
    """
    results = execute_query(query, (doc_type, doc_number), fetch=True)
    
    if results:
        guest_data = results[0]
        # Format dates for JSON
        check_in = guest_data['check_in'].isoformat() if hasattr(guest_data['check_in'], 'isoformat') else guest_data['check_in']
        check_out = guest_data['check_out'].isoformat() if hasattr(guest_data['check_out'], 'isoformat') else guest_data['check_out']
        
        return jsonify({
            "success": True,
            "guest": {
                "id": guest_data['id'],
                "firstName": guest_data['first_name'],
                "lastName": guest_data['last_name'],
                "documentType": guest_data['document_type'],
                "documentNumber": guest_data['document_number']
            },
            "reservation": {
                "id": guest_data['reservation_id'],
                "roomId": guest_data['room_id'],
                "roomNumber": guest_data['room_number'],
                "roomType": guest_data['room_type'],
                "roomFloor": guest_data['room_floor'],
                "checkIn": check_in,
                "checkOut": check_out
            }
        }), 200
    else:
        return jsonify({"success": False, "message": "No se encontró una reserva activa"}), 401
@auth_bp.route('/session/status/<res_id>', methods=['GET'])
def check_session_status(res_id):
    query = "SELECT status FROM reservations WHERE id = %s"
    result = execute_query(query, (res_id,), fetch=True)
    
    if not result or result[0]['status'] != 'checked-in':
        return jsonify({"active": False}), 200
    
    return jsonify({"active": True}), 200
