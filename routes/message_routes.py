from flask import Blueprint, request, jsonify
from database import execute_query
import uuid
from datetime import datetime

message_bp = Blueprint('message', __name__)

@message_bp.route('/messages/<reservation_id>', methods=['GET'])
def get_messages(reservation_id):
    query = "SELECT * FROM messages WHERE reservation_id = %s ORDER BY timestamp ASC"
    results = execute_query(query, (reservation_id,), fetch=True)
    
    return jsonify(results if results else []), 200

@message_bp.route('/messages', methods=['POST'])
def send_message():
    data = request.get_json()
    reservation_id = data.get('reservationId')
    room_number = data.get('roomNumber')
    content = data.get('content')
    sender = data.get('sender', 'guest')
    
    if not all([reservation_id, room_number, content]):
        return jsonify({"message": "Faltan datos requeridos"}), 400
    
    message_id = str(uuid.uuid4())
    query = """
        INSERT INTO messages (id, reservation_id, room_number, content, sender, is_read)
        VALUES (%s, %s, %s, %s, %s, FALSE)
    """
    params = (message_id, reservation_id, room_number, content, sender)
    
    result = execute_query(query, params)
    
    if result is not None:
        return jsonify({
            "success": True,
            "id": message_id,
            "timestamp": datetime.now().isoformat()
        }), 201
    else:
        return jsonify({"message": "Error al enviar el mensaje"}), 500
@message_bp.route('/messages/<id>/read', methods=['PUT'])
def mark_message_read(id):
    query = "UPDATE messages SET is_read = TRUE WHERE id = %s"
    result = execute_query(query, (id,))
    if result is not None:
        return jsonify({"success": True}), 200
    return jsonify({"message": "Error al actualizar mensaje"}), 500

@message_bp.route('/messages/reservation/<reservation_id>/read', methods=['PUT'])
def mark_all_messages_read(reservation_id):
    # Usually we want to mark messages as read when the OTHER side reads them.
    # But for simplicity, we'll mark all unread messages for this reservation as read.
    # A better approach might be to specify the sender to mark as read (e.g. mark all guest messages as read by staff).
    # For now, we'll mark everything as read.
    query = "UPDATE messages SET is_read = TRUE WHERE reservation_id = %s AND is_read = FALSE"
    result = execute_query(query, (reservation_id,))
    if result is not None:
        return jsonify({"success": True}), 200
    return jsonify({"message": "Error al actualizar mensajes"}), 500
@message_bp.route('/messages/room/<room_number>/read', methods=['PUT'])
def mark_room_messages_read(room_number):
    query = "UPDATE messages SET is_read = TRUE WHERE room_number = %s AND is_read = FALSE"
    result = execute_query(query, (room_number,))
    if result is not None:
        return jsonify({"success": True}), 200
    return jsonify({"message": "Error al actualizar mensajes"}), 500
