from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager

# Инициализация приложения Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_help.db'

# Инициализация базы данных
db = SQLAlchemy(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Функция user_loader для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Модели базы данных

class User(db.Model, UserMixin):
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
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'), nullable=False)  # Связь с предложением

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    offer = db.relationship('Offer', backref='messages')


class Review(db.Model):
    """Модель отзыва."""
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # Рейтинг от 1 до 5
    text = db.Column(db.Text, nullable=False)  # Текст отзыва
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Продавец
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Автор отзыва

    user = db.relationship('User', foreign_keys=[user_id], backref='reviews_received')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')


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

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Имя пользователя уже занято, пожалуйста, выберите другое имя.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Пожалуйста, войдите в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход пользователя в систему."""
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)  # Логиним пользователя
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')  # Сообщение об ошибке
    return render_template('login.html')



@app.route('/logout')
def logout():
    """Выход пользователя из системы."""
    logout_user()  # Выход из системы
    return redirect(url_for('home'))


@app.route('/create_offer', methods=['GET', 'POST'])
def create_offer():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        subcategory_name = request.form['subtopic']
        subcategory = Subcategory.query.filter_by(name=subcategory_name).first()

        offer = Offer(
            title=request.form['title'],
            description=request.form['description'],
            price=float(request.form['price']),
            subcategory_id=subcategory.id,
            seller_id=current_user.id
        )
        db.session.add(offer)
        db.session.commit()
        return redirect(url_for('profile'))

    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
        subcategories = Subcategory.query.filter_by(category_id=category.id).all()
        categories_dict[category.name] = [sub.name for sub in subcategories]

    return render_template('create_offer.html', categories=categories_dict)


@app.route('/tema/<string:subtopic>')
def show_subtopic(subtopic):
    category_name = get_category_for_subtopic(subtopic)
    subcategories = get_subcategories_with_counts(category_name)
    subcategory = Subcategory.query.filter_by(name=subtopic).first()

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


@app.route('/profile', defaults={'user_id': None}, methods=['GET', 'POST'])
@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    """Профиль пользователя и его предложения."""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if user_id is None:
        user = current_user
    else:
        user = User.query.get_or_404(user_id)

    offers = Offer.query.filter_by(seller_id=user.id).all()
    reviews = Review.query.filter_by(user_id=user.id).all()

    if request.method == 'POST' and user != current_user:
        rating = request.form['rating']
        text = request.form['text']

        # Создаем новый отзыв
        new_review = Review(rating=rating, text=text, user_id=user.id, reviewer_id=current_user.id)

        # Сохраняем в базе данных
        db.session.add(new_review)
        db.session.commit()

        flash('Отзыв успешно добавлен!', 'success')
        return redirect(url_for('profile', user_id=user.id))

    return render_template('profile.html', user=user, offers=offers, reviews=reviews)


@app.route('/review/<int:user_id>', methods=['GET', 'POST'])
def create_review(user_id):
    """Оставить отзыв о пользователе."""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user_to_review = User.query.get_or_404(user_id)

    if request.method == 'POST':
        rating = int(request.form['rating'])
        text = request.form['text']

        review = Review(rating=rating, text=text, user_id=user_to_review.id, reviewer_id=current_user.id)
        db.session.add(review)
        db.session.commit()

        flash('Отзыв оставлен успешно!', 'success')
        return redirect(url_for('profile', user_id=user_to_review.id))

    return render_template('create_review.html', user=user_to_review)

@app.route('/offer/<int:offer_id>', methods=['GET', 'POST'])
def offer(offer_id):
    """Просмотр конкретного предложения и чата с продавцом."""
    offer = Offer.query.get_or_404(offer_id)

    if request.method == 'POST':
        text = request.form['text']
        if not current_user.is_authenticated:
            flash("Пожалуйста, войдите для отправки сообщений.", "danger")
            return redirect(url_for('login'))

        receiver_id = offer.seller.id if current_user.id != offer.seller.id else offer.seller.id

        new_message = Message(sender_id=current_user.id, receiver_id=receiver_id, text=text, offer_id=offer.id)
        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('offer', offer_id=offer.id))

    # Проверка на авторизацию перед использованием current_user.id
    if current_user.is_authenticated:
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == offer.seller.id)) |
            ((Message.sender_id == offer.seller.id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp).all()
    else:
        messages = []  # Пустой список, если пользователь не авторизован

    return render_template('offer.html', offer=offer, messages=messages)



@app.route('/edit_offer/<int:offer_id>', methods=['GET', 'POST'])
def edit_offer(offer_id):
    offer = Offer.query.get_or_404(offer_id)
    if offer.seller_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        offer.title = request.form['title']
        offer.description = request.form['description']
        offer.price = float(request.form['price'])
        db.session.commit()
        flash('Предложение обновлено!', 'success')
        return redirect(url_for('offer', offer_id=offer.id))

    return render_template('edit_offer.html', offer=offer)

@app.route('/faq')
def faq():
    """Страница с вопросами и ответами."""
    return render_template('faq.html')


@app.route('/checkout/<int:offer_id>', methods=['GET', 'POST'])
def checkout(offer_id):
    offer = Offer.query.get_or_404(offer_id)

    if request.method == 'POST':
        flash('Покупка успешно оформлена!', 'success')
        return redirect(url_for('home'))  # или на страницу профиля

    return render_template('checkout.html', offer=offer)


@app.route('/message/<int:receiver_id>', methods=['GET', 'POST'])
def message(receiver_id):
    """Обработка сообщений между пользователями."""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    sender_id = current_user.id
    if sender_id == receiver_id:
        return redirect(url_for('profile'))

    receiver = User.query.get_or_404(receiver_id)

    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp).all()

    offer = Offer.query.filter_by(id=messages[0].offer_id).first() if messages else None

    if request.method == 'POST':
        message_text = request.form['text']

        if message_text:
            new_message = Message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                text=message_text,
                offer_id=offer.id if offer else None
            )
            db.session.add(new_message)
            db.session.commit()
            
            flash("Сообщение отправлено!", "success")
            return redirect(url_for('message', receiver_id=receiver_id))

    return render_template('message.html', messages=messages, receiver=receiver, offer=offer)



@app.route('/messages')
def messages():
    """Список всех диалогов текущего пользователя."""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user_id = current_user.id

    partner_ids = db.session.query(
        Message.sender_id, Message.receiver_id
    ).filter(
        (Message.sender_id == user_id) | (Message.receiver_id == user_id)
    ).all()

    partners = set()
    for partner_id1, partner_id2 in partner_ids:
        partners.add(partner_id1)
        partners.add(partner_id2)

    partners.discard(user_id)
    partner_users = User.query.filter(User.id.in_(partners)).all()

    return render_template('messages.html', partners=partner_users)

@app.route('/search', methods=['GET'])
def search_offers():
    query = request.args.get('query')
    if query:
        offers = Offer.query.filter(Offer.title.ilike(f'%{query}%')).all()
    else:
        offers = []

    return render_template('search_results.html', offers=offers, query=query)





if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)