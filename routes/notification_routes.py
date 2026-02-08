from flask import Blueprint, request, jsonify
from database import execute_query
from datetime import datetime

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/notifications/<reservation_id>', methods=['GET'])
def get_notifications(reservation_id):
    # Get the room number for this reservation to also pull room-specific non-reservation notifications if any
    # But usually reservation_id is enough. The problem was NULL reservation_id showing to everyone.
    # We only show notifications that are for THIS reservation OR are TRULY global (both NULL).
    query = """
        SELECT * FROM notifications 
        WHERE reservation_id = %s 
        OR (reservation_id IS NULL AND room_number IS NULL)
        ORDER BY created_at DESC
    """
    results = execute_query(query, (reservation_id,), fetch=True)
    
    return jsonify(results if results else []), 200

@notification_bp.route('/notifications', methods=['GET'])
def get_all_notifications():
    query = "SELECT * FROM notifications ORDER BY created_at DESC"
    results = execute_query(query, fetch=True)
    return jsonify(results if results else []), 200

@notification_bp.route('/notifications', methods=['POST'])
def create_notification():
    data = request.json
    title = data.get('title')
    message = data.get('message')
    ntype = data.get('type', 'info')
    # Support both snake_case and camelCase from frontend
    reservation_id = data.get('reservation_id') or data.get('reservationId')
    room_number = data.get('room_number') or data.get('roomNumber')
    
    import uuid
    nid = str(uuid.uuid4())
    
    query = """
        INSERT INTO notifications (id, reservation_id, room_number, title, message, type, is_read, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, FALSE, %s)
    """
    execute_query(query, (nid, reservation_id, room_number, title, message, ntype, datetime.now()))
    
    return jsonify({"success": True, "id": nid}), 201

@notification_bp.route('/notifications/<id>/read', methods=['PUT'])
def mark_notification_read(id):
    query = "UPDATE notifications SET is_read = TRUE WHERE id = %s"
    result = execute_query(query, (id,))
    
    if result is not None:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"message": "Error al actualizar notificación"}), 500
