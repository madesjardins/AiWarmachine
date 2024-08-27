from PyQt6 import QtCore
# from gtts import gTTS
import os
from io import BytesIO
import pygame
import argparse
import queue
import sys
import sounddevice as sd
from ast import literal_eval
from vosk import Model, KaldiRecognizer
from TTS.api import TTS
import subprocess
import pyglet
import mmap
import re

piper_dir = r"D:\Dev_Projects\AiWarmachine\test\piper"
piper_exe = os.path.join(piper_dir, "piper.exe")


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


VOICES_DICT = {
    'one': "en_US-amy-medium",
    'two': "en_US-kristin-medium", 'to': "en_US-kristin-medium",
    'three': "en_GB-cori-high", 'tree': "en_GB-cori-high",
    'four': "en_GB-aru-medium", 'for': "en_US-aru-medium",
}


class Narrator(QtCore.QObject):

    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050)
        # self.tts = TTS("tts_models/en/ek1/tacotron2", progress_bar=False).to("cuda")
        self.output_file_template = r"D:\tmp\output.{:04d}.wav"
        self.sound_num = 0
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.startupinfo.wShowWindow = subprocess.SW_HIDE

        self.voice_re_c = re.compile("voice (?P<vnum>[^ ]+)")

    def speak(self, text, lang='en', tld='us', slow=False, wait_till_over=True):
        if text.strip():
            voice = "FR_mls_1840"  # VOICES_DICT['two']
            # if v_result := self.voice_re_c.match(text):
            #     voice = VOICES_DICT.get(v_result.group("vnum"), voice)
            #     text = text[len(v_result.group(0)):]
            # tts = gTTS(text=text, lang=lang, tld=tld, slow=slow)
            # fp = BytesIO()
            # tts.write_to_fp(fp)
            # fp.seek(0)
            # self.tts.tts_to_file(text=text, file_path=self.output_file)
            output_file = self.output_file_template.format(self.sound_num)
            command_str = f"echo \"{text}\" | {piper_exe} -m {piper_dir}\\voices\\{voice}.onnx -f {output_file}"
            print(command_str)
            os.system(command_str)
            with open(output_file) as f:
                sound_data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            pygame.mixer.music.load(sound_data)
            pygame.mixer.music.play()
            if True:  # wait_till_over:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.stop()

            # buffer
            self.sound_num = (self.sound_num + 1) % 2


if __name__ == '__main__':

    narrator = Narrator()
    q = queue.Queue()
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "-l", "--list-devices", action="store_true",
        help="show list of audio devices and exit")
    args, remaining = parser.parse_known_args()
    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[parser])
    parser.add_argument(
        "-f", "--filename", type=str, metavar="FILENAME",
        help="audio file to store recording to")
    parser.add_argument(
        "-d", "--device", type=int_or_str,
        help="input device (numeric ID or substring)")
    parser.add_argument(
        "-r", "--samplerate", type=int, help="sampling rate")
    parser.add_argument(
        "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
    args = parser.parse_args(remaining)

    try:
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, "input")
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info["default_samplerate"])

        if args.model is None:
            model = Model(lang="en-us")
        else:
            model = Model(lang=args.model)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        with sd.RawInputStream(samplerate=args.samplerate, blocksize=8000, device=args.device, dtype="int16", channels=1, callback=callback):
            print("#" * 80)
            print("Press Ctrl+C to stop the recording")
            print("#" * 80)

            rec = KaldiRecognizer(model, args.samplerate)
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result_dict = literal_eval(rec.Result()) or {}
                    text = result_dict.get('text')
                    print(text)
                    if text == "quit":
                        break
                    elif text:
                        narrator.speak(text, wait_till_over=False)
                # else:
                #     print(rec.PartialResult())
                if dump_fn is not None:
                    dump_fn.write(data)

    except KeyboardInterrupt:
        print("\nDone")
        parser.exit(0)
    except Exception as e:
        parser.exit(type(e).__name__ + ": " + str(e))
