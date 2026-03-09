from machine import Pin, I2C
import ssd1306
import urequests
import network
import time
import ujson

import keys


ssid = keys.WIFI_SSID
password = keys.WIFI_PASSWORD

API_URL = "https://api.xor.cl/red/bus-stop/PC837"
error = ["Connection Error"]

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)

# function that connect to wi-fi
def connect_wifi(ssid, password, timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        print("Already connected:", wlan.ifconfig())
        return wlan

    print("Connecting to Wi-Fi:", ssid)
    wlan.connect(ssid, password)

    t0 = time.time()
    while not wlan.isconnected():
        st = wlan.status()
        # En ESP32: 1001=conectando, 1010=GOT_IP (éxito), 201/202=errores típicos
        if st == network.STAT_WRONG_PASSWORD:
            print("Wrong password (202)")
            return None
        if st == network.STAT_NO_AP_FOUND:
            print("No access point found (201) (note: must be 2.4 GHz)")
            return None

        if time.time() - t0 > timeout_s:
            print("Timeout. status =", st)
            return None

        time.sleep(0.3)

    print("Connected! IP:", wlan.ifconfig()[0], "status:", wlan.status())
    return wlan
    
def on_receive(response_text):
    """
    Procesa el texto de la respuesta JSON, lo convierte en diccionario
    e intenta extraer la información de 'services'.
    """
    print("\n--- Procesando respuesta en on_receive ---")
    try:
        # 1. Convertir el texto JSON en un diccionario Python
        response = ujson.loads(response_text)
        return response
    except ValueError as e:
        # Esto ocurre si response_text no es un JSON válido
        print(f"Error al decodificar JSON: {e}")
        print("El texto recibido no parece ser JSON válido.")
        print("Texto recibido:", response_text) # Muestra lo que se recibió
        print("----------------------------------------")
    except Exception as e:
        # Captura otros posibles errores
        print(f"Ocurrió un error inesperado en on_receive: {e}")
        print("----------------------------------------")


# --- Función principal ---
def api_call():
    # 1. Conectar a Wi-Fi
    wlan = connect_wifi(ssid, password)

    if wlan:
        # Solo procede si la conexión Wi-Fi fue exitosa
        print(f"\nRealizando request a: {API_URL}")
        response = None # Inicializa la variable de respuesta
        try:
            print("Api called")
            # 2. Realizar la solicitud GET
            response = urequests.get(API_URL, timeout=15) # Aumenté un poco el timeout

            # 3. Procesar la respuesta
            print(f"Código de estado HTTP: {response.status_code}")

            if response.status_code == 200:
                # Llama a on_receive pasando el CONTENIDO TEXTUAL de la respuesta
                return on_receive(response.text)
            else:
                print(f"Error en la solicitud: Código {response.status_code}")
                try:
                    print("Contenido del error (si existe):")
                    print(response.text)
                except Exception as e:
                    print(f"No se pudo leer el contenido del error: {e}")

        except Exception as e:
            print(f"Ocurrió un error durante la solicitud HTTP: {e}")

        finally:
            # 4. Cerrar la respuesta (MUY IMPORTANTE para liberar memoria)
            if response:
                response.close()
                print("\nConexión de respuesta cerrada.")

    else:
        return error[0]  
api_call()