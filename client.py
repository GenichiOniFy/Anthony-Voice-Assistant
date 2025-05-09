#!/home/genichi/Documents/python_venv/bin/python

import json
import queue
import socket
import struct
import threading
import time

import numpy as np
import pvporcupine
import sounddevice as sd
from pvrecorder import PvRecorder
from vosk import KaldiRecognizer, Model

from server.data import config

sock = None
recorder = None
porcupine = None
rec = None
audio_queue = queue.Queue()
is_speaking = False


def audio_playback_worker():
    """Поток для воспроизведения аудио."""
    global is_speaking
    while True:
        audio_data = audio_queue.get()
        if audio_data == "STOP":
            break
        is_speaking = True
        voice = np.frombuffer(audio_data, dtype=np.float32)
        sd.play(voice, 24000)
        sd.wait()
        is_speaking = False


# Запуск потока воспроизведения
audio_thread = threading.Thread(target=audio_playback_worker)
audio_thread.start()


def initialization():
    global sock
    global recorder
    global porcupine
    global rec
    # Init pvporcupine КЛИЕНТ
    porcupine = pvporcupine.create(
        access_key=config.PORCUPINE_api_key,
        keyword_paths=["./server/data/anthony_en_linux_v3_0_0.ppn"],
        sensitivities=[1],
    )

    # INIT VOSK
    model = Model(lang="ru")
    rec = KaldiRecognizer(model, 16000)

    recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("0.0.0.0", 5000))

    recorder.start()


initialization()


def getting_voice():
    voice_data = bytearray()
    while True:
        chunk = sock.recv(4096)
        # print(voice_data)
        if chunk.endswith(b"VOICE"):
            voice_data.extend(chunk[:-5])
            audio_queue.put(bytes(voice_data))
            voice_data = bytearray()

        elif chunk.endswith(b"END"):
            voice_data.extend(chunk[:-8])
            if voice_data:
                audio_queue.put(bytes(voice_data))
            break

        else:
            voice_data.extend(chunk)


t = 0
print("I am here")
while True:
    pcm = recorder.read()
    if not is_speaking:
        # print(pcm)
        keyword_index = porcupine.process(pcm)
        print(keyword_index)
        if keyword_index >= 0:
            recorder.stop()
            sock.send("Энтони".encode("utf-8"))
            getting_voice()
            # print(voice.decode())
            recorder.start()
            t = time.time()
        while time.time() - t <= 5:
            pcm = recorder.read()
            data = struct.pack("h" * len(pcm), *pcm)
            if rec.AcceptWaveform(data):
                recorder.stop()
                result = rec.Result()
                text = json.loads(result)["text"]
                if len(text) > 0:
                    sock.send(text.encode("utf-8"))
                    getting_voice()
                    # print(voice.decode())
                t = time.time()
                recorder.start()
