import logging


class voice_assistant:
    def __init__(
        self,
        llm,
        name="bot",
        language="en",
        temp_memory=[],
        important_memory=[],
        tts_set=None,
    ):
        self.name = name
        self.language = language
        self.temp_memory = temp_memory
        self.important_memory = important_memory
        self.llm = llm
        self.modelTTS = tts_set
        logging.info("\nThe voice assistant has been successfully created")

    def think(self, request, conn=None, speak=False):
        if len(request) > 0:
            self.temp_memory.append({"role": "user", "content": f"{request}"})
            chat_completion = self.llm.chat.completions.create(
                messages=self.important_memory + self.temp_memory,
                model="deepseek-v2",
                stream=True,
            )
            response = ""
            speach_buffer = ""

            for chunk in chat_completion:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    response += chunk_content

                    if conn and (not speak):
                        conn.send(chunk_content.encode("utf-8"))

                    if speak and self.modelTTS:
                        speach_buffer += chunk_content

                        logging.info(speach_buffer)
                        # if len(speach_buffer) >= 30 or any(
                        if any(
                            punct in chunk_content for punct in ".!?,:\n"
                        ):
                            try:
                                audio_bytes = self.speak(speach_buffer)
                                if conn:
                                    conn.send(audio_bytes)
                                    conn.send(b'VOICE')
                                    speach_buffer = ""

                            except:
                                continue


            response += "\n"
            if conn and (not speak):
                conn.send(b"\n")
            if conn and (speak):
                conn.send(b'END')

            self.temp_memory.append({"role": "assistant", "content": response})
            return response + "\n"

    def speak(self, data):
        voice = self.modelTTS.apply_tts(
            text=data + "...",
            speaker="eugene",
            sample_rate=24000,
            put_accent=True,
            put_yo=True,
        )

        voice_np = voice.numpy()
        voice_bytes = voice_np.tobytes()

        return voice_bytes
