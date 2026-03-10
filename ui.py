from machine import Pin, I2C
import ssd1306
import time

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

print("I2C devices:", i2c.scan())   # debería salir [0x3c] o [0x3d]

oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # o 128x32 según tu pantalla
oled.fill(0)
oled.text("Hola ESP32!", 0, 0)

oled.fill(0)
oled.text("==== PC837 ====", 0,0)
oled.text("CO9: SX-FT56", 0, 10)
oled.text("10-12min, 4667m", 0, 20)
oled.text("---------------", 0, 30)
oled.text("CO9: SX-FT56", 0, 40)
oled.text("10-12min, 4667m", 0, 50)
oled.fill(0)

loading = ""


def load():
    loading = ""
    for i in range (0, 5):
        loading += "."

        oled.text(loading, 48, 32)
        time.sleep(0.5)
        oled.show()
    time.sleep(0.5)
        
while True:
    load()
    oled.fill(0)
    oled.show()
        

oled.show()

