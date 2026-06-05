from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

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


# DATABASE model

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    photo_filename = db.Column(db.String(300), nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

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
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/post/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        category = request.form.get("category")

        # Handle photo upload

        photo_filename = None
        photo = request.files.get("photo")

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            photo_filename = filename

        # SAVE post to DATABASE with AI summary
        ai_summary = generate_ai_summary(title, description, category)
        post = Post(
            title=title,
            description=description,
            category=category,
            photo_filename=photo_filename,
            ai_summary=ai_summary
        )

        db.session.add(post)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("post.html")


# start the Flask application
if __name__ == "__main__":
    app.run(debug=True)
