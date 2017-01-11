import logging
import os
import time
import sys
from threading import Thread, Event
from respeaker import Microphone
from bing_speech_api import BingSpeechAPI
from mpd import MPDClient

# get a key from https://www.microsoft.com/cognitive-services/en-us/speech-api
BING_KEY = ''

listNames = []

def setvol(v):
    try:
        client.setvol(v)
    except Exception as e:
        print "Failed to set volume"
        connect()

def task(quit_event):
    print "Started task"

    try:
        mic = Microphone(quit_event=quit_event)
    except Exception as e:
        print "Failed to open Microphone"
        sys.exit(1)

    print "Microphone opened"

    os.system("/etc/init.d/mopidy start")

    try:
	    bing = BingSpeechAPI(key=BING_KEY)
    except Exception as e:
        print "Failed to open speech API"

    print "Bing Speech API opened"

    print "Waiting for mopidy to start"
    time.sleep(60)

    print "Connecting to mopidy"
    connect()

    print "Playlists: "
    print listNames

    while not quit_event.is_set():
        if mic.wakeup('respeaker'):
            print('Wake up')
            setvol(10)
            data = mic.listen()
            try:
                text = bing.recognize(data)
                setvol(100)
                if text:
                    print('Recognized %s' % text)
                    if text == "pause music":
                        client.pause(1)
                    elif text == "play music":
                        client.pause(0)
                    elif text == "play next":
                        client.next()
                    elif text == "play previous":
                        client.previous()
                    else
                        for l in listNames:
                            if l in text:
                                print "Playing " + l + " playlist"
                                client.load(l)
                                time.sleep(2)
                                print "Calling client.play()"
                                try:
                                    client.play()
                                except Exception as e:
                                    print "Call to play() failed"
                                    print(e.message)
            except Exception as e:
                print(e.message)

def connect():
    global client
    client = MPDClient()

    client.timeout = 10
    client.idletimeout = None

    try:
        client.connect("localhost", 6600)
        print(client.mpd_version)
        playlists = client.listplaylists()
		
		listNames = []

        for playlist in playlists:
            if playlist['playlist'] != '[Radio Streams]':
                listNames.append(playlist['playlist'])
    except Exception as e:
        print(e.message)

def main():
    os.system("/etc/init.d/mopidy stop")
    print "Waiting for mopidy to stop"
    time.sleep(10)

    logging.basicConfig(level=logging.DEBUG)
    quit_event = Event()
    thread = Thread(target=task, args=(quit_event,))

    print "Starting thread"

    thread.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print('Quit')
            quit_event.set()
            break
    thread.join()

if __name__ == '__main__':
    main()