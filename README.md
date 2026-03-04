# MediAnalyze - AI Medical Report Analysis System

## 📋 Overview
A full-stack AI-powered medical report analysis system with four modules:
1. **Report Analysis** - AI-powered medical report analysis with patient/doctor views
2. **Health Chatbot** - RAG-based health assistant
3. **Symptom Checker** - Disease prediction based on symptoms
4. **Drug Interaction** - Medication compatibility checking

## 🏗️ Project Structure
medical-report-analysis/
├── index.html # Landing page
├── login.html # Login page
├── register.html # Registration page
├── dashboard.html # Patient dashboard
├── doctor-dashboard.html # Doctor dashboard
├── report-analysis.html # Module 1: Report analysis
├── chatbot.html # Module 2: Health chatbot
├── symptom-checker.html # Module 3: Symptom checker
├── drug-interaction.html # Module 4: Drug interaction
├── profile.html # User profile
├── css/ # Stylesheets
├── js/ # JavaScript files
├── assets/ # Images and assets
├── backend/ # Node.js backend
│ ├── server.js
│ ├── models/
│ ├── routes/
│ └── middleware/
└── modules/ # Python modules
└── report_analyzer/ # Report analysis module
├── app.py
├── agents/
├── config/
└── utils/


## 🚀 Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB Atlas account
- Groq API key

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd medical-report-analysis

#3.Setup Python Environment

cd modules/report_analyzer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Groq API key

 #Setup Node.js Backend
cd backend
npm install
cp .env.example .env
# Edit .env with your MongoDB URI and JWT secret

#Setup Frontend
# No installation needed - just serve with Python HTTP server
cd ..
python -m http.server 8000

🏃 Running the Application
#Terminal 1 - Python Flask Server
cd modules/report_analyzer
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py --port=5001


#Terminal 2 - Node.js Backend
bash
cd backend
npm run dev


#Terminal 3 - Frontend Server
cd medical-report-analysis
python -m http.server 8000
Access the application at: http://localhost:8000