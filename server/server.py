import json
import logging
import re
import socket
import subprocess
# import data.server_telegram as tg_bot
import threading
import time

import torch
from data.class_voice_assistant import voice_assistant
from openai import OpenAI

# import sounddevice as sd


pattern = r"system\((.*?)\)"

# def init_telegram_bot():
#    tg_bot.init(config.TELEGRAM_token)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],  # Вывод в stdout
)


def create_assistant():
    # INIT llm
    llm = OpenAI(base_url="http://192.168.1.108:11434/v1", api_key="ollama")

    # Init TTS
    modelTTS, _ = torch.hub.load(
        repo_or_dir="snakers4/silero-models",
        model="silero_tts",
        language="ru",
        speaker="v4_ru",
    )
    modelTTS.to(torch.device("cpu"))

    important_memory = json.load(open("data/memory.json", "r", encoding="utf-8"))
    # important_memory.append({"role":"user","content":f'
    # Вот твой исходный код:
    # {open("server.py", "r", encoding="utf-8").read()}'})

    anthony = voice_assistant(
        llm,
        "anthony",
        "ru",
        important_memory=important_memory,
        tts_set=modelTTS,
    )

    return anthony


def initialization():
    # INIT SERVER-SOCKET
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 5000))
    sock.listen()

    logging.info("Сервер ожидает соединения...")

    # Поток для телеграм-бота
    # bot_thread=threading.Thread(target=init_telegram_bot)
    # bot_thread.start()

    while True:
        # Принятие нового подключения
        conn, addr = sock.accept()
        logging.info(f"Подключен клиент: {addr}")

        # Создание нового экземпляра бота для каждого нового подключения
        anthony = create_assistant()

        # Обработка взаимодействий с клиентом
        server_thread = threading.Thread(target=handle_server, args=(conn, anthony))
        server_thread.start()


def bot_system(res, conn, anthony):
    matches = re.findall(pattern, res)
    fl = 0
    for match in matches:
        command = f"{match}"[1:-1]
        question = f"Мне выполнить: {command}?"
        conn.send(question.encode("utf-8") + b"TEXT")
        anthony.temp_memory.append({"role": "assistant", "content": question})
        ans = conn.recv(4096).decode("utf-8").lower()
        anthony.temp_memory.append({"role": "user", "content": ans})
        if "да" in ans or "давай" in ans or "выполни" in ans:
            result_command = subprocess.check_output(command, shell=True)
            conn.send(result_command + b"COMMAND")
            anthony.temp_memory.append(
                {
                    "role": "assistant",
                    "content": f"Выполнил команду: {result_command.decode('utf-8')}",
                }
            )
        else:
            response = anthony.think(ans).encode("utf-8")
            conn.send(response + b"TEXT")
            break
        fl = 1
    if fl:
        return 1


def handle_server(conn, anthony):
    try:
        while True:
            t = time.time()
            while time.time() - t <= 600:
                t = time.time()
                # Получаем данные от клиента и передаем боту
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    break
                logging.info("USER:" + data)
                anthony.think(data, conn=conn, speak=True).encode("utf-8")

                # Выполняем системные команды, если они есть
                # bot_system(response.decode("utf-8"), conn, anthony)

            anthony.temp_memory.clear()

    except ConnectionResetError:
        logging.info("Клиент отключился")
    finally:
        conn.close()


initialization()
