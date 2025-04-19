from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///marketplace.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'buyer' or 'seller'
    specialty = db.Column(db.String(150))
    field = db.Column(db.String(150))
    documents = db.Column(db.Text)  # Comma-separated paths

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    subject = db.Column(db.String(100))
    price = db.Column(db.Float)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    rating = db.Column(db.Integer)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        specialty = request.form.get('specialty')
        field = request.form.get('field')

        user = User(username=username, password=password, role=role, specialty=specialty, field=field)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])
    if user.role == 'seller':
        offers = Offer.query.filter_by(seller_id=user.id).all()
        return render_template('seller_dashboard.html', user=user, offers=offers)
    else:
        offers = Offer.query.all()
        return render_template('buyer_dashboard.html', offers=offers)

@app.route('/offer/create', methods=['GET', 'POST'])
def create_offer():
    if request.method == 'POST':
        offer = Offer(
            seller_id=session['user_id'],
            title=request.form['title'],
            description=request.form['description'],
            subject=request.form['subject'],
            price=request.form['price']
        )
        db.session.add(offer)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_offer.html')


@app.route('/review/<int:seller_id>', methods=['POST'])
def leave_review(seller_id):
    review = Review(
        seller_id=seller_id,
        buyer_id=session['user_id'],
        content=request.form['content'],
        rating=int(request.form['rating'])
    )
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/upload_documents', methods=['POST'])
def upload_documents():
    user = User.query.get(session['user_id'])
    files = request.files.getlist('documents')
    filenames = []
    for f in files:
        path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
        f.save(path)
        filenames.append(path)
    user.documents = ','.join(filenames)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Dummy payment handler
@app.route('/pay/<int:offer_id>', methods=['POST'])
def pay(offer_id):
    offer = Offer.query.get(offer_id)
    commission_rate = 0.1
    seller_payment = offer.price * (1 - commission_rate)
    # Logic to transfer funds would go here
    return f"Paid {offer.price} to seller. Commission taken: {offer.price - seller_payment}"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)