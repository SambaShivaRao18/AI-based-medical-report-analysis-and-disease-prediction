from app_integrated import chatbot_bp
from flask import Flask

app = Flask(__name__)
app.register_blueprint(chatbot_bp)

if __name__ == "__main__":
    print("íº€ Health Chatbot running on port 5002")
    app.run(host="0.0.0.0", port=5002, debug=True)
