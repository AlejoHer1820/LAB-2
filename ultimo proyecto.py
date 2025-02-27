from teclado import Tecladox
from lcd import LCD
from machine import Pin, ADC, DAC
import time

# --- Configuración del teclado matricial ---
teclas = [["1", "2", "3", "A"],
          ["4", "5", "6", "B"],
          ["7", "8", "9", "C"],
          ["*", "0", "#", "D"]]
filas = [14, 27, 26, 13]
columnas = [33, 32, 35, 12]
teclado = Tecladox(filas, columnas, teclas)

# --- Configuración del LCD de 2 líneas ---
modo = 4
rs_pin = 15
e_pin = 2
data_pins = [5, 18, 19, 21]
lcd = LCD(mode=modo)
lcd.SetPines(rs_pin, e_pin, data_pins)
lcd.Iniciar()

# --- Configuración de ADC y DAC ---
adc = ADC(Pin(34))         # Entrada analógica del ESP32
adc.atten(ADC.ATTN_11DB)   # Rango configurado a 11 dB (~0 - 3.9V)
adc.width(ADC.WIDTH_12BIT) # Resolución: 0-4095
dac = DAC(Pin(25))         # Salida analógica del ESP32

# --- Bucle principal ---
velocidad_deseada = ""
rpm = 0
lcd.Clear()
lcd.Print("RPM Obj:", fil=0, col=0)
lcd.Print("RPM Real:", fil=1, col=0)

# Mapeo DAC a RPM (Tabla mejorada con mayor granularidad)
dac_rpm_data = [
    (255, 4500, 5000),
    (220, 4000, 4500),
    (200, 3500, 4000),
    (180, 3000, 3500),
    (160, 2500, 3000),
    (140, 2000, 2500),
    (120, 1500, 2000),
    (100, 1000, 1500),
    (80, 500, 1000),
    (50, 200, 500),
    (30, 50, 200),
    (0, 0, 50)
]

# Obtener el valor DAC basado en el RPM deseado
def get_dac_value(target_rpm):
    closest_dac = 0
    min_distance = float('inf')
    for dac, min_rpm, max_rpm in dac_rpm_data:
        if min_rpm <= target_rpm <= max_rpm:
            return dac
        distance = min(abs(target_rpm - min_rpm), abs(target_rpm - max_rpm))
        if distance < min_distance:
            min_distance = distance
            closest_dac = dac
    return closest_dac

# Filtro de suavizado para el RPM real
def suavizar_rpm(nuevo_rpm, rpm_suavizado, factor=0.2):
    return (factor * nuevo_rpm) + ((1 - factor) * rpm_suavizado)

rpm_suavizado = 0

# Control proporcional suave
Kp = 0.1

while True:
    teclado.leer_teclas()
    if teclado.nueva_tecla_detectada:
        tecla = teclado.numeros_presionados[-1] if teclado.numeros_presionados else None
        print(f"Tecla detectada: {tecla}")
        if tecla == "#":
            if velocidad_deseada.isdigit():
                rpm = min(max(int(velocidad_deseada), 0), 5000)
                print(f"Velocidad deseada confirmada: {rpm} RPM")
                lcd.Clear()
                lcd.Print(f"RPM Obj: {rpm}", fil=0, col=0)
            else:
                print("Error: La velocidad deseada no es un número válido.")
            velocidad_deseada = ""
        elif tecla == "*":
            velocidad_deseada = ""
            rpm = 0
            lcd.Clear()
            lcd.Print("RPM Obj:", fil=0, col=0)
        elif tecla and tecla.isdigit():
            velocidad_deseada += tecla
            print(f"Velocidad deseada actual: {velocidad_deseada}")
            lcd.Clear()
            lcd.Print(f"RPM Obj: {velocidad_deseada}", fil=0, col=0)

    voltaje_adc = adc.read() * (3.9 / 4095)
    rpm_real = min(max((voltaje_adc / 1.1) * 5000, 0), 5000)
    rpm_suavizado = suavizar_rpm(rpm_real, rpm_suavizado)
    print(f"Voltaje ADC: {voltaje_adc:.2f} V, RPM Real Suavizado: {int(rpm_suavizado)}")

    error = rpm - rpm_suavizado
    dac_value = int(max(min(Kp * error, 255), 0))

    dac.write(dac_value)
    print(f"RPM Objetivo: {rpm}, DAC enviado: {dac_value} (0-255)")

    lcd.Print(f"RPM Real: {int(rpm_suavizado)}", fil=1, col=0)
    time.sleep(0.3)

