from flask import Blueprint, request, jsonify
from database import execute_query
from datetime import datetime

unified_auth_bp = Blueprint('unified_auth', __name__)

@unified_auth_bp.route('/login', methods=['POST'])
def unified_login():
    data = request.get_json()
    identifier = data.get('identifier') # email or documentNumber
    password = data.get('password') # for staff
    doc_type = data.get('documentType') # for guest

    # 1. Try Staff Login (Email/Password)
    if identifier and password:
        staff_query = "SELECT id, name, email, role FROM staff WHERE email = %s AND password = %s"
        staff_results = execute_query(staff_query, (identifier, password), fetch=True)
        if staff_results:
            return jsonify({
                "success": True,
                "role": staff_results[0]['role'],
                "user": staff_results[0]
            }), 200

    # 2. Try Guest Login (DocType/DocNumber)
    # Use identifier as documentNumber if password is not provided or if staff login failed
    target_doc_num = identifier
    if doc_type and target_doc_num:
        guest_query = """
            SELECT g.*, r.id as reservation_id, r.room_id, r.check_in, r.check_out, 
                   rm.number as room_number, rm.type as room_type, rm.floor as room_floor
            FROM guests g
            JOIN reservations r ON g.id = r.guest_id
            JOIN rooms rm ON r.room_id = rm.id
            WHERE g.document_type = %s AND g.document_number = %s AND r.status = 'checked-in'
        """
        guest_results = execute_query(guest_query, (doc_type, target_doc_num), fetch=True)
        
        if guest_results:
            guest_data = guest_results[0]
            check_in = guest_data['check_in'].isoformat() if hasattr(guest_data['check_in'], 'isoformat') else guest_data['check_in']
            check_out = guest_data['check_out'].isoformat() if hasattr(guest_data['check_out'], 'isoformat') else guest_data['check_out']
            
            return jsonify({
                "success": True,
                "role": "guest",
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

    return jsonify({"success": False, "message": "Credenciales inválidas o no hay reserva activa"}), 401
