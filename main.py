import telebot
import requests
import jsons
from Class_ModelResponse import ModelResponse

BASE_URL = 'http://127.0.0.1:1234'
API_TOKEN = '111:AAG'
bot = telebot.TeleBot(API_TOKEN)
MAX_MESSAGE_LENGTH = 4096

# словарь для хранения контекста диалога для каждого пользователя (ключ: chat_id)
user_context = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Привет! Я ваш Telegram бот.\n"
        "Доступные команды:\n"
        "/start - вывод всех доступных команд\n"
        "/model - выводит название используемой языковой модели\n"
        "/clear - очистка истории диалога\n"
        "Отправьте любое сообщение, и я отвечу с помощью LLM модели."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['clear'])
def clear_context(message):
    chat_id = message.chat.id
    if chat_id in user_context:
        del user_context[chat_id]
    bot.reply_to(message, "Контекст очищен.")


@bot.message_handler(commands=['model'])
def send_model_name(message):
    response = requests.get(f'http://localhost:1234/v1/models')

    print(f"Status Code: {response.status_code}")
    print(f"Response Content: {response.text}")

    if response.status_code == 200:
        try:
            model_info = response.json()
            model_name = model_info['data'][0]['id']
            bot.reply_to(message, f"Используемая модель: {model_name}")
        except Exception as e:
            bot.reply_to(message, f"Ошибка при обработке ответа: {e}")
    else:
        bot.reply_to(message, 'Не удалось получить информацию о модели.')


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    # контекст пользователя
    if chat_id not in user_context:
        user_context[chat_id] = []

    user_context[chat_id].append({"role": "user", "content": message.text})

    request_data = {"messages": user_context[chat_id]}
    response = requests.post(f'{BASE_URL}/v1/chat/completions',
                             json=request_data)

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        answer = model_response.choices[0].message.content

        # обрезка ответа - 4096 символов в тг
        if len(answer) > MAX_MESSAGE_LENGTH:
            answer = answer[:MAX_MESSAGE_LENGTH]

        user_context[chat_id].append({"role": "assistant", "content": answer})

        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, 'Произошла ошибка при обращении к модели.')


if __name__ == '__main__':
    bot.polling(none_stop=True)
