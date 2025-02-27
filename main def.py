from teclado import Tecladox
from lcd import LCD
from machine import Pin, ADC, DAC
import time

# Configuración del teclado matricial 
teclas = [["1", "2", "3", "A"],
          ["4", "5", "6", "B"],
          ["7", "8", "9", "C"],
          ["*", "0", "#", "D"]]
filas = [14, 27, 26, 13]
columnas = [33, 32, 35, 12]
teclado = Tecladox(filas, columnas, teclas)

#  Configuración del LCD 
modo = 4
rs_pin = 15
e_pin = 2
data_pins = [5, 18, 19, 21]
lcd = LCD(mode=modo)
lcd.SetPines(rs_pin, e_pin, data_pins)
lcd.Iniciar()

#  Configuración de ADC y DAC 
adc = ADC(Pin(34))         # Entrada analógica del ESP32
adc.atten(ADC.ATTN_11DB)     # Rango configurado a 11 dB (0 - 3.9V)
adc.width(ADC.WIDTH_12BIT)   # Resolución: 0-4095
dac = DAC(Pin(25))         # Salida analógica del ESP32

#  Bucle principal 
velocidad_deseada = ""
rpm = 0
lcd.Clear()
lcd.Print("RPM Obj:", fil=0, col=0)
lcd.Print("RPM Real:", fil=1, col=0)

# Filtro de suavizado para el RPM real
def suavizar_rpm(nuevo_rpm, rpm_suavizado, factor=0.2):
    return (factor * nuevo_rpm) + ((1 - factor) * rpm_suavizado)

rpm_suavizado = 0

# Controlador PI con feedforward.
Kp = 0.4   # Ganancia proporcional ajustada
Ki = 0.15  # Ganancia integral ajustada
integral = 0

# Factor de calibración para la conversión ADC->RPM.
# Si al establecer 1500 RPM ideales las reales son 1000, prueba con cal_factor=1.5.
cal_factor = 1.5

while True:
    teclado.leer_teclas()
    if teclado.nueva_tecla_detectada:
        tecla = teclado.numeros_presionados[-1] if teclado.numeros_presionados else None
        print(f"Tecla detectada: {tecla}")
        if tecla == "#":
            if velocidad_deseada.isdigit():
                rpm = min(max(int(velocidad_deseada), 0), 2000)
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
            nueva_velocidad = int(velocidad_deseada + tecla)
            if nueva_velocidad <= 2000:
                velocidad_deseada += tecla
                print(f"Velocidad deseada actual: {velocidad_deseada}")
                lcd.Clear()
                lcd.Print(f"RPM Obj: {velocidad_deseada}", fil=0, col=0)
    # Limpiar la lista de teclas presionadas para evitar acumulación
    teclado.numeros_presionados = []

    # Lectura y conversión del ADC: 3.9 V -> 2000 RPM, con factor de calibración
    voltaje_adc = adc.read() * (3.9 / 4095)
    rpm_real = min(max(((voltaje_adc / 3.9) * 2000 * cal_factor), 0), 2000)
    rpm_suavizado = suavizar_rpm(rpm_real, rpm_suavizado)
    print(f"Voltaje ADC: {voltaje_adc:.2f} V, RPM Real Suavizado: {int(rpm_suavizado)}")

    # Término de feedforward: valor DAC base para alcanzar la RPM deseada
    DAC_ff = (rpm / 2000) * 255

    # Controlador PI: corrige la diferencia entre la RPM deseada y las reales
    error = rpm - rpm_suavizado
    integral = max(min(integral + error * 0.3, 255), -255)  # Anti-windup
    DAC_PI = (Kp * error) + (Ki * integral)
    
    # Valor final para el DAC: feedforward + corrección PI
    DAC_val = DAC_ff + DAC_PI
    DAC_val = int(min(max(DAC_val, 0), 255))
    
    dac.write(DAC_val)
    print(f"RPM Objetivo: {rpm}, DAC enviado: {DAC_val} (0-255)"),

    lcd.Print(f"RPM Real: {int(rpm_suavizado)}", fil=1, col=0)
    time.sleep(0.3)