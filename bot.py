import os
import json
import logging
import random
from twilio.rest import Client
from flask import Flask, request
import cohere

# ⚠️ Clés API
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # Numéro Twilio WhatsApp
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# 📂 Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# 📌 Initialisation de Cohere
co = cohere.Client(COHERE_API_KEY)

# 📝 Configuration du logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 📂 Charger les données des utilisateurs
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# 📂 Sauvegarder les données des utilisateurs
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

JOKER_JOKES = [
    "Pourquoi Batman n'aime pas les blagues ? Parce qu'il n'a pas de parents ! HAHAHA !",
    # ... Ajoutez d'autres blagues ici
]

# 🚀 Commande /start
def start(message, from_number):
    response = (
        f"🤡🚬Ah, tu es là... Enfin. Bienvenue {from_number} ! 🎉\n"
        "Tu veux des prédictions ? Rejoins-moi dans mon équipe pour obtenir certaines offres spéciaux: \n https://t.me/FreeSurf237_Canal_INTECH \n https://t.me/+pmj78cr6mYBhMTM8\n"
        "Pour prédire: /predire [équipe1] vs [équipe2]."
    )
    send_whatsapp_message(response, from_number)

# 🔮 Commande /predire
def predict_score(message, from_number):
    if len(message.split()) < 3:
        send_whatsapp_message("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2] !", from_number)
        return

    match = message.split(" ", 2)[2]  # Récupère la partie après "/predire"
    if "vs" not in match:
        send_whatsapp_message("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2].", from_number)
        return

    team1, team2 = match.split(" vs ")
    prompt = f"Imagine que tu es le Joker. Fais une estimation du score final pour {team1} vs {team2} en tenant compte de leurs performances."

    try:
        response = co.chat(model="command-r-plus-08-2024", messages=[{"role": "user", "content": prompt}])
        prediction = response.message.content[0].text.strip()
        send_whatsapp_message(f"😈 *Le Joker dit* : {prediction}", from_number)
    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        send_whatsapp_message("❌ Impossible d'obtenir une prédiction.", from_number)

# 🃏 Commande /joke
def joke(message, from_number):
    joke = random.choice(JOKER_JOKES)
    send_whatsapp_message(f"🤡 {joke}", from_number)

# 📊 Commande /stats
def stats(message, from_number):
    user_data = load_user_data()
    remaining = user_data.get(from_number, {}).get("predictions_left", 15)
    send_whatsapp_message(f"🤡 Il te reste {remaining} prédictions aujourd'hui... HAHAHA!", from_number)

# 📩 Fonction pour envoyer des messages via WhatsApp Twilio
def send_whatsapp_message(message, to_number):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message,
        from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
        to=f"whatsapp:{to_number}"
    )
    return message.sid

# 🚀 Flask pour recevoir les messages
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form
    from_number = data.get("From")
    body = data.get("Body").strip().lower()

    # Gérer les commandes
    if body.startswith("/start"):
        start(body, from_number)
    elif body.startswith("/predire"):
        predict_score(body, from_number)
    elif body.startswith("/joke"):
        joke(body, from_number)
    elif body.startswith("/stats"):
        stats(body, from_number)
    else:
        send_whatsapp_message("🤡 Commande non reconnue. Tape /help pour voir les options.", from_number)
    
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
