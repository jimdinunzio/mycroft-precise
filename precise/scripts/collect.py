#!/usr/bin/env python3
# Copyright 2019 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Record audio samples for use with precise

:-w --width int 2
    Sample width of audio

:-r --rate int 16000
    Sample rate of audio

:-c --channels int 1
    Number of audio channels
"""
from select import select
from sys import stdin
#from termios import tcsetattr, tcgetattr, TCSADRAIN

#import tty
import time
import wave
from os.path import isfile
from prettyparse import Usage
from pyaudio import PyAudio
import keyboard



from precise.scripts.base_script import BaseScript


def record_until(p, should_return, args):
    chunk_size = 1024
    stream = p.open(format=p.get_format_from_width(args.width), channels=args.channels,
                    rate=args.rate, input=True, frames_per_buffer=chunk_size)

    frames = []
    while not should_return():
        frames.append(stream.read(chunk_size))

    stream.stop_stream()
    stream.close()

    return b''.join(frames)


def save_audio(name, data, args):
    wf = wave.open(name, 'wb')
    wf.setnchannels(args.channels)
    wf.setsampwidth(args.width)
    wf.setframerate(args.rate)
    wf.writeframes(data)
    wf.close()


class CollectScript(BaseScript):
    RECORD_KEY = 'space'
    EXIT_KEY_CODE = 'esc'

    usage = Usage(__doc__)
    usage.add_argument('file_label', nargs='?', help='File label (Ex. recording-##)')

    def __init__(self, args):
        super().__init__(args)
        #self.orig_settings = tcgetattr(stdin)
        self.p = PyAudio()

    # def on_release(self, key):
    #     print('{0} release'.format(
    #         key))
    #     if key == Key.esc:
    #         # Stop listener
    #         return False 

    def key_pressed(self):
        # Collect events until released
        return keyboard.is_pressed('space')
        #return select([stdin], [], [], 0) == ([stdin], [], [])

    def show_input(self):
        None
        #tcsetattr(stdin, TCSADRAIN, self.orig_settings)

    def hide_input(self):
        None
        #tty.setcbreak(stdin.fileno())

    def next_name(self, name):
        name += '.wav'
        pos, num_digits = None, None
        try:
            pos = name.index('#')
            num_digits = name.count('#')
        except ValueError:
            print("Name must contain at least one # to indicate where to put the number.")
            raise

        def get_name(i):
            nonlocal name, pos
            return name[:pos] + str(i).zfill(num_digits) + name[pos + num_digits:]

        i = 0
        while True:
            if not isfile(get_name(i)):
                break
            i += 1

        return get_name(i)

    def wait_to_continue(self):
        while True:
            # Wait for the next event.
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == self.RECORD_KEY:
                    return True
                elif event.name == self.EXIT_KEY_CODE:
                    return False

    def record_until_key(self):
        def should_return():
            return self.key_pressed()

        return record_until(self.p, should_return, self.args)

    def _run(self):
        args = self.args
        self.show_input()
        args.file_label = args.file_label or input("File label (Ex. recording-##): ")
        args.file_label = args.file_label + ('' if '#' in args.file_label else '-##')
        self.hide_input()

        while True:
            print('Press space to record (esc to exit)...')

            if not self.wait_to_continue():
                break

            time.sleep(0.25)

            print('Recording...')
            d = self.record_until_key()
            name = self.next_name(args.file_label)
            save_audio(name, d, args)
            print('Saved as ' + name)
            print()

    def run(self):
        try:
            self.hide_input()
            self._run()
        finally:
            #tcsetattr(stdin, TCSADRAIN, self.orig_settings)
            self.p.terminate()


main = CollectScript.run_main

if __name__ == '__main__':
    main()
