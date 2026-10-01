# 💼 TrackDesk

**Stop manually logging job applications. Just forward the email.**

TrackDesk is a job application tracker that updates itself. Set up an email filter once, and every application confirmation, interview invite, or rejection you receive gets automatically parsed by an LLM and turned into a tracked application — no manual data entry required.

🔗 **Live app:** [trackdesk.streamlit.app](https://trackdesk-mgsgo3jyc7clignd5lhatd.streamlit.app/)
🔗 **API:** [trackdesk-2v59.onrender.com](https://trackdesk-2v59.onrender.com)

---

## The problem this solves

Most job trackers fail for one simple reason: people stop updating them after the first week. Manually logging every application is friction, and friction kills habits.

TrackDesk removes that friction entirely. You set up an email forward once. After that, the tracker builds itself while you apply to jobs like normal.

---

## How it works

```
Job confirmation email arrives in Gmail
        │
        ▼
Gmail filter forwards it to your personal TrackDesk inbound address
        │
        ▼
Resend receives the email → sends a signed webhook to the backend
        │
        ▼
FastAPI verifies the webhook signature (HMAC, replay-protected)
        │
        ▼
Email body is cleaned (HTML stripped, quoted threads removed)
        │
        ▼
Gemini LLM extracts: company, role, status, confidence score
        │
        ▼
If confidence ≥ 0.7 → application is created or updated automatically
        │
        ▼
Shows up instantly in your dashboard
```

You can also add, edit, search, and filter applications manually at any time — the automation is additive, not required.

---

## Features

- 🔐 **Secure auth** — JWT-based sessions, Argon2 password hashing
- 📧 **Automatic application creation** from forwarded emails via LLM parsing
- ✅ **Signed webhook verification** — rejects any request not genuinely from Resend (HMAC + timestamp replay protection)
- 📊 **Dashboard** — totals, status breakdown, upcoming/overdue follow-ups
- 🔎 **Search & filter** by company, role, and status
- ✏️ **Full manual CRUD** — add, edit, delete applications anytime
- 🚦 **Per-user daily email limits** to prevent abuse of the LLM pipeline
- 🗄️ **Database migrations** via Alembic, versioned schema changes

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Frontend | Streamlit |
| Database | PostgreSQL (hosted on [Neon](https://neon.tech)) |
| ORM / Migrations | SQLAlchemy + Alembic |
| Auth | JWT (PyJWT) + Argon2 password hashing (pwdlib) |
| Email ingestion | [Resend](https://resend.com) inbound email + webhooks |
| Email parsing | Google Gemini (LLM) + BeautifulSoup (HTML cleaning) |
| Hosting | Render (API) + Streamlit Community Cloud (frontend) |

---

## Architecture decisions worth noting

- **Webhook signature verification** — every inbound email event is cryptographically verified (Svix-style HMAC) before touching the database or calling the LLM, preventing forged webhook requests from creating fake applications or burning API quota.
- **Confidence-gated automation** — the LLM returns a confidence score with every extraction. Applications are only auto-created above a 0.7 threshold, so ambiguous or malformed emails don't pollute the tracker with garbage data.
- **Environment-based configuration** — no credentials are hardcoded; database URL, API keys, and secrets are all read from environment variables, making local dev and production deploys use identical code paths.

---

## Running it locally

**1. Clone and install**
```bash
git clone https://github.com/suryaisinsane/TrackDesk.git
cd TrackDesk
pip install -r requirements.txt
```

**2. Set up environment variables**

Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql://user:password@host/dbname
JWT_SECRET_KEY=your-secret-key
RESEND_API_KEY=your-resend-key
RESEND_WEBHOOK_SECRET=whsec_your-webhook-secret
GEMINI_API_KEY=your-gemini-key
API_URL=http://127.0.0.1:8000
```

**3. Run migrations**
```bash
alembic upgrade head
```

**4. Start both services** (two terminals)
```bash
uvicorn main:app --reload
streamlit run app1.py
```

---

## Roadmap

- [ ] Persistent login across page reloads (currently session-based)
- [ ] Gmail OAuth integration (skip manual filter setup)
- [ ] Email-based reminder notifications for upcoming follow-ups

---

## Why I built this

Every job tracker I'd seen made me do the boring part — typing in company, role, status, every single time. I wanted something that worked the way I actually apply to jobs: fast, across a dozen tabs, with no patience to come back and log it all later. So I built the tracker to meet me where I already was — my inbox.
