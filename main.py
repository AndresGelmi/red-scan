import network
import time
import gc
from api_red import get_paradero_con_token, extraer_token_paradero
from keys import WIFI_SSID, WIFI_PASSWORD
from machine import Pin, I2C
import ssd1306
import _thread

paraderos = ['PC837', 'PC836', 'PC831']

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Hola ESP32", 0, 0)
oled.text("Pantalla OK", 0, 12)
oled.show()

is_loading = False
lock = _thread.allocate_lock()


def set_loading(value):
    global is_loading
    with lock:
        is_loading = value


def get_loading():
    with lock:
        return is_loading


def draw_loading_frame(frame_text):
    oled.fill(0)
    oled.text(frame_text, 48, 28)
    oled.show()


def load():
    frames = ["", ".", "..", "...", "...."]
    idx = 0

    while get_loading():
        draw_loading_frame(frames[idx])
        idx = (idx + 1) % len(frames)
        time.sleep(0.35)

    # pantalla al terminar
    oled.fill(0)
    oled.show()


def conectar_wifi(ssid, password, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(ssid, password)

        t0 = time.time()
        dots = 0

        while not wlan.isconnected():
            if time.time() - t0 > timeout:
                raise RuntimeError("Timeout conectando a WiFi")

            print(".", end="")
            oled.fill_rect(0, 16, 128, 16, 0)
            oled.text("." * ((dots % 4) + 1), 0, 16)
            oled.show()
            dots += 1
            time.sleep(0.5)

    print("\nWiFi conectado")
    print("IP:", wlan.ifconfig()[0])

    oled.fill(0)
    oled.text("WiFi conectado", 0, 0)
    oled.text(wlan.ifconfig()[0], 0, 16)
    oled.show()
    time.sleep(1)

    return wlan


def list_get(lst, index, default=None):
    try:
        return lst[index]
    except (IndexError, TypeError):
        return default


def fill_data(raw_data):
    data = {
        "result": False,
        "paraderos": {}
    }

    hay_al_menos_un_ok = False

    for codsimt, parada_raw in raw_data.items():
        parada_data = {
            "result": parada_raw.get("ok", False),
            "address": parada_raw.get("data", {}).get("nomett", ""),
            "servicios": []
        }

        if parada_data["result"]:
            hay_al_menos_un_ok = True

        buses = parada_raw.get("data", {}).get("servicios", {}).get("item", [])

        if isinstance(buses, dict):
            buses = [buses]

        for bus in buses:
            servicio_data = {
                "servicio": bus.get("servicio", ""),
                "bus1": {
                    "patente": bus.get("ppubus1"),
                    "distancia": bus.get("distanciabus1"),
                    "tiempo": bus.get("horaprediccionbus1")
                },
                "bus2": {
                    "patente": bus.get("ppubus2"),
                    "distancia": bus.get("distanciabus2"),
                    "tiempo": bus.get("horaprediccionbus2")
                }
            }
            parada_data["servicios"].append(servicio_data)

        data["paraderos"][codsimt] = parada_data

    data["result"] = hay_al_menos_un_ok
    return data


def main():
    gc.collect()
    conectar_wifi(WIFI_SSID, WIFI_PASSWORD)

    raw_data = {}

    print("mem libre antes de token:", gc.mem_free())

    # iniciar animación de carga
    set_loading(True)
    _thread.start_new_thread(load, ())

    try:
        token = extraer_token_paradero(paraderos[0])

        for codigo in paraderos:
            gc.collect()
            raw_data[codigo] = get_paradero_con_token(codigo, token)

    finally:
        # detener animación aunque haya error
        set_loading(False)
        time.sleep(0.5)

    data = fill_data(raw_data)

    oled.fill(0)
    oled.show()

    return data


print(main())