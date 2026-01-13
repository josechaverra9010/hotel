from flask import Blueprint, request, jsonify
from database import execute_query
import uuid
from datetime import datetime

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/staff/login', methods=['POST'])
def staff_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    query = "SELECT id, name, email, role FROM staff WHERE email = %s AND password = %s"
    results = execute_query(query, (email, password), fetch=True)
    
    if results:
        return jsonify({"success": True, "user": results[0]}), 200
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@staff_bp.route('/staff/dashboard/stats', methods=['GET'])
def get_stats():
    # Rooms stats
    total_rooms = execute_query("SELECT COUNT(*) as count FROM rooms", fetch=True)[0]['count']
    occupied = execute_query("SELECT COUNT(*) as count FROM rooms WHERE status = 'occupied'", fetch=True)[0]['count']
    available = execute_query("SELECT COUNT(*) as count FROM rooms WHERE status = 'available'", fetch=True)[0]['count']
    
    # Message stats
    unread_messages = execute_query("SELECT COUNT(*) as count FROM messages WHERE is_read = FALSE AND sender = 'guest'", fetch=True)[0]['count']
    
    # Service stats
    pending_requests = execute_query("SELECT COUNT(*) as count FROM service_requests WHERE status = 'pending'", fetch=True)[0]['count']
    
    return jsonify({
        "rooms": {"total": total_rooms, "occupied": occupied, "available": available},
        "unreadMessages": unread_messages,
        "pendingRequests": pending_requests
    }), 200

@staff_bp.route('/staff/rooms', methods=['GET'])
def get_all_rooms():
    query = "SELECT * FROM rooms ORDER BY number ASC"
    results = execute_query(query, fetch=True)
    return jsonify(results), 200

@staff_bp.route('/staff/rooms/<room_id>/status', methods=['PUT'])
def update_room_status(room_id):
    data = request.json
    status = data.get('status')
    
    # Update room status
    query = "UPDATE rooms SET status = %s WHERE id = %s"
    execute_query(query, (status, room_id))
    
    # If room becomes available or cleaning, we should ensure any active reservation is marked as checked-out
    # to prevent data leaking to the next guest.
    if status in ['available', 'cleaning']:
        # Find active (checked-in) reservation for this room
        find_res = "SELECT id FROM reservations WHERE room_id = %s AND status = 'checked-in'"
        active_res = execute_query(find_res, (room_id,), fetch=True)
        
        for res in active_res:
            res_id = res['id']
            # Mark reservation as checked-out
            execute_query("UPDATE reservations SET status = 'checked-out' WHERE id = %s", (res_id,))
            
        # Get room number for room-specific cleanup
        room_data = execute_query("SELECT number FROM rooms WHERE id = %s", (room_id,), fetch=True)
        if room_data:
            room_number = room_data[0]['number']
            # Also cleanup any notifications sent specifically to the ROOM (without reservation_id)
            # to ensure the next guest starts with a fresh state.
            execute_query("DELETE FROM notifications WHERE room_number = %s AND reservation_id IS NULL", (room_number,))
            
    return jsonify({"success": True}), 200

@staff_bp.route('/staff/reservations', methods=['GET'])
def get_all_reservations():
    query = """
        SELECT r.*, g.first_name, g.last_name, rm.number as room_number, rm.floor as room_floor
        FROM reservations r
        JOIN guests g ON r.guest_id = g.id
        JOIN rooms rm ON r.room_id = rm.id
        ORDER BY r.check_in DESC
    """
    results = execute_query(query, fetch=True)
    # Format dates
    for r in results:
        r['check_in'] = r['check_in'].isoformat() if hasattr(r['check_in'], 'isoformat') else r['check_in']
        r['check_out'] = r['check_out'].isoformat() if hasattr(r['check_out'], 'isoformat') else r['check_out']
        r['guestName'] = f"{r['first_name']} {r['last_name']}"
    return jsonify(results), 200

@staff_bp.route('/staff/reservations/<res_id>', methods=['PUT'])
def update_reservation(res_id):
    data = request.json
    status = data.get('status')
    
    query = "UPDATE reservations SET status = %s WHERE id = %s"
    execute_query(query, (status, res_id))
    
    # If check-in or check-out, update room status automatically
    if status == 'checked-in':
        room_query = "UPDATE rooms SET status = 'occupied' WHERE id = (SELECT room_id FROM reservations WHERE id = %s)"
        execute_query(room_query, (res_id,))
    elif status == 'checked-out':
        # 1. Update room status to cleaning
        room_query = "UPDATE rooms SET status = 'cleaning' WHERE id = (SELECT room_id FROM reservations WHERE id = %s)"
        execute_query(room_query, (res_id,))
        
        # 2. Cleanup room-specific notifications that don't have a reservation_id
        # to ensure the next guest starts with a fresh state.
        room_data = execute_query("SELECT rm.number FROM rooms rm JOIN reservations r ON rm.id = r.room_id WHERE r.id = %s", (res_id,), fetch=True)
        if room_data:
            room_number = room_data[0]['number']
            execute_query("DELETE FROM notifications WHERE room_number = %s AND reservation_id IS NULL", (room_number,))
            
    return jsonify({"success": True}), 200

