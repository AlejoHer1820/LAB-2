from machine import Pin
import time

class Tecladox:
    def __init__(self, filas, columnas, teclas):
        self.filas = filas
        self.columnas = columnas
        self.teclas = teclas
        self.tecla_arriba = 0
        self.tecla_abajo = 1
        
        #inicializar pines
        self.pines_filas = [Pin(pin_nombre, mode=Pin.OUT) for pin_nombre in filas]
        self.pines_columnas = [Pin(pin_nombre, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_nombre in columnas]
    
        #lista para almacenar los números precionadas
        self.numeros_presionados = []
        self.nueva_tecla_detectada = False
        
    def escaner(self, fila, columna):
        """ESCANEO DE TECLADO"""
        self.pines_filas[fila].value(1) #activa la fila
        key = None
        if self.pines_columnas[columna].value() == self.tecla_abajo:
            key = self.teclas[fila][columna] #si la tecla esta presionada, devuelve el valor
        self.pines_filas[fila].value(0) #desactivar la fila
        return key
    
    def leer_teclas(self):
        """leer las teclas presionadas"""
        self.nueva_tecla_detectada = False #reicia la bandera
        for fila in range (4):
            for columna in range (4):
                tecla = self.escaner(fila, columna)
                if tecla is not None:
                    print(f"Tecla presionada : {tecla}")
                    self.numeros_presionados.append(tecla)
                    self.nueva_tecla_detectada = True #registra que hubo un cambio
                    time.sleep(0.3) #espera para evitar multiples lecturas de la misma tecla
    
    def get_numeros_presionados(self):
        """obtener los numeros presionados hasta ahora"""
        return ''.join(self.numeros_presionados)