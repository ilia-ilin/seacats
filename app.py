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

@app.route('/message')
def message():
    return render_template('message.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
