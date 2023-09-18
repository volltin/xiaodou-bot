# -*- coding: utf-8 -*-
import contextlib
import dataclasses
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import List, Optional

import azure.cognitiveservices.speech as speechsdk
import dotenv
import openai

with contextlib.redirect_stdout(None):
    from pygame import mixer

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

# input and output device names, if None, use default device
INPUT_DEVICE_NAME = None  # Azure format
OUTPUT_DEVICE_NAME = None  # pygame format

# Set up OpenAI API credentials
openai.api_type = "azure"
openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_version = "2023-03-15-preview"
openai.api_key = os.getenv("OPENAI_API_KEY")
# Set up engine name
engine_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
# Set up the system prompt
SYSTEM_PROMPT_FILE = str(Path(__file__).parent / "prompts" / "system.txt")
SYSTEM_PROMPT_AUTOLOAD = True

# Set up Azure Speech-to-Text and Text-to-Speech credentials
speech_key = os.getenv("SPEECH_API_KEY")
service_region = os.getenv("SPEECH_SERVICE_REGION")
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
# Set up Azure Text-to-Speech language
speech_config.speech_synthesis_language = "zh-CN"
# Set up Azure Speech-to-Text language recognition
speech_config.speech_recognition_language = "zh-CN"
speech_config.set_speech_synthesis_output_format(
    speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3
)

# Set up the voice configuration
speech_config.speech_synthesis_voice_name = "zh-CN-XiaochenNeural"
speech_synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config, audio_config=None
)


# Set up the path to the keyword recognition model
MOLDE_PATH = str(Path(__file__).parent / "models" / "Xiaodou.table")
_model = speechsdk.KeywordRecognitionModel(MOLDE_PATH)
KEYWORD = "小豆"

# Set up the sound effect for the start and end of speech recognition
SOUND_START = str(Path(__file__).parent / "sounds" / "sound_start.wav")
SOUND_END = str(Path(__file__).parent / "sounds" / "sound_end.wav")


# Define the speech-to-text function
def speech_to_text():
    # Set up the audio configuration
    if INPUT_DEVICE_NAME:
        audio_config = speechsdk.audio.AudioConfig(
            use_default_microphone=False, device_name=INPUT_DEVICE_NAME
        )
    else:
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Create a speech recognizer and start the recognition
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )

    # result = speech_recognizer.recognize_once_async().get()

    keyword_recognizer = speechsdk.KeywordRecognizer(audio_config=audio_config)
    done = False
    logging.info(
        "Say something starting with '{}' followed by whatever you want...".format(
            KEYWORD
        )
    )

    def recognized_cb(evt):
        # Only a keyword phrase is recognized. The result cannot be 'NoMatch'
        # and there is no timeout. The recognizer runs until a keyword phrase
        # is detected or recognition is canceled (by stop_recognition_async()
        # or due to the end of an input file or stream).
        result = evt.result
        if result.reason == speechsdk.ResultReason.RecognizedKeyword:
            logging.info("keyword_recognizer RECOGNIZED KEYWORD: %s", result.text)
        nonlocal done
        done = True

    def canceled_cb(evt):
        result = evt.result
        if result.reason == speechsdk.ResultReason.Canceled:
            logging.info(
                "keyword_recognizer CANCELED: %s", result.cancellation_details.reason
            )
        nonlocal done
        done = True

    keyword_recognizer.recognized.connect(recognized_cb)
    keyword_recognizer.canceled.connect(canceled_cb)

    result = keyword_recognizer.recognize_once_async(_model).get()
    stop_future = keyword_recognizer.stop_recognition_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedKeyword:
        play_sound(SOUND_START, wait=False)
        t = speech_recognizer.recognize_once_async().get()
        play_sound(SOUND_END, wait=False)
        if t.reason == speechsdk.ResultReason.RecognizedSpeech:
            logging.info("speech_recognizer RECOGNIZED: %s", t.text)
            return t.text
        else:
            logging.info("speech_recognizer ERROR: %s", t.reason)
            return "[Unknown]"
    elif result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return "[No Match]"
    elif result.reason == speechsdk.ResultReason.Canceled:
        return "[Canceled]"
    else:
        return "[Unknown]"


