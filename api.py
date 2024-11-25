from flask import Flask, request, jsonify
from database import Session, Appointment, Client
from sqlalchemy.exc import IntegrityError
from datetime import datetime

app = Flask(__name__)

@app.route('/appointments', methods=['GET'])
def get_appointments():
    session = Session()
    appointments = session.query(Appointment).all()
    session.close()
    return jsonify([{
        'id': appt.id,
        'date': appt.date.strftime('%Y-%m-%d'),
        'time': appt.time.strftime('%H:%M'),
        'client_id': appt.client_id,
        'status': appt.status,
        'price': appt.price,
        'confirmed': appt.confirmed,
        'comment': appt.appoint_comment
    } for appt in appointments])

@app.route('/appointments/<int:appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    session = Session()
    appointment = session.query(Appointment).get(appointment_id)
    session.close()
    if appointment:
        return jsonify({
            'id': appointment.id,
            'date': appointment.date.strftime('%Y-%m-%d'),
            'time': appointment.time.strftime('%H:%M'),
            'client_id': appointment.client_id,
            'status': appointment.status,
            'price': appointment.price,
            'confirmed': appointment.confirmed,
            'comment': appointment.appoint_comment
        })
    return jsonify({'error': 'Appointment not found'}), 404

@app.route('/appointments', methods=['POST'])
def create_appointment():
    data = request.json
    session = Session()
    new_appointment = Appointment(
        date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
        time=datetime.strptime(data['time'], '%H:%M').time(),
        client_id=data['client_id'],
        status=data['status'],
        price=data['price'],
        confirmed=data['confirmed'],
        appoint_comment=data['comment']
    )
    session.add(new_appointment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        return jsonify({'error': 'Integrity error'}), 400
    finally:
        session.close()
    return jsonify({'message': 'Appointment created successfully'}), 201

@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
def update_appointment(appointment_id):
    data = request.json
    session = Session()
    appointment = session.query(Appointment).get(appointment_id)
    if not appointment:
        session.close()
        return jsonify({'error': 'Appointment not found'}), 404

    appointment.date = data['date']
    appointment.time = data['time']
    appointment.client_id = data['client_id']
    appointment.status = data['status']
    appointment.price = data['price']
    appointment.confirmed = data['confirmed']
    appointment.appoint_comment = data['comment']
    
    session.commit()
    session.close()
    return jsonify({'message': 'Appointment updated successfully'})

@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
def delete_appointment(appointment_id):
    session = Session()
    appointment = session.query(Appointment).get(appointment_id)
    if not appointment:
        session.close()
        return jsonify({'error': 'Appointment not found'}), 404

    session.delete(appointment)
    session.commit()
    session.close()
    return jsonify({'message': 'Appointment deleted successfully'})

@app.route('/clients', methods=['GET'])
def get_clients():
    session = Session()
    clients = session.query(Client).all()
    session.close()
    return jsonify([{
        'id': client.id,
        'lastname': client.lastname,
        'name': client.name,
        'address': client.address,
        'phone': client.phone,
        'dog_name': client.dog_name,
        'breed': client.breed,
        'comments': client.comments
    } for client in clients])

if __name__ == '__main__':
    app.run(debug=True)
