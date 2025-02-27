from machine import Pin
import time

class LCD:
    def __init__(self, mode=8):
        """
        Inicializa el LCD. Por defecto usa modo de 8 bits.
        :param mode: 8 para 8 pines o 4 para 4 pines.
        """
        self.mode = mode
        self.rs = None
        self.e = None
        self.data_pins = []

    def SetPines(self, rs_pin, e_pin, data_pins):
        """
        Configura los pines del LCD.
        :param rs_pin: Pin RS
        :param e_pin: Pin Enable
        :param data_pins: Lista de pines de datos (4 o 8 pines)
        """
        self.rs = Pin(rs_pin, Pin.OUT)
        self.e = Pin(e_pin, Pin.OUT)
        self.e.value(0)
        self.rs.value(0)
        self.data_pins = [Pin(pin, Pin.OUT) for pin in data_pins]

    def _pulse_enable(self):
        """Genera un pulso en el pin Enable."""
        time.sleep_us(10)
        self.e.value(1)
        time.sleep_us(50)
        self.e.value(0)
        time.sleep_us(10)

    def _send_data(self, data, rs_value):
        """
        Envía datos o comandos al LCD.
        :param data: El dato o comando (8 bits).
        :param rs_value: 0 para comando, 1 para datos.
        """
        self.rs.value(rs_value)
        if self.mode == 8:
            # Modo 8 bits: enviar directamente los 8 bits
            for i in range(8):
                self.data_pins[i].value((data >> i) & 0x01)
            self._pulse_enable()
        elif self.mode == 4:
            # Modo 4 bits: enviar primero los 4 bits altos, luego los 4 bits bajos
            for i in range(4):
                self.data_pins[i].value((data >> (i + 4)) & 0x01)  # Bits altos
            self._pulse_enable()
            for i in range(4):
                self.data_pins[i].value((data >> i) & 0x01)  # Bits bajos
            self._pulse_enable()

    def comando(self, command):
        """Envía un comando al LCD."""
        self._send_data(command, 0)

    def dato(self, data):
        """Envía un dato al LCD."""
        self._send_data(data, 1)

    def Iniciar(self):
        """Inicializa el LCD."""
        time.sleep(0.04)
        if self.mode == 4:
            self.comando(0x02)  # Configurar para 4 bits
            self.comando(0x28)  # Modo 4 bits, 2 líneas
        elif self.mode == 8:
            self.comando(0x30)  # Modo 8 bits, 2 líneas
            self.comando(0x38)
        self.comando(0x06)  # Configurar cursor
        self.comando(0x0C)  # Encender pantalla
        self.comando(0x01)  # Limpiar pantalla
        time.sleep(0.005)

    def Clear(self):
        """Limpia la pantalla."""
        self.comando(0x01)
        time.sleep(0.002)

    def Home(self):
        """Lleva el cursor a la posición inicial."""
        self.comando(0x02)
        time.sleep(0.002)

    def DireccionDD(self, dire):
        """Cambia la dirección de la memoria de datos (DDRAM)."""
        self.comando(0x80 | (dire & 0x7F))

    def Print(self, text, fil=0, col=0):
        """
        Imprime texto en la pantalla.
        :param text: Texto a imprimir.
        :param fil: Fila (0, 1, 2, 3).
        :param col: Columna (0-39).
        """
        if fil == 1:
            self.DireccionDD(0x40 + col)
        elif fil == 2:
            self.DireccionDD(0x14 + col)
        elif fil == 3:
            self.DireccionDD(0x54 + col)
        elif fil == 0:
            self.DireccionDD(0x00 + col)
        for char in text:
            self.dato(ord(char))