import random
import requests

TOKEN = '7338578221:AAFzx5IGRnRJzhRUHun8gX3fv9sb8600U1U'


def bot_send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get('result')
    else:
        raise requests.exceptions.HTTPError(f"Sending message to {chat_id} raised error.")


def gen_random_code():
    return ''.join([str(random.randint(0, 9)) for i in range(5)])
