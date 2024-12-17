from flask import Flask, request, jsonify
from flask_restful import Api, Resource, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

# === Ініціалізація додатка ===
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# === Компоненти ===
api = Api(app)
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# === Моделі БД ===
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(50), nullable=False)

# === Схема відповіді ===
item_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'price': fields.Float,
    'size': fields.String,
    'weight': fields.Float,
    'color': fields.String
}

# === Аутентифікація ===
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user

def create_default_admin():
    """Створює адміністратора за замовчуванням."""
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('password'))
        db.session.add(admin)
        db.session.commit()
        print("Створено користувача: admin, пароль: password")
    else:
        print("Користувач 'admin' вже існує.")

# === Утиліти ===
def validate_fields(data, required_fields):
    """Перевірка наявності обов'язкових полів у запиті."""
    missing = [field for field in required_fields if field not in data]
    if missing:
        return {'message': f"Пропущені поля: {', '.join(missing)}"}, 400
    return None

# === Ресурси ===
class ItemList(Resource):
    @marshal_with(item_fields)
    def get(self):
        """Отримати список усіх товарів."""
        return Item.query.all(), 200

    @auth.login_required
    def post(self):
        """Створити новий товар."""
        data = request.get_json()
        error = validate_fields(data, ['name', 'price', 'size', 'weight', 'color'])
        if error:
            return error
        new_item = Item(**data)
        db.session.add(new_item)
        db.session.commit()
        return {'message': 'Товар створено', 'id': new_item.id}, 201

class ItemResource(Resource):
    @marshal_with(item_fields)
    def get(self, id):
        """Отримати конкретний товар за ID."""
        item = Item.query.get_or_404(id)
        return item, 200

    @auth.login_required
    def put(self, id):
        """Оновити товар за ID."""
        item = Item.query.get_or_404(id)
        data = request.get_json()
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        db.session.commit()
        return {'message': 'Товар оновлено'}, 200

    @auth.login_required
    def delete(self, id):
        """Видалити товар за ID."""
        item = Item.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return {'message': 'Товар видалено'}, 200

# === Маршрути ===
api.add_resource(ItemList, '/items')
api.add_resource(ItemResource, '/items/<int:id>')

# === Запуск додатка ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(debug=True)
