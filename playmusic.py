import logging
import os
import time
import sys
from threading import Thread, Event
from respeaker import Microphone
from bing_speech_api import BingSpeechAPI
from mpd import MPDClient
import pyaudio

# get a key from https://www.microsoft.com/cognitive-services/en-us/speech-api
BING_KEY = ''      

def setvol(v):
    try:
        client.setvol(v)
    except Exception as e:               
        print "Failed to set volume"
        connect()

def speak(text):
    try:
        data = bing.synthesize(text, stream=None)
        stream = p.open(format = p.get_format_from_width(2), channels = 1, rate = 16000, output = True)
        stream.write(data)
        stream.stop_stream()
        stream.close()
    except Exception as e:               
        print "Failed to say: " + text

def task(quit_event):                                                         
    print "Started task"

    try:
        mic = Microphone(quit_event=quit_event)                                   
    except Exception as e:               
        print "Failed to open Microphone"
        sys.exit(1)

    print "Microphone opened"

    os.system("/etc/init.d/mopidy start")

    global p
    p = pyaudio.PyAudio()

    global bing 
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

    speak("My name is Marvin")

    while not quit_event.is_set():
        if mic.wakeup('marvin'):        
            print('Wake up')               
            setvol(80)
            data = mic.listen()            
            try:                      
                text = bing.recognize(data)
                if text:           
                    print('Recognized %s' % text)
                    if text == "pause music":
                        client.pause(1)
                    elif text == "play music":
                        client.pause(0)
                    elif text == "play next":
                        client.next()
                        print(client.status())
                    elif text == "play previous":
                        client.previous()
                        print(client.status())
                    elif text == "status":
                        speak(str(client.status()))
                    else:
                        for l in listNames:
                            if l in text:
                                print "Playing " + l + " playlist"
                                setvol(100)
                                speak("Playing " + l + " playlist")
                                client.clear()
                                client.load(l)
                                time.sleep(2)
                                print "Calling client.play()"
                                try:
                                    client.play()
                                    print(client.status())
                                except Exception as e:               
                                    print "Call to play() failed"
                                    print(e.message)                 
                                break
            except Exception as e:               
                print(e.message)                 
            setvol(100)

def connect():
    global client
    client = MPDClient()

    client.timeout = 10
    client.idletimeout = None

    try:
        client.connect("localhost", 6600)
        print(client.mpd_version)
        playlists = client.listplaylists()

        global listNames
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
