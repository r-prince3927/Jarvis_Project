import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os
import time
import tempfile
import uuid

# pip install pocketsphinx

recognizer = sr.Recognizer()
engine = pyttsx3.init() 
newsapi = "<Your Key Here>"

def speak_old(text):
    engine.say(text)
    engine.runAndWait()

def speak(text):
    # Save MP3 to a safe temp location with a unique name
    temp_dir = tempfile.gettempdir()
    filename = f"jarvis_{uuid.uuid4().hex}.mp3"
    full_path = os.path.join(temp_dir, filename)

    try:
        tts = gTTS(text)
        tts.save(full_path)

        # Initialize Pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Load and play the file
        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()

        # Keep the program running until the music stops playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        # Unload the music
        try:
            pygame.mixer.music.unload()
        except Exception:
            # Some pygame builds may not implement unload; ignore
            pass

    except Exception as e:
        # On any failure (permission, network, pygame), fall back to pyttsx3
        print(f"TTS playback failed ({e}), falling back to pyttsx3")
        speak_old(text)

    finally:
        # Cleanup temp file if it exists
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception:
            pass

def aiProcess(command):
    client = OpenAI(api_key="<Your Key Here>",
    )

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a virtual assistant named jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
        {"role": "user", "content": command}
    ]
    )

    return completion.choices[0].message.content

def processCommand(c):
    if "open google" in c.lower():
        webbrowser.open("https://google.com")
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
    elif c.lower().startswith("play"):
        song = c.lower().split(" ")[1]
        link = musicLibrary.music[song]
        webbrowser.open(link)

    elif "news" in c.lower():
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
        if r.status_code == 200:
            # Parse the JSON response
            data = r.json()
            
            # Extract the articles
            articles = data.get('articles', [])
            
            # Print the headlines
            for article in articles:
                speak(article['title'])

    else:
        # Let OpenAI handle the request
        output = aiProcess(c)
        speak(output) 





if __name__ == "__main__":
    speak("Initializing Jarvis....")
    while True:
        # Listen for the wake word "Jarvis"
        # obtain audio from the microphone
        r = sr.Recognizer()
         
        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                try:
                    audio = r.listen(source, timeout=2, phrase_time_limit=1)
                except sr.WaitTimeoutError:
                    # No speech detected in timeout window
                    print("Listening timed out while waiting for phrase to start")
                    continue
                except (OSError, ConnectionResetError) as mic_err:
                    print(f"Microphone read error: {mic_err}")
                    time.sleep(0.5)
                    continue

            # Try online Google recognition first
            try:
                word = r.recognize_google(audio)
            except sr.UnknownValueError:
                # Nothing recognized; continue listening
                continue
            except sr.RequestError as e:
                # Network / API error (e.g., connection reset)
                print(f"Speech recognition request failed: {e}")
                # Try offline pocketsphinx if available
                try:
                    word = r.recognize_sphinx(audio)
                except Exception as sphinx_err:
                    print(f"Offline recognition failed: {sphinx_err}")
                    time.sleep(0.5)
                    continue

            if word.lower() == "jarvis":
                speak("Ya")
                # Listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    try:
                        audio = r.listen(source)
                    except sr.WaitTimeoutError:
                        print("Listening timed out while waiting for phrase to start")
                        continue
                    except (OSError, ConnectionResetError) as mic_err:
                        print(f"Microphone read error: {mic_err}")
                        time.sleep(0.5)
                        continue

                    # Recognize the command with fallback to offline
                    try:
                        command = r.recognize_google(audio)
                    except sr.UnknownValueError:
                        speak("Sorry, I didn't catch that.")
                        continue
                    except sr.RequestError as e:
                        print(f"Speech recognition request failed during command: {e}")
                        try:
                            command = r.recognize_sphinx(audio)
                        except Exception as sphinx_err:
                            print(f"Offline recognition failed: {sphinx_err}")
                            speak("Speech recognition is unavailable right now.")
                            continue

                    processCommand(command)


        except Exception as e:
            print("Error; {0}".format(e))