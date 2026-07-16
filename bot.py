import os
import json
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
STATE_FILE = "last_update.json"

TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def load_offset():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("last_update_id", 0)
    return 0


def save_offset(update_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_update_id": update_id}, f)


def get_updates(offset):
    resp = requests.get(f"{TG_URL}/getUpdates", params={"offset": offset, "timeout": 5})
    resp.raise_for_status()
    return resp.json().get("result", [])


def send_message(chat_id, text):
    requests.post(f"{TG_URL}/sendMessage", data={"chat_id": chat_id, "text": text})


def ask_ai(user_text):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "mistral-small-latest",
        "messages": [{"role": "user", "content": user_text}],
    }
    resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=body)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def main():
    offset = load_offset()
    updates = get_updates(offset)

    last_id = offset
    for update in updates:
        last_id = update["update_id"] + 1
        message = update.get("message")
        if not message or "text" not in message:
            continue
        chat_id = message["chat"]["id"]
        user_text = message["text"]

        try:
            reply = ask_ai(user_text)
        except Exception as e:
            reply = f"Error: {e}"

        send_message(chat_id, reply)

    save_offset(last_id)


if __name__ == "__main__":
    main()
