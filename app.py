import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Инициализация приложения Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_help.db'

# Инициализация базы данных
db = SQLAlchemy(app)

# Модели базы данных

class User(db.Model):
    """Модель пользователя."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    offers = db.relationship('Offer', backref='seller', lazy=True)  # связь с предложениями

class Category(db.Model):
    """Модель категории."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    subcategories = db.relationship('Subcategory', backref='category', lazy=True)

class Subcategory(db.Model):
    """Модель подкатегории."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

class Offer(db.Model):
    """Модель предложения."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Message(db.Model):
    """Модель сообщения."""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

# Вспомогательные функции
def get_subcategories_with_counts(category_name):
    """Возвращает подкатегории с количеством предложений"""
    category = Category.query.filter_by(name=category_name).first()
    subcategories = []
    if category:
        subcategories = [
            {
                'name': subcategory.name,
                'count': Offer.query.filter_by(subcategory_id=subcategory.id).count()
            }
            for subcategory in category.subcategories
        ]
    return subcategories

def get_category_for_subtopic(subtopic):
    """Возвращает категорию для подкатегории"""
    subcategory = Subcategory.query.filter_by(name=subtopic).first()
    if subcategory:
        return subcategory.category.name
    return 'Другие предметы'


# Маршруты и представления
@app.route('/')
def home():
    """Главная страница с категориями и подкатегориями."""
    categories = Category.query.all()
    # Формируем структуру данных для отображения категорий с подкатегориями
    category_data = [
        {
            'name': category.name,
            'subcategories': [
                {'name': subcategory.name, 'count': Offer.query.filter_by(subcategory_id=subcategory.id).count()}
                for subcategory in category.subcategories
            ]
        }
        for category in categories
    ]
    return render_template('index.html', categories=category_data)




@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
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
    """Вход пользователя в систему."""
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Выход пользователя из системы."""
    session.clear()
    return redirect(url_for('home'))


@app.route('/create_offer', methods=['GET', 'POST'])
def create_offer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        subcategory_name = request.form['subtopic']
        subcategory = Subcategory.query.filter_by(name=subcategory_name).first()

        offer = Offer(
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            subcategory_id=subcategory.id,
            seller_id=session['user_id']
        )
        db.session.add(offer)
        db.session.commit()
        return redirect(url_for('profile'))

    categories = Category.query.all()
    # Формируем структуру словаря категорий с подкатегориями
    categories_dict = {}
    for category in categories:
        subcategories = Subcategory.query.filter_by(category_id=category.id).all()
        categories_dict[category.name] = [sub.name for sub in subcategories]

    return render_template('create_offer.html', categories=categories_dict)


@app.route('/tema/<string:subtopic>')
def show_subtopic(subtopic):
    # Получаем имя категории для подкатегории
    category_name = get_category_for_subtopic(subtopic)

    # Получаем список подкатегорий с количеством предложений в каждой
    subcategories = get_subcategories_with_counts(category_name)

    # Получаем подкатегорию по имени
    subcategory = Subcategory.query.filter_by(name=subtopic).first()

    # Если подкатегория найдена, фильтруем предложения по subcategory_id
    if subcategory:
        offers = Offer.query.filter_by(subcategory_id=subcategory.id).order_by(Offer.id.desc()).all()
    else:
        offers = []

    return render_template(
        'tema.html',
        category_name=category_name,
        subtopic_name=subtopic,
        subcategories=subcategories,
        offers=offers
    )


@app.route('/profile')
def profile():
    """Профиль пользователя и его предложения."""
    user = User.query.get(session['user_id'])
    offers = Offer.query.filter_by(seller_id=session['user_id']).all()
    return render_template('profile.html', user=user, offers=offers)


@app.route('/offer/<int:offer_id>')
def offer(offer_id):
    """Просмотр конкретного предложения."""
    offer = Offer.query.get_or_404(offer_id)
    return render_template('offer.html', offer=offer)


@app.route('/faq')
def faq():
    """Страница с вопросами и ответами."""
    return render_template('faq.html')

@app.route('/checkout/<int:offer_id>', methods=['GET', 'POST'])
def checkout(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if request.method == 'POST':
        # тут логика оформления заказа
        # например: создать запись в таблице заказов, отправить уведомление и т.д.
        flash('Покупка успешно оформлена!', 'success')
        return redirect(url_for('index'))  # или на страницу профиля / чека

    return render_template('checkout.html', offer=offer)


@app.route('/message/<int:receiver_id>', methods=['GET', 'POST'])
def message(receiver_id):
    """Обработка сообщений между пользователями."""
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

@app.route('/messages')
def messages():
    """Список всех диалогов текущего пользователя."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Получаем уникальных собеседников
    partner_ids = db.session.query(
        Message.sender_id, Message.receiver_id
    ).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).all()

    # Извлекаем ID собеседников (кроме самого пользователя)
    unique_ids = set()
    for sender_id, receiver_id in partner_ids:
        if sender_id != user_id:
            unique_ids.add(sender_id)
        if receiver_id != user_id:
            unique_ids.add(receiver_id)

    partners = User.query.filter(User.id.in_(unique_ids)).all()

    return render_template('messages.html', partners=partners)

if __name__ == '__main__':
    # Создание таблиц в базе данных
    with app.app_context():
        db.create_all()
    app.run(debug=True)
