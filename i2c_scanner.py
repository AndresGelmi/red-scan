from machine import Pin, I2C
import ssd1306

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

print("I2C devices:", i2c.scan())   # debería salir [0x3c] o [0x3d]

oled = ssd1306.SSD1306_I2C(128, 64, i2c)  # o 128x32 según tu pantalla
oled.fill(0)
oled.text("Hola ESP32!", 0, 0)
oled.show()
