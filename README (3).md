# WithMe 🧡

**Post a need. Help someone. No middleman.**

WithMe is a community needs platform that connects people who need help directly with people who want to give it — no fees, no intermediaries, no barriers. Whether someone needs food, medicine, shelter, or educational support, they can post their need and a member of the community can step in to help directly.

🔗 **Live app:** [withme-034l.onrender.com](https://withme-034l.onrender.com)

> ⏳ *Note: the app is hosted on Render's free tier, so the first visit after a period of inactivity may take 30–50 seconds to wake up. Subsequent loads are fast.*

---

## 💡 Why I Built This

I grew up in a Bangladeshi family where giving back was simply part of life. Sending money home to support people facing poverty — helping with food, medicine, and the most basic everyday needs — was never an event; it was constant, and it was personal. Charity wasn't charity, it was responsibility. That spirit of helping directly, person to person, is the foundation of WithMe.

As I got older, I noticed how much harder that becomes at a distance. Around the world — across Bangladesh, Palestine, Sudan, Yemen, and so many other places — people are starving and in desperate need, and well-meaning donors want to help. But so often the help flows through fundraising platforms that take their cut, and it's genuinely hard to know how much of a donation ever reaches the person who needed it. The middleman makes giving feel uncertain, and that uncertainty stops people from giving at all.

WithMe is my answer to that. I wanted to build a platform where helping someone is direct and human — where a person in need and a person willing to help can find each other without a company standing in the way or taking a slice. Help isn't always about money, either; it can be a bag of groceries, hygiene essentials, medication, or simply showing up. WithMe is built to make that connection as simple, safe, and dignified as possible.

My background also shapes how I build. Before moving into software engineering, I worked as a Special Educational Needs Teaching Assistant, supporting children who needed extra care to thrive. That taught me to see technology not as something impressive for its own sake, but as something that should make people's lives genuinely better.

This project is also where I taught myself full-stack development — every feature here was built from the ground up, debugged line by line, and shipped to production.

---

## ✨ Features

### 📝 Posting & Discovery
- Create posts describing a need, with category (Food, Medical, Shelter, Education), location, and an optional photo
- AI-generated compassionate summaries of each need, powered by Anthropic's Claude
- Urgency flags to highlight time-sensitive needs, which surface to the top of the feed
- Photo uploads handled via Cloudinary

### 💬 Community Interaction
- Nested comments and replies on every post (threaded, Reddit-style), built with a self-referential model and a recursive template macro
- Internal direct messaging system, Instagram-style, so members can coordinate help privately
- Automatic profanity filtering on messages to keep conversations safe
- Safety banners reminding users never to share sensitive personal or financial information

### 🔐 Accounts & Security
- Secure registration with hashed passwords
- Email verification via Resend — new accounts must confirm their email before logging in
- Password confirmation and strength validation (minimum length, number, and symbol required)
- Session management and protected routes via Flask-Login

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | PostgreSQL (production), SQLite (local) |
| ORM | SQLAlchemy |
| Templating | Jinja2 |
| Authentication | Flask-Login, Werkzeug password hashing |
| Email | Resend |
| Image hosting | Cloudinary |
| AI summaries | Anthropic Claude API |
| Content safety | better-profanity |
| Hosting | Render |

---

## ⚙️ How It Works

WithMe is a server-rendered Flask application. Posts, comments, messages, and users are stored in a PostgreSQL database and modelled with SQLAlchemy. When a user creates a post, the app calls Anthropic's Claude API to generate a short, warm summary of the need, and uploads any attached image to Cloudinary.

Registration sends a verification email through Resend containing a unique, securely generated token; the account stays inactive until the user clicks the link. Direct messages are grouped into conversations between two users and passed through a profanity filter before being saved.

---

## 💻 Running Locally

**1. Clone the repository**
```bash
git clone https://github.com/Sangima-Chowdhury/withme.git
cd withme
```

**2. Create and activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create a `.env` file** in the project root with your own keys:
```
SECRET_KEY=your-secret-key
ANTHROPIC_API_KEY=your-anthropic-key
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-key
CLOUDINARY_API_SECRET=your-cloudinary-secret
RESEND_API_KEY=your-resend-key
```

**5. Run the app**
```bash
python app.py
```
The app will be available at `http://127.0.0.1:5000`.

---

## 📚 What I Learned

Building WithMe took me from foundational Python through to a deployed, full-stack web application. Along the way I worked through self-referential database relationships, recursive templates, third-party API integration (AI, email, image hosting), production database migrations without shell access, and the security considerations that come with handling real user accounts and messages. Most importantly, I learned to make product decisions — choosing what *not* to build, and keeping the platform's purpose and users' safety at the centre of every feature.

---

## 🚀 Roadmap

Planned future improvements:
- Password reset / "forgot password" flow
- Custom domain to enable email delivery to all users in production
- User profiles and reputation
- Search and filtering by category and location

---

## 📸 Screenshots



<img width="1352" height="878" alt="Screenshot 2026-06-10 at 18 11 54" src="https://github.com/user-attachments/assets/a1d6dd33-e314-4794-871e-9f129396230c" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 20 09 35" src="https://github.com/user-attachments/assets/d8fd1d3f-0cac-4b11-b942-0b70d3b8c2e9" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 20 10 47" src="https://github.com/user-attachments/assets/2bf7949d-f818-46b7-8dcf-cddeff113f09" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 24 08" src="https://github.com/user-attachments/assets/e96a1332-e773-4a4a-9561-61b2d12a4545" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 06 49" src="https://github.com/user-attachments/assets/8a0f90f9-0193-4a7d-a07f-a451cdcc9395" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 10 56" src="https://github.com/user-attachments/assets/ec78676e-cb81-496a-8c79-51abef7aebec" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 12 25" src="https://github.com/user-attachments/assets/e32e8df4-9430-47bd-8fc2-9cee95520430" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 17 49" src="https://github.com/user-attachments/assets/f152e463-ad43-425d-a5b6-7026d6760a46" />

<img width="1352" height="878" alt="Screenshot 2026-06-10 at 23 18 15" src="https://github.com/user-attachments/assets/d2491fe1-2ecd-4ab1-a799-9483ca16c262" />

---

## 👩‍💻 Author

**Sangima Chowdhury**
Self-taught Python / AI developer based in East London, transitioning from Special Educational Needs support into software and AI engineering.

- GitHub: [github.com/Sangima-Chowdhury](https://github.com/Sangima-Chowdhury)
- LinkedIn: [linkedin.com/in/sangima-chowdhury](https://linkedin.com/in/sangima-chowdhury)
- Live project: [withme-034l.onrender.com](https://withme-034l.onrender.com)
