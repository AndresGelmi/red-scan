import network
import time
import gc
from api_red import get_paradero
from keys import WIFI_SSID, WIFI_PASSWORD
from machine import Pin, I2C
import ssd1306

paraderos = ['PC837', 'PC836', 'PC831']

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # o 128x32 según tu pantalla
oled.fill(0)
oled.text("Hola ESP32, Pantalla Funcional!", 0, 0)
oled.show()





def conectar_wifi(ssid, password, timeout=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Conectando a WiFi...")
        wlan.connect(ssid, password)

        t0 = time.time()
        while not wlan.isconnected():
            if time.time() - t0 > timeout:
                raise RuntimeError("Timeout conectando a WiFi")
            print(".", end="")
            time.sleep(0.5)

    print("\nWiFi conectado")
    print("IP:", wlan.ifconfig()[0])
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

        # Asegurar que buses sea lista
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
    wlan = conectar_wifi(WIFI_SSID, WIFI_PASSWORD)

    print("mem libre antes de HTTPS:", gc.mem_free())

    paraderos = ["PC837", "PC836", "PC831"]
    raw_data = {}

    raw_data["PC837"] = get_paradero(paraderos[0])
    raw_data["PC836"] = get_paradero(paraderos[1])
    raw_data["PC831"] = get_paradero(paraderos[2])

    print("RAW:")
    print(raw_data)

    data = fill_data(raw_data)

    print("DATA:")
    print(data)

    return data


print(main())

