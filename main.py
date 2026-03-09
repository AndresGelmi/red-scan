import network
import time
import gc
from api_red import get_paradero
from keys import WIFI_SSID, WIFI_PASSWORD

CODSIMT = "PC837"


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
        'result': False,
        'address': "",
        'servicio1': ['', {}, {}],
        'servicio2': ['', {}, {}],
        'servicio3': ['', {}, {}],
    }

    data["result"] = raw_data.get("ok", False)
    data["address"] = raw_data.get("data", {}).get("nomett", "")

    buses = raw_data.get("data", {}).get("servicios", {}).get("item", [])
    servicios_keys = ["servicio1", "servicio2", "servicio3"]

    for i, key in enumerate(servicios_keys):
        bus = list_get(buses, i)
        if not bus:
            continue

        data[key][0] = bus.get("servicio", "")

        data[key][1]["patente"] = bus.get("ppubus1")
        data[key][1]["distancia"] = bus.get("distanciabus1")
        data[key][1]["tiempo"] = bus.get("horaprediccionbus1")

        data[key][2]["patente"] = bus.get("ppubus2")
        data[key][2]["distancia"] = bus.get("distanciabus2")
        data[key][2]["tiempo"] = bus.get("horaprediccionbus2")

    return data


def main():
    gc.collect()
    wlan = conectar_wifi(WIFI_SSID, WIFI_PASSWORD)

    print("mem libre antes de HTTPS:", gc.mem_free())

    raw_data = get_paradero(CODSIMT)

    print("RAW:")
    print(raw_data)

    data = fill_data(raw_data)

    print("DATA:")
    print(data)

    return data


print(main())

