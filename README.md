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





How to run :


The Issue: Your Python Services Aren't Running Locally

The error means your Node.js backend can't connect to the Drug Interaction Python module on port 5004. You need to start ALL Python services before starting the Node.js backend.

Solution: Start All Services in Correct Order

Step 1: Open 4 Separate Terminals

You need one terminal for each Python module and one for Node.js backend.

---

Terminal 1: Start Report Analyzer (Port 5001)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis/modules/report_analyzer

# Activate virtual environment
source venv/Scripts/activate

# Run the module
python app.py --port=5001
```

Keep this terminal open.

---

Terminal 2: Start Health Chatbot (Port 5002)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis/modules/health_chatbot

# Activate virtual environment
source venv/Scripts/activate

# Run the module
python app_integrated.py
```

Keep this terminal open.

---

Terminal 3: Start Symptom Checker (Port 5003)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis/modules/symptom_checker_ml

# Activate virtual environment
source venv/Scripts/activate

# Run the module
python app.py
```

Keep this terminal open.

---

Terminal 4: Start Drug Interaction (Port 5004)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis/modules/drug_interaction

# Activate virtual environment
source venv/Scripts/activate

# Run the module
python app.py
```

Keep this terminal open.

---

Terminal 5: Start Node.js Backend (Port 5000)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis/backend

# Start Node.js
npm run dev
# OR
node server.js
```

Keep this terminal open.

---

Terminal 6: Start Frontend (Port 8000)

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis

# Start HTTP server
python -m http.server 8000
```

Keep this terminal open.

---

Quick Verification: Check All Ports

Open a new terminal and run:

```bash
# Check Drug Interaction (port 5004)
curl http://localhost:5004/api/drugs/health

# Check Symptom Checker (port 5003)
curl http://localhost:5003/api/symptoms/health

# Check Chatbot (port 5002)
curl http://localhost:5002/api/chatbot/health

# Check Report Analyzer (port 5001)
curl http://localhost:5001/api/report-analyzer/health

# Check Node.js (port 5000)
curl http://localhost:5000
```

All should return success messages.

---

Alternative: Use Your start.py Script

Instead of opening 5 terminals manually, you can use your start.py script:

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis

# Activate virtual environment for Python
source venv/Scripts/activate  # If you have a root venv

# Run the master script
python start.py
```

This will start all services in one terminal. Then open another terminal for the frontend:

```bash
cd ~/Desktop/4th\ Major/project/medical-report-analysis
python -m http.server 8000
```

---

If Modules Won't Start

Check if virtual environment exists:

```bash
ls -la modules/drug_interaction/venv
```

If missing, create it:

```bash
cd modules/drug_interaction
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```

Check if models exist for symptom checker:

```bash
ls -la modules/symptom_checker_ml/models/
```

If missing, train them:

```bash
cd modules/symptom_checker_ml
source venv/Scripts/activate
python train_model.py
```

Check if Pinecone index exists for chatbot:

The chatbot needs Pinecone setup. Check if you ran:

```bash
cd modules/health_chatbot
source venv/Scripts/activate
python store_index.py
```

---

Summary

Service Port Command
Report Analyzer 5001 python app.py --port=5001
Health Chatbot 5002 python app_integrated.py
Symptom Checker 5003 python app.py
Drug Interaction 5004 python app.py
Node.js Backend 5000 npm run dev
Frontend 8000 python -m http.server 8000

Start them in order (1→2→3→4→5→6) and keep all terminals open!