@staff_bp.route('/staff/reservations/<res_id>', methods=['DELETE'])
def delete_reservation(res_id):
    # 1. Delete associated data
    execute_query("DELETE FROM messages WHERE reservation_id = %s", (res_id,))
    execute_query("DELETE FROM service_requests WHERE reservation_id = %s", (res_id,))
    execute_query("DELETE FROM notifications WHERE reservation_id = %s", (res_id,))
    
    # 2. Delete reservation
    result = execute_query("DELETE FROM reservations WHERE id = %s", (res_id,))
    
    if result is not None:
        return jsonify({"success": True}), 200
    return jsonify({"message": "Error al eliminar reserva"}), 500

@staff_bp.route('/staff/reservations', methods=['POST'])
def create_reservation():
    data = request.json
    guest_data = data.get('guest')
    res_data = data.get('reservation')
    
    if not guest_data or not res_data:
        return jsonify({"message": "Faltan datos de huésped o reserva"}), 400
        
    doc_type = guest_data.get('documentType')
    doc_number = guest_data.get('documentNumber')
    
    # 1. Check if guest exists
    query_guest = "SELECT id FROM guests WHERE document_type = %s AND document_number = %s"
    existing_guest = execute_query(query_guest, (doc_type, doc_number), fetch=True)
    
    if existing_guest:
        guest_id = existing_guest[0]['id']
    else:
        # Create new guest
        guest_id = str(uuid.uuid4())
        insert_guest = """
            INSERT INTO guests (id, first_name, last_name, document_type, document_number, email, phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(insert_guest, (
            guest_id, 
            guest_data.get('firstName'), 
            guest_data.get('lastName'), 
            doc_type, 
            doc_number,
            guest_data.get('email', ''),
            guest_data.get('phone', '')
        ))
    
    # 2. Create reservation
    res_id = str(uuid.uuid4())
    insert_res = """
        INSERT INTO reservations (id, guest_id, room_id, check_in, check_out, status, total_amount)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(insert_res, (
        res_id,
        guest_id,
        res_data.get('roomId'),
        res_data.get('checkIn'),
        res_data.get('checkOut'),
        res_data.get('status', 'confirmed'),
        res_data.get('totalAmount', 0)
    ))
    
    # 3. Update room status if confirmed/checked-in
    status = res_data.get('status', 'confirmed')
    if status in ['confirmed', 'checked-in']:
        room_status = 'occupied' if status == 'checked-in' else 'available' 
        # Actually, if it's confirmed, it might stay available until check-in, 
        # but for the "assign room" feature, usually it means they are coming or here.
        # Let's follow the plan: "Automatically update room status to 'occupied'".
        execute_query("UPDATE rooms SET status = 'occupied' WHERE id = %s", (res_data.get('roomId'),))
        
    return jsonify({"success": True, "reservationId": res_id}), 201

@staff_bp.route('/staff/services', methods=['GET'])
def get_all_services():
    query = "SELECT * FROM service_requests ORDER BY created_at DESC"
    results = execute_query(query, fetch=True)
    for s in results:
        s['created_at'] = s['created_at'].isoformat() if hasattr(s['created_at'], 'isoformat') else s['created_at']
        s['completed_at'] = s['completed_at'].isoformat() if hasattr(s['completed_at'], 'isoformat') else s['completed_at']
    return jsonify(results), 200

@staff_bp.route('/staff/messages', methods=['GET'])
def get_all_messages():
    # Group by reservation or just list all
    query = "SELECT * FROM messages ORDER BY timestamp ASC"
    results = execute_query(query, fetch=True)
    for m in results:
        m['timestamp'] = m['timestamp'].isoformat() if hasattr(m['timestamp'], 'isoformat') else m['timestamp']
    return jsonify(results), 200
@staff_bp.route('/staff/services/<id>/status', methods=['PUT'])
def update_service_status(id):
    data = request.json
    status = data.get('status')
    
    if status == 'completed':
        query = "UPDATE service_requests SET status = %s, completed_at = %s WHERE id = %s"
        execute_query(query, (status, datetime.now(), id))
    else:
        query = "UPDATE service_requests SET status = %s WHERE id = %s"
        execute_query(query, (status, id))
        
    return jsonify({"success": True}), 200

# --- ADMIN ROUTES ---

# Room Management
@staff_bp.route('/staff/rooms', methods=['POST'])
def add_room():
    data = request.json
    room_id = str(uuid.uuid4())
    query = """
        INSERT INTO rooms (id, number, floor, type, status, price_per_night, capacity, amenities)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, (
        room_id, data.get('number'), data.get('floor'), 
        data.get('type'), data.get('status', 'available'),
        data.get('price_per_night'), data.get('capacity'), data.get('amenities', '')
    ))
    return jsonify({"success": True, "id": room_id}), 201

@staff_bp.route('/staff/rooms/<room_id>', methods=['PUT'])
def update_room_details(room_id):
    data = request.json
    query = """
        UPDATE rooms 
        SET number = %s, floor = %s, type = %s, price_per_night = %s, capacity = %s, amenities = %s
        WHERE id = %s
    """
    execute_query(query, (
        data.get('number'), data.get('floor'), data.get('type'),
        data.get('price_per_night'), data.get('capacity'), data.get('amenities'),
        room_id
    ))
    return jsonify({"success": True}), 200

@staff_bp.route('/staff/rooms/<room_id>', methods=['DELETE'])
def delete_room(room_id):
    execute_query("DELETE FROM rooms WHERE id = %s", (room_id,))
    return jsonify({"success": True}), 200

# Staff Management
@staff_bp.route('/staff/users', methods=['GET'])
def get_staff_users():
    results = execute_query("SELECT id, name, email, role, created_at FROM staff", fetch=True)
    for s in results:
        s['created_at'] = s['created_at'].isoformat() if hasattr(s['created_at'], 'isoformat') else s['created_at']
    return jsonify(results), 200

@staff_bp.route('/staff/users', methods=['POST'])
def add_staff_user():
    data = request.json
    user_id = str(uuid.uuid4())
    query = "INSERT INTO staff (id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)"
    execute_query(query, (user_id, data.get('name'), data.get('email'), data.get('password'), data.get('role')))
    return jsonify({"success": True, "id": user_id}), 201

@staff_bp.route('/staff/users/<user_id>', methods=['PUT'])
def update_staff_user(user_id):
    data = request.json
    if data.get('password'):
        query = "UPDATE staff SET name = %s, email = %s, password = %s, role = %s WHERE id = %s"
        execute_query(query, (data.get('name'), data.get('email'), data.get('password'), data.get('role'), user_id))
    else:
        query = "UPDATE staff SET name = %s, email = %s, role = %s WHERE id = %s"
        execute_query(query, (data.get('name'), data.get('email'), data.get('role'), user_id))
    return jsonify({"success": True}), 200

@staff_bp.route('/staff/users/<user_id>', methods=['DELETE'])
def delete_staff_user(user_id):
    execute_query("DELETE FROM staff WHERE id = %s", (user_id,))
    return jsonify({"success": True}), 200

# Service Catalog Management
@staff_bp.route('/staff/catalog', methods=['GET'])
def get_catalog():
    results = execute_query("SELECT * FROM service_catalog", fetch=True)
    return jsonify(results), 200

@staff_bp.route('/staff/catalog', methods=['POST'])
def add_catalog_item():
    data = request.json
    item_id = str(uuid.uuid4())
    query = """
        INSERT INTO service_catalog (id, type, category, name, description, price, icon, available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, (
        item_id, data.get('type'), data.get('category'), 
        data.get('name'), data.get('description'), data.get('price'),
        data.get('icon'), data.get('available', True)
    ))
    return jsonify({"success": True, "id": item_id}), 201

@staff_bp.route('/staff/catalog/<item_id>', methods=['PUT'])
def update_catalog_item(item_id):
    data = request.json
    query = """
        UPDATE service_catalog 
        SET type = %s, category = %s, name = %s, description = %s, price = %s, icon = %s, available = %s
        WHERE id = %s
    """
    execute_query(query, (
        data.get('type'), data.get('category'), data.get('name'),
        data.get('description'), data.get('price'), data.get('icon'),
        data.get('available'), item_id
    ))
    return jsonify({"success": True}), 200

@staff_bp.route('/staff/catalog/<item_id>', methods=['DELETE'])
def delete_catalog_item(item_id):
    execute_query("DELETE FROM service_catalog WHERE id = %s", (item_id,))
    return jsonify({"success": True}), 200

# WiFi Settings
@staff_bp.route('/staff/wifi', methods=['GET'])
def get_wifi_settings():
    results = execute_query("SELECT * FROM wifi_zones ORDER BY floor ASC", fetch=True)
    return jsonify(results), 200

@staff_bp.route('/staff/wifi/<int:floor>', methods=['PUT'])
def update_wifi_settings(floor):
    data = request.json
    # Check if exists
    exists = execute_query("SELECT id FROM wifi_zones WHERE floor = %s", (floor,), fetch=True)
    if exists:
        query = "UPDATE wifi_zones SET ssid = %s, password = %s, location_description = %s WHERE floor = %s"
        execute_query(query, (data.get('ssid'), data.get('password'), data.get('location_description'), floor))
    else:
        query = "INSERT INTO wifi_zones (floor, ssid, password, location_description) VALUES (%s, %s, %s, %s)"
        execute_query(query, (floor, data.get('ssid'), data.get('password'), data.get('location_description')))
    return jsonify({"success": True}), 200
