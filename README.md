# 🗳️ Voting Platform

A cross-platform (iOS, Android, Web) application that allows users to create voting channels on **anything and everything**, enabling seamless, secure online voting with **one-vote-per-device enforcement**.

---

## 🚀 Features

✅ Create voting channels with customizable fields  
✅ Shareable voting links and QR codes for voters  
✅ Voters can vote without accounts but provide required information  
✅ One-vote-per-device enforcement for integrity  
✅ Real-time or post-vote result display with charts  
✅ Accessible via iOS, Android, and Web  
✅ Future support for ID-verified official voting

---

## 🛠️ Tech Stack

- **Frontend:** Flutter (iOS, Android, Web)
- **Backend:** Django REST API
- **Database:** PostgreSQL
- **CI/CD:** GitHub Actions + Codemagic
- **Deployment:** Render/Fly.io, Vercel (optional for frontend)

---

## 📦 Installation

### **1️⃣ Clone the repository**
```bash
  git clone https://github.com/YourUsername/voting-platform.git

cd voting-platform
```

---


### **2️⃣ Backend Setup**
Create a Python virtual environment:

```bash

  python -m venv venv
  source venv/bin/activate
```
---
Install dependencies:

```bash
  pip install -r requirements.txt
  
```

Create a .env file using the provided .env.example.

Run migrations:

```bash
  python manage.py migrate

```
Start the server:

```bash
  python manage.py runserver

```
---

### **3️⃣ Frontend Setup (Flutter)**

Install Flutter: Flutter Installation Guide

Navigate to the frontend directory:

```bash
  cd frontend
  
```

Get dependencies:

```bash
  flutter pub get

```

Run on Web:

```bash
  flutter run -d chrome

```
Run on iOS/Android using your simulator or device:

```bash
  flutter run

```
---

## 🌐 Environment Variables
Create a .env file in the backend root with:

```ini

DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=your_postgres_url
ALLOWED_HOSTS=localhost,127.0.0.1

```
Adjust as needed for production.

---

# 🧪 Testing

## **Backend**

```bash
  python manage.py test_file
  
```
## **Frontend**

```bash
  flutter test_file

```
---
# 🗂️ Project Structure

```bash

voting-platform/
│
├── backend/                 # Django REST API
│   ├── voting/              # App for voting logic
│   ├── users/               # User authentication
│   └── ...
│
├── frontend/                # Flutter app
│   ├── lib/
│   └── ...
│
├── .github/                 # GitHub Actions workflows
│
└── README.md

```
---
# 📈 Roadmap

✅ MVP with core voting and result functionality

✅ Web + iOS + Android support

✅ One-vote-per-device enforcement

✅ ID verification for official voting (Future)

✅ Analytics dashboard for creators (Future)

✅ AI-powered poll suggestions (Future)

---

# 🤝 Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

For major changes, open an issue first to discuss what you would like to change.

---

# 📜 License
This project is licensed under the MIT License.

---

# 📞 Contact
If you have questions, please open an issue or contact:

Project Owner: [Bruno Fonkeng]

Email: [Your Email]

LinkedIn: [Your LinkedIn]

---

Note: This project aligns with global data privacy standards (GDPR/CCPA) and allows voters to request data deletion upon request for compliance.
---