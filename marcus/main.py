from marcus import listen
from marcus import speak
from marcus import route_command


def main():
    speak("Marcus is online.")

    while True:
        command = listen()

        if command:
            response = route_command(command)
            speak(response)


if __name__ == "__main__":
    main()