import network      # Para la conexión Wi-Fi
import urequests    # Para hacer solicitudes HTTP
import time         # Para pausas
import ujson
from machine import Pin, I2C
import ssd1306
# ¡IMPORTANTE! Para trabajar con JSON

# --- Configuración Wi-Fi ---
# !!! REEMPLAZA CON TUS CREDENCIALES !!!
WIFI_SSID = "MiMac_visita"
WIFI_PASSWORD = "visita.vip"
# --------------------------

# --- URL del API ---
API_URL = "https://api.xor.cl/red/bus-stop/PC837"
# -----------------
error = ["Connection Error"]

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
oled.fill(0)

# --- Función para conectar a Wi-Fi ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF) # Interfaz de estación (cliente)
    wlan.active(True) # Activa la interfaz

    if not wlan.isconnected():
        print('Conectando a la red Wi-Fi...')
        wlan.connect(ssid, password)

        # Espera hasta que la conexión se establezca o falle
        max_wait = 15 # segundos
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3: # 3 = CONECTADO
                break
            max_wait -= 1
            print('.', end='') # Imprime puntos en la misma línea
            time.sleep(1)
        print() # Salto de línea después de los puntos

    # Verifica el estado final de la conexión
    if wlan.status() != 3:
        print('¡Error al conectar a Wi-Fi!')
        print('Status code:', wlan.status())
        return None # Retorna None si falla la conexión
    else:
        print('¡Conectado a Wi-Fi!')
        status = wlan.ifconfig() # Obtiene la configuración IP
        print('IP:', status[0])
        return wlan # Retorna el objeto wlan si la conexión es exitosa

# --- Función para procesar la respuesta ---
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
    wlan = connect_wifi(WIFI_SSID, WIFI_PASSWORD)

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

def refactor_data(response):
    info = []
    services = response.get("services", None)
    for bus_type in services:
        bus_dict = {}
        bus_dict["id"] = bus_type["id"]
        
        buses = bus_type.get("buses", None)
        bus_list = []
        if buses:
            for bus in buses:
                bus_attrb = {"id" : "id", "meters_distance" : "m", "max_arrival_time" : "t_max", "min_arrival_time" : "t_min"}
                bus_info = {}
                for old_attrb, new_attrb in bus_attrb.items():
                    bus_info[new_attrb] = bus[old_attrb]
                    
                bus_list.append(bus_info)
                bus_dict["buses"] = bus_list
            
        
        info.append(bus_dict)
    return info
    
def prep_data(data, micro):
    title = [f"------{micro.upper()}-------", 2, 0]
    bus1 = [[2, 11],[ 2, 21]]
    bus2 = [[2, 43,],[2, 54]]
    buses = [bus1, bus2]
    
    for element in data:
        print(element["id"], micro)
        if element["id"] == micro:
            global directory
            directory = data[data.index(element)]
            
    print(directory)
    length = len(directory["buses"])
    index = 0
    for bus in directory["buses"]:
        if index > 1:
            break
        print(buses[index][0])
        current_bus = buses[directory["buses"].index(bus)]
        buses[index][0].insert(0, directory["buses"][index]["m"])
        buses[index][0].insert(0, directory["buses"][index]["id"])
        buses[index][1].insert(0, directory["buses"][index]["t_max"])
        buses[index][1].insert(0, directory["buses"][index]["t_min"])
        
        index += 1
    return buses, title
        
def show_data(data, micro):
    
    buses, title = prep_data(data, micro)
    print(buses)
    oled.text(*title)
    if buses:
        oled.text(f"{buses[0][0][0]} : {buses[0][0][1]}", buses[0][0][2], buses[0][0][3])
        oled.text(f"min:{buses[0][1][0]} ; max:{buses[0][1][1]}", buses[0][1][2], buses[0][1][3])
        if buses[1]:
            oled.text("- - - - - - - - - - - - ", 2, 32)
            oled.text(f"{buses[1][0][0]} : {buses[1][0][1]}", buses[1][0][2], buses[1][0][3])
            oled.text(f"min:{buses[1][1][0]} ; max:{buses[1][1][1]}", buses[1][1][2], buses[1][1][3])
        oled.show()
    
    
        
    
def C27(data):
    show_data(data, "C27")
    
def C09(data):
    pass

def C09c(data):
    pass
    
def main():
    response = api_call()
    info = refactor_data(response)
    print(info)
    C27(info)


# --- Ejecutar la función principal ---
if __name__ == "__main__":
    main()