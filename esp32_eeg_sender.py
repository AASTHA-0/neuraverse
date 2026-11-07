import json
import socket
import time

import network
from machine import ADC, Pin


# Set these for your network.
WIFI_SSID = "your wifi name"
WIFI_PASSWORD = "wifi password"
SERVER_IP = "your_pc ip"
SERVER_PORT = 5000

SAMPLE_RATE = 256
BATCH_SIZE = 256


def ask_person_name():
    while True:
        name = input("Person's name: ").strip()
        if name:
            return name
        print("Please enter a name.")


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connecting to Wi-Fi...")
    for _ in range(40):
        if wlan.isconnected():
            print("Wi-Fi connected:", wlan.ifconfig()[0])
            return
        time.sleep_ms(500)

    raise OSError("Could not connect to Wi-Fi")


def connect_server():
    sock = socket.socket()
    sock.connect((SERVER_IP, SERVER_PORT))
    print("Connected to EEG receiver")
    return sock


def read_millivolts(adc):
    return adc.read() * 3300 / 4095


def main():
    person = ask_person_name()
    print("Collecting data for:", person)

    # ADC1 pins: GPIO36=Fp1, GPIO35=Fp2, GPIO34=O1.
    fp1 = ADC(Pin(36))
    fp2 = ADC(Pin(35))
    o1 = ADC(Pin(34))

    for adc in (fp1, fp2, o1):
        adc.atten(ADC.ATTN_11DB)

    connect_wifi()
    sock = connect_server()
    samples = []
    sample_period = 1000000 // SAMPLE_RATE
    next_sample = time.ticks_us()

    print("Streaming at %d Hz. Press Ctrl+C to stop." % SAMPLE_RATE)
    try:
        while True:
            delay = time.ticks_diff(next_sample, time.ticks_us())
            if delay > 0:
                time.sleep_us(delay)
            next_sample = time.ticks_add(next_sample, sample_period)

            samples.append({
                "Fp1": read_millivolts(fp1),
                "Fp2": read_millivolts(fp2),
                "O1": read_millivolts(o1),
                "timestamp": time.time(),
                "person": person,
            })

            if len(samples) == BATCH_SIZE:
                sock.sendall((json.dumps(samples) + "\n").encode())
                samples = []
                print("Sent %d samples" % BATCH_SIZE)

    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        sock.close()


main()
