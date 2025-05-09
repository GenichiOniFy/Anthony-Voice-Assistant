import socket

import telebot


def init(token):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("0.0.0.0", 1382))
    bot = telebot.TeleBot(token)

    @bot.message_handler(content_types=["text"])
    def get_text_messages(message):
        sock.send(message.text.encode())
        response = sock.recv(4096).decode()
        bot.send_message(message.from_user.id, response)

    bot.polling(none_stop=True, interval=0)
