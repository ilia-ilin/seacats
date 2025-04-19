from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship, declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_help.db'
db = SQLAlchemy(app)

class User(db):
    user_id = Column(Integer, primary_key=True)
    login = Column(String)
    password = Column(String)
    email = Column(String)

    profiles = relationship("Profile", back_populates="user")
    reviews_left = relationship("Review", back_populates="author", foreign_keys='Review.user_id')
    offers = relationship("Offer", back_populates="user")
    chats = relationship("Chat", back_populates="user")


class Profile(db):
    profile_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    rate = Column(Float)
    text = Column(Text)
    photo = Column(String)

    user = relationship("User", back_populates="profiles")
    reviews_received = relationship("Review", back_populates="profile")
    chats = relationship("Chat", back_populates="profile")


class Review(db):
    review_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.user_id'))  # кто оставил
    profile_id = Column(Integer, ForeignKey('profile.profile_id'))  # где
    rate = Column(Float)
    text = Column(Text)

    author = relationship("User", back_populates="reviews_left")
    profile = relationship("Profile", back_populates="reviews_received")


class Chapter(db):
    chapter_id = Column(Integer, primary_key=True)
    name = Column(String)
    text = Column(Text)

    topics = relationship("Topic", back_populates="chapter")


class Topic(db):
    topic_id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapter.chapter_id'))
    text = Column(Text)

    chapter = relationship("Chapter", back_populates="topics")
    offers = relationship("Offer", back_populates="topic")


class Offer(db):
    offer_id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topic.topic_id'))
    user_id = Column(Integer, ForeignKey('user.user_id'))
    text = Column(Text)
    price = Column(Float)

    topic = relationship("Topic", back_populates="offers")
    user = relationship("User", back_populates="offers")
    chats = relationship("Chat", back_populates="offer")


class Chat(db):
    chat_id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey('profile.profile_id'))  # с кем
    user_id = Column(Integer, ForeignKey('user.user_id'))  # кто
    offer_id = Column(Integer, ForeignKey('offer.offer_id'))

    profile = relationship("Profile", back_populates="chats")
    user = relationship("User", back_populates="chats")
    offer = relationship("Offer", back_populates="chats")
    messages = relationship("Message", back_populates="chat")


class Message(db):
    message_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chat.chat_id'))
    text = Column(Text)
    time = Column(DateTime)

    chat = relationship("Chat", back_populates="messages")

class Payment(db):
    id = Column(Integer, primary_key=True)
    pay_method = Column(String)
    price = Column(String)

@app.route('/')
def home():
    offers = Offer.query.all()
    return render_template('index.html', offers=offers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        user = User(username=username, password=password, role=role)
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
            session['role'] = user.role
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/create_offer', methods=['GET', 'POST'])
def create_offer():
    if 'user_id' not in session or session.get('role') != 'seller':
        return redirect(url_for('login'))
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

@app.route('/offer/<int:offer_id>')
def offer_detail(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    return render_template('offer_detail.html', offer=offer)


@app.route('/faq')
def faq():
    return "FAQ"

@app.route('/messenger')
def messenger():
    return "Messenger"

@app.route('/profile')
def profile():
    return "Profile"

@app.route('/chapter')
def profile():
    return "Chapter"

@app.route('/buy')
def profile():
    return "Buy"

@app.route('/Seller_profile')
def profile():
    return "Seller_profile"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
