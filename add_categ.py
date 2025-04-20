from app import app, db, Category, Subcategory, User, Offer
from werkzeug.security import generate_password_hash

# Конфигурация категорий и подкатегорий
CATEGORIES = {
    'Математика': ['Алгебра', 'Геометрия', 'Матанализ', 'Теория вероятностей', 'Дифференциальные уравнения'],
    'Программирование': ['Python', 'Web-разработка', 'Базы данных', 'Java', 'C++', 'Алгоритмы и структуры данных'],
    'Иностранные языки': ['Английский', 'Немецкий', 'Французский', 'Испанский', 'Китайский'],
    'Физика': ['Классическая механика', 'Электродинамика', 'Квантовая физика', 'Термодинамика'],
    'Химия': ['Органическая химия', 'Неорганическая химия', 'Физическая химия', 'Аналитическая химия'],
    'Биология': ['Зоология', 'Ботаника', 'Генетика', 'Экология', 'Микробиология'],
    'История': ['Мировая история', 'История России', 'Археология', 'Антропология'],
    'География': ['Физическая география', 'Экономическая география', 'Геоинформатика', 'Геология'],
    'Искусство': ['Изобразительное искусство', 'Музыка', 'Театр', 'Кино', 'Литература'],
    'Психология': ['Общая психология', 'Социальная психология', 'Клиническая психология', 'Психология личности'],
    'Философия': ['Общая философия', 'Социальная философия', 'Клиническая философия', 'Психология философия'],
    'Другие категории': ['иное']
}

# Функция для добавления категорий и подкатегорий в базу данных
def populate_categories():
    for category_name, subtopics in CATEGORIES.items():
        # Добавляем категорию
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()

        # Добавляем подкатегории
        for subtopic_name in subtopics:
            subcategory = Subcategory.query.filter_by(name=subtopic_name).first()
            if not subcategory:
                subcategory = Subcategory(name=subtopic_name, category_id=category.id)
                db.session.add(subcategory)

    db.session.commit()
    print("Категории и подкатегории успешно добавлены в базу данных!")

# Функция для добавления пользователя и предложений
def add_test_user_and_offers():
    # Добавляем пользователя test с паролем test
    user = User.query.filter_by(username='test').first()
    if not user:
        user = User(username='test', password=generate_password_hash('test'))
        db.session.add(user)
        db.session.commit()

    # Добавляем по 5 предложений в каждую категорию
    for category_name, subtopics in CATEGORIES.items():
        for subtopic_name in subtopics:
            subcategory = Subcategory.query.filter_by(name=subtopic_name).first()
            if subcategory:
                # Создаем 5 предложений для каждой подкатегории
                for i in range(5):
                    offer = Offer(
                        title=f"Предложение {i+1} в категории {category_name} - {subtopic_name}",
                        description=f"Описание предложения {i+1} для подкатегории {subtopic_name}.",
                        price=100 + i*10,  # Цена увеличивается с каждым предложением
                        subcategory_id=subcategory.id,
                        seller_id=user.id
                    )
                    db.session.add(offer)

    db.session.commit()
    print("Пользователь и предложения успешно добавлены!")

# Запуск скрипта
if __name__ == '__main__':
    with app.app_context():
        populate_categories()  # Сначала заполняем категории и подкатегории
        add_test_user_and_offers()  # Добавляем пользователя и предложения
