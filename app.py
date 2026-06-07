from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import anthropic
import cloudinary
import cloudinary.uploader

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = Flask(__name__)


# DATABASE configuration

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///withme.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = "static/uploads/"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# DATABASE model

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    photo_filename = db.Column(db.String(300), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    is_urgent = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Post {self.title}>"


# Create the DATABASE tables

with app.app_context():
    db.create_all()

# HELPERs because we only want actual images rather than random files like .exe or .py files

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_ai_summary(title, description, category):
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": f"""Someone has posted a need on WithMe, a community help platform.

Category: {category}
Title: {title}
Their story: {description}

Write a single compassionate sentence that clearly summarises what this person needs.
Be warm, human, and specific. Do not start with 'This person' — speak about them with dignity.
Maximum 30 words."""
                }
            ]

        )

        return message.content[0].text

# exception handling for AI summary generation to ensure the app doesn't crash if the API call fails cause of slow internet or returns an error otherwise the post nevr gets posted
    except Exception as e:
        print(f"AI summary error: {e}")
        return None


# Routes

@app.route("/")
def home():
    posts = Post.query.order_by(
        Post.is_urgent.desc(),
        Post.date_posted.desc()).all()

    return render_template("index.html", posts=posts)


@app.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")
        is_urgent = request.form.get("is_urgent") == "true"

        # Handle photo upload to Cloudinary and get the secure URL to save in the DATABASE, with error handling to ensure the app doesn't crash if the upload fails, and instead just saves the post without a photo

        photo_filename = None
        photo = request.files.get("photo")

        if photo and photo.filename != "" and allowed_file(photo.filename):
            try:
                result = cloudinary.uploader.upload(photo)
                photo_filename = result["secure_url"]
            except Exception as e:
                print(f"Cloudinary upload error: {e}")
                photo_filename = None

        # SAVE post to DATABASE with AI summary
        ai_summary = generate_ai_summary(title, description, category)
        post = Post(
            title=title,
            description=description,
            category=category,
            photo_filename=photo_filename,
            ai_summary=ai_summary,
            user_id=current_user.id,
            is_urgent=is_urgent
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("post.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please log in.")
            return redirect(url_for("login"))

        # Create new user with hashed password

        hashed_password = generate_password_hash(password)
        user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/setup-db")
def setup_db():
    with db.engine.connect() as conn:
        conn.execute("db.text(
            "ALTER TABLE post ADD COLUMN IF NOT EXISTS is_urgent BOOLEAN DEFAULT FALSE"
        ))
        conn.commit()
        return "is_urgent column added!"


# start the Flask application
if __name__ == "__main__":
    app.run(debug=True)
