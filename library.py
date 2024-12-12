from flask import Flask, request,Response,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import csv
from io import StringIO


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost/library_db'
#256 bit key as secret key
app.config['JWT_SECRET_KEY'] = '8566e73b2d7601def0d3d0573b7d10ae6d31c16ad9e24fb3e5ffcc35ec4b2628'

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_librarian = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    copies = db.Column(db.Integer, default=1)

class BorrowRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    date_from = db.Column(db.Date, nullable=False)
    date_to = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BorrowHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=False)

#Do ensure you run below line if your running first time
##db.create_all()

# Authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Invalid input'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    access_token = create_access_token(identity={'id': user.id, 'is_librarian': user.is_librarian}, expires_delta=timedelta(hours=1))
    return jsonify({'access_token': access_token}), 200


# Librarian APIs
@app.route('/librarian/create_user', methods=['POST'])
@jwt_required()
def create_user():
    current_user = get_jwt_identity()
    if not current_user['is_librarian']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Invalid input'}), 400
    hashed_password = generate_password_hash(data['password'])
    user = User(email=data['email'], password=hashed_password, is_librarian=data.get('is_librarian', False))

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":"Database error occurred :" + str(e)}), 500
    
    return jsonify({'message': 'User created successfully'})


@app.route('/librarian/view_requests', methods=['GET'])
@jwt_required()
def view_requests():
    current_user = get_jwt_identity()
    if not current_user['is_librarian']:
        return jsonify({'error': 'Unauthorized'}), 403
    requests = BorrowRequest.query.all()
    return jsonify([{
        'id': r.id, 'user_id': r.user_id, 'book_id': r.book_id, 
        'date_from': r.date_from, 'date_to': r.date_to, 'status': r.status
    } for r in requests])


@app.route('/librarian/update_request/<int:request_id>', methods=['PATCH'])
@jwt_required()
def update_request(request_id):
    current_user = get_jwt_identity()
    if not current_user['is_librarian']:
        return jsonify({'error': 'Unauthorized'}), 403
    request_data = BorrowRequest.query.get(request_id)
    if not request_data:
        return jsonify({'error': 'Request not found'}), 404
    status = request.json.get('status')
    if status not in ['Approved', 'Denied']:
        return jsonify({'error': 'Invalid status'}), 400
    request_data.status = status

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred: ' + str(e)}), 500
    return jsonify({'message': 'Request updated successfully'})

# Library User APIs
@app.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    books = Book.query.all()
    return jsonify([{
        'id': b.id, 'title': b.title, 'author': b.author, 'isbn': b.isbn, 'copies': b.copies
    } for b in books])


@app.route('/borrow', methods=['POST'])
@jwt_required()
def borrow_book():
    current_user = get_jwt_identity()
    data = request.json

    try:
        date_from = datetime.strptime(data['date_from'], '%Y-%m-%d').date()
        date_to = datetime.strptime(data['date_to'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if date_from > date_to:
        return jsonify({'error': 'Invalid date range'}), 400
    
#availability
    book = Book.query.get(data.get('book_id'))
    if not book or book.copies < 1:
        return jsonify({'error': 'Book unavailable'}), 400
    
#overlapping requests
    overlapping = BorrowRequest.query.filter(
        BorrowRequest.book_id == book.id,
        BorrowRequest.status == 'Approved',
        ((BorrowRequest.date_from <= date_from) & (BorrowRequest.date_to >= date_from) |
        (BorrowRequest.date_from <= date_to) & (BorrowRequest.date_to >= date_to))
    ).first()
    if overlapping:
        return jsonify({'error': 'Book already borrowed for given dates'}), 400
    
#submit borrow request
    borrow_request = BorrowRequest(
        user_id=current_user['id'], book_id=book.id,
        date_from=date_from, date_to=date_to
    )
    try:
        db.session.add(borrow_request)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":"Database error occurred :" + str(e)}), 500
    return jsonify({'message': 'Borrow request submitted'})

@app.route('/user/history', methods=['GET'])
@jwt_required()
def user_history():
    current_user = get_jwt_identity()
    history = BorrowHistory.query.filter_by(user_id=current_user['id']).all()
    return jsonify([{
        'id': h.id, 'book_id': h.book_id,
        'borrow_date': h.borrow_date, 'return_date': h.return_date
    } for h in history])

@app.route('/user/history/download', methods=['GET'])
@jwt_required()
def download_user_history():
    current_user = get_jwt_identity()
    history = BorrowHistory.query.filter_by(user_id=current_user['id']).all()

    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(['History ID', 'Book ID', 'Borrow Date', 'Return Date']) #header
    for h in history:
        writer.writerow([h.id, h.book_id, h.borrow_date, h.return_date]) #row

    csv_data.seek(0)  # Rewind the in-memory file

    # Create a response with CSV mime type
    return Response(
        csv_data.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=borrow_history.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
