from app import db, Category, Subcategory, app

# Конфигурация категорий и подкатегорий
CATEGORIES = {
    'Математика': ['Алгебра', 'Геометрия', 'Матанализ'],
    'Программирование': ['Python', 'Web-разработка', 'Базы данных'],
    'Иностранные языки': ['Английский', 'Немецкий', 'Французский'],
    'Другие предметы': ['Физика', 'Химия', 'История']
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

# Запуск скрипта
if __name__ == '__main__':
    with app.app_context():
        populate_categories()
