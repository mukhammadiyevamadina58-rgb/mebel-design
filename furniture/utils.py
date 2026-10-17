import requests

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    if reply_markup:
        payload['reply_markup'] = reply_markup
        
    try:
        # timeout=5 -> Agar internet ishlamasa yoki Telegram sekin kelsa, 
        # sayt cheksiz kutib o'tirmaydi, 5 sekundda to'xtab o'z ishini davom ettiradi.
        response = requests.post(url, json=payload, timeout=5)
        
        # Agar Telegram xatolik qaytarsa (masalan, token xato yoki chat topilmadi)
        if response.status_code != 200:
            print(f"Telegram API xatolik qaytardi: {response.text}")
            return False
            
        return True

    except requests.exceptions.RequestException as e:
        # Internet yo'q yoki ulanish vaqti tugasa (timeout), 
        # bu yer xatolikni ushlab qoladi va saytni qulashdan saqlaydi.
        print(f"Tarmoq bilan bog'liq xatolik: {e}")
        return False