def play_sound(sound_file, wait=True):
    if OUTPUT_DEVICE_NAME:
        mixer.init(48000, -16, 2, 4096, devicename=OUTPUT_DEVICE_NAME)
    else:
        mixer.init(48000, -16, 2, 4096)
    sound = mixer.Sound(sound_file)
    channel = sound.play()
    if wait:
        while channel.get_busy():
            time.sleep(0.05)
    return True


# Define the text-to-speech function
def text_to_speech(text):
    try:
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            stream = speechsdk.AudioDataStream(result)
            tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            logging.info("Text-to-speech conversion successful.")
            logging.debug("text-to-speech, saving to %s", tmp_wav.name)
            stream.save_to_wav_file(tmp_wav.name)
            logging.debug("Playing speech...")
            play_sound(tmp_wav.name)
            logging.debug("text-to-speech, unlinking %s", tmp_wav.name)
            os.unlink(tmp_wav.name)
            return True
        else:
            logging.info("Speech synthesis failed: %s", result.reason)
            return False
    except Exception as ex:
        logging.error("Error in text-to-speech: %s", ex)
        return False


# Define the Azure OpenAI language generation function
def generate_text(messages):
    response = openai.ChatCompletion.create(
        engine=engine_name,
        messages=messages,
        temperature=0.7,
        max_tokens=75,
    )
    return response["choices"][0]["message"]["content"]


@dataclasses.dataclass
class Message:
    role: str
    content: str


class HistoryManager:
    # keep a window of the last 20 messages, or last 2000 words
    def __init__(self, max_len=30, max_words=3000, system_prompt_file=None):
        self.max_len = max_len
        self.max_words = max_words
        self.history: List[Message] = []
        self.words = 0
        self.system_prompt_file = system_prompt_file
        if system_prompt_file:
            self.get_system_prompt()

    def add(self, message: Message):
        self.history.append(message)
        self.words += len(message.content.split())
        while (
            self.history and len(self.history) > self.max_len
        ) or self.words > self.max_words:
            self.history.pop(0)
            self.words -= len(self.history[0].content.split())

    def get_system_prompt(self):
        def loaf_from_file():
            if self.system_prompt_file:
                with open(self.system_prompt_file, "r") as f:
                    system_prompt = f.read()
                return system_prompt
            return None

        if SYSTEM_PROMPT_AUTOLOAD:
            return loaf_from_file()
        else:
            if hasattr(self, "system_prompt") and self.system_prompt:
                return self.system_prompt
            elif self.system_prompt_file:
                self.system_prompt = loaf_from_file()
            else:
                return None

    def to_array(self):
        openai_messages = [{"role": m.role, "content": m.content} for m in self.history]
        system_prompt = self.get_system_prompt()
        if system_prompt:
            openai_messages = [
                {"role": "system", "content": system_prompt}
            ] + openai_messages
        return openai_messages


history_manager = HistoryManager(system_prompt_file=SYSTEM_PROMPT_FILE)
# Main program loop
while True:
    # Get input from user using speech-to-text
    user_input = speech_to_text()
    logging.info("You said: %s", user_input)

    print("You said: {}".format(user_input))

    if user_input in ["[No Match]", "[Canceled]", "[Unknown]"]:
        continue

    # Generate a response using OpenAI
    history_manager.add(Message("user", user_input))
    try:
        logging.info("Start generating response...")
        response = generate_text(history_manager.to_array())
        logging.info("AI said: %s", response)
        print("AI said: {}".format(response))

        # Convert the response to speech using text-to-speech
        text_to_speech(response)
        history_manager.add(Message("system", response))
    except Exception as e:
        logging.error("Error generating response: %s", e)
        text_to_speech("遇到一些错误，请重说一次")
