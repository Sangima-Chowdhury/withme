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
from better_profanity import profanity
import resend
import secrets


load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

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
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(200), nullable=True)
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
    location = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Post {self.title}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey(
        "comment.id"), nullable=True)
    replies = db.relationship("Comment", backref=db.backref(
        "parent", remote_side=[id]), lazy="dynamic")
    author = db.relationship("User", backref="comments")


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", backref="conversation", lazy=True)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey(
        "conversation.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship("User", foreign_keys=[sender_id])


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

    # Helper function for email verification


def send_verification_email(user):
    verify_url = url_for(
        "verify_email", token=user.verification_token, _external=True)
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": user.email,
            "subject": "Verify your WithMe account",
            "html": f"""
                <div style="font-family:sans-serif; max-width:480px; margin:0 auto;">
                    <h2 style="color: #FF6B6B;">Welcome to WithMe! 🧡</h2>
                    <p>Thanks for signing up. Please verify your email to activate your account.</p>
                    <a href="{verify_url}" style="display:inline-block; background:#FF6B6B; color:white; padding:12px 24px; border-radius:100px; text-decoration:none; font-weight:bold; margin:16px 0;">Verify My Account</a>
                    <p style="color:#888; font-size:13px;">If you didn't sign up for WithMe, you can ignore this email.</p>
                </div>
            """
        })

    except Exception as e:
        print(f"Email send error: {e}")


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
        location = request.form.get("location")

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
            is_urgent=is_urgent,
            location=location
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

        # Create new user with hashed password and verification token

        hashed_password = generate_password_hash(password)
        token = secrets.token_urlsafe(32)
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            verification_token=token
        )
        db.session.add(user)
        db.session.commit()

# Send verification email
        send_verification_email(user)

        flash("Account created! Please check your email to verify your account before logging in.")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/verify/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        flash("Oops! That link has expired or already been used.")
        return redirect(url_for("login"))

    # Mark as verified and clear the token
    user.is_verified = True
    user.verification_token = None
    db.session.commit()

    flash("✅ Your account has been verified! You can now log in.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        # Block Un-verified users(they must verify email & then login)

        if not user.is_verified:
            flash("Please verify your email before logging in. Check your inbox!")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter(
        Comment.post_id == post_id, Comment.parent_id == None
    ).order_by(Comment.timestamp.asc()).all()
    return render_template("post_detail.html", post=post, comments=comments)


@app.route("/post/<int:post_id>/comment", methods=["POST"])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get("body")

    if body:
        comment = Comment(body=body, user_id=current_user.id,
                          post_id=post_id, parent_id=None)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/post/<int:post_id>/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def add_reply(post_id, comment_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get("body")
    if body:
        reply = Comment(body=body, user_id=current_user.id,
                        post_id=post_id, parent_id=comment_id)
        db.session.add(reply)
        db.session.commit()
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/message/<int:user_id>")
@login_required
def start_conversation(user_id):
    if user_id == current_user.id:
        return redirect(url_for("home"))

    # Check if conversation already exists
    conversation = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == user_id)) |
        ((Conversation.user1_id == user_id) &
         (Conversation.user2_id == current_user.id))
    ).first()

    # If not, create a new conversation
    if not conversation:
        conversation = Conversation(user1_id=current_user.id, user2_id=user_id)
        db.session.add(conversation)
        db.session.commit()

    return redirect(url_for("conversation_detail", conversation_id=conversation.id))


@app.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@login_required
def conversation_detail(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)

    # Security - only the two people in the conversation can see it
    if current_user.id not in [conversation.user1_id, conversation.user2_id]:
        return redirect(url_for("home"))

    if request.method == "POST":
        body = request.form.get("body")
        if body:
            if profanity.contains_profanity(body):
                flash(
                    "⚠️ Your message contains inappropriate language and was not sent.")
            else:
                message = Message(
                    conversation_id=conversation_id,
                    sender_id=current_user.id,
                    body=body
                )
                db.session.add(message)
                db.session.commit()

    messages = Message.query.filter_by(
        conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    other_id = conversation.user2_id if conversation.user1_id == current_user.id else conversation.user1_id
    other_user = User.query.get(other_id)
    return render_template("conversation.html", conversation=conversation,
                           messages=messages, other_user=other_user)


@app.route("/inbox")
@login_required
def inbox():
    conversations = Conversation.query.filter(
        (Conversation.user1_id == current_user.id) |
        (Conversation.user2_id == current_user.id)
    ).order_by(Conversation.created_at.desc()).all()

    # Get the other user for each convo and the latest message

    conv_data = []
    for convo in conversations:
        other_id = convo.user2_id if convo.user1_id == current_user.id else convo.user1_id
        other = User.query.get(other_id)
        conv_data.append({"convo": convo, "other": other})

    return render_template("inbox.html", conv_data=conv_data)


@app.route("/setup-db-verify")
def setup_db_verify():
    try:
        from sqlalchemy import text
        db.session.execute(text(
            "ALTER TABLE \"user\" ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL"))
        db.session.execute(
            text("ALTER TABLE \"user\" ADD COLUMN verification_token VARCHAR(200"))
        db.session.commit()
        return "✅ Columns added successfully!"

    except Exception as e:
        return f"Error: {e}"


# start the Flask application
if __name__ == "__main__":
    app.run(debug=True)
