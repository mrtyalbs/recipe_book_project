from flask import Flask, render_template, redirect, request, flash, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy.orm import relationship
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.jinja_env.globals.update(random=random)

bootstrap = Bootstrap5(app)

db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///..
/project/recipedatabase.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)


class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    prep_time = db.Column(db.Integer)
    cook_time = db.Column(db.Integer)
    img = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, nullable=False)
    ingredients = relationship(
        'Ingredient', back_populates='recipe')


class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'))
    recipe = relationship('Recipe', back_populates='ingredients')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    recipes = Recipe.query.all()
    random_recipe = random.choice(recipes)
    comments = Comment.query.all()
    comments_list = [{"id": comment.id, "comment": comment.comment} for comment in comments]
    return render_template('index.html', recipe=random_recipe, comments=comments_list)


@app.route('/comment', methods=['GET', 'POST'])
def comment():
    comment = request.form.get('comment')
    if not comment == None:
        new_comment = Comment(comment=comment)
        db.session.add(new_comment)
        db.session.commit()
        return render_template('comment.html', comment=new_comment)
    return render_template('comment.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form.get('email')).first() or User.query.filter_by(username=request.form.get('user-name')).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('register'))

        hash_and_salted_password = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256',
                                                          salt_length=8)

        new_user = User(username=request.form.get(
            'user-name'), email=request.form.get('email'), password=hash_and_salted_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html', current_user=current_user)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/add-recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        recipe_name = request.form.get('name')
        prep_time = request.form.get('prep_time')
        cook_time = request.form.get('cook_time')
        instructions = request.form.get('instructions')
        img = request.form.get('img')
        category = request.form.get('category')
        ingredients_text = request.form.get('ingredients')
        ingredients_list = ingredients_text.split(",")
        ingredients = []

        for ingredient in ingredients_list:
            ingredient_name = ingredient.strip()
            ingredient_ = Ingredient(name=ingredient_name)
            ingredients.append(ingredient_)

        recipe = Recipe(
            name=recipe_name,
            prep_time=prep_time,
            cook_time=cook_time,
            instructions=instructions,
            img=img,
            ingredients=ingredients,
            category=category
        )

        db.session.add(recipe)
        db.session.commit()

        return redirect(url_for('add_recipe'))

    return render_template('add_recipe.html')


@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    recipes = Recipe.query.all()
    return render_template('recipes.html', recipes=recipes)


@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe(recipe_id):
    recipe = Recipe.query.filter_by(id=recipe_id).first()
    return render_template('recipe.html', recipe=recipe)


if __name__ == '__main__':
    app.run(debug=True)
