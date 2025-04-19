import sqlite3

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_help.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    offers = db.relationship('Offer', backref='seller', lazy=True)  # связь с предложениями

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

@app.route('/message/<int:receiver_id>', methods=['GET', 'POST'])
def message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    sender_id = session['user_id']
    if sender_id == receiver_id:
        return redirect(url_for('profile'))

    receiver = User.query.get_or_404(receiver_id)

    if request.method == 'POST':
        text = request.form['text']
        new_msg = Message(sender_id=sender_id, receiver_id=receiver_id, text=text)
        db.session.add(new_msg)
        db.session.commit()
        return redirect(url_for('message', receiver_id=receiver_id))

    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp).all()

    return render_template('message.html', messages=messages, receiver=receiver)


@app.route('/')
def home():
    offers = Offer.query.all()
    return render_template('index.html', offers=offers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
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
            session['username'] = user.username
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/create_offer', methods=['GET', 'POST'])
def create_offer():
    if request.method == 'POST':
        offer = Offer(
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            seller_id=session['user_id']
        )
        db.session.add(offer)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create_offer.html')

@app.route('/profile')
def profile():
    user = User.query.get(session['user_id'])
    offers = Offer.query.filter_by(seller_id=session['user_id']).all()
    return render_template('profile.html', user=user, offers=offers)

@app.route('/offer/<int:offer_id>')
def offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template('offer.html', offer=offer)

@app.route('/faq')
def faq():
    return render_template('faq.html')

def get_offers_by_tema(tema_number):
    conn = sqlite3.connect('offers.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM offers WHERE tema = ?", (tema_number,))
    offers = cursor.fetchall()
    conn.close()
    return offers

@app.route('/')
@app.route('/tema1')
def tema1():
    offers = get_offers_by_tema(1)
    return render_template('tema.html', tema_number=1, offers=offers)

@app.route('/tema2')
def tema2():
    offers = get_offers_by_tema(2)
    return render_template('tema.html', tema_number=2, offers=offers)

@app.route('/tema3')
def tema3():
    offers = get_offers_by_tema(3)
    return render_template('tema.html', tema_number=3, offers=offers)

@app.route('/tema4')
def tema4():
    offers = get_offers_by_tema(4)
    return render_template('tema.html', tema_number=4, offers=offers)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
