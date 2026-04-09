"""
Proyecto: Dibujo con xArm - Versión Personalizada de La Liga
"""

import os
import sys
import time
import re

# Cargamos el SDK (ajusta la ruta según tu carpeta)
sys.path.append(os.path.join(os.path.dirname(__file__), 'xArm-Python-SDK'))
from xarm.wrapper import XArmAPI

# --- CONFIGURACIÓN DE IP (Tu versión personalizada) ---
if len(sys.argv) >= 2:
    ip = sys.argv[1]
else:
    try:
        from configparser import ConfigParser
        parser = ConfigParser()
        parser.read('../robot.conf')
        ip = parser.get('xArm', 'ip')
    except:
        ip = input('Por favor, ingresa la IP de tu xArm: ')
        if not ip:
            print('Error de IP, saliendo...')
            sys.exit(1)

# Inicializamos el brazo y sus estados básicos
arm = XArmAPI(ip)
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)

# El brazo regresa a casa para limpiar el área
arm.move_gohome(wait=True)

# Movimientos de seguridad iniciales para no chocar al acercarnos a la mesa
arm.set_position(x=100, y=-50, z=250, roll=180, pitch=0, yaw=0, speed=100, wait=True)
arm.set_position(x=-44, y=-170, z=250, roll=180, pitch=0, yaw=0, speed=100, wait=True)

# Pausa manual para acomodar la hoja antes de empezar
prompt = 's'
print("\n>>> Escribe 'a' y dale Enter cuando estés listo para dibujar:")
while prompt != "a":
    prompt = input()

# --- CARGAMOS TU ARCHIVO G-CODE ---
gcode_path = "/home/alfonso/Documents/8 Semestre/last_bloque/xArm-Python-SDK/example/wrapper/common/laliga_drawing_0001.ngc"

if not os.path.exists(gcode_path):
    print(f"Error: No se encuentra {gcode_path}")
    sys.exit(1)

with open(gcode_path, 'r') as fp:
    lines = sum(1 for line in fp)
    print('Total de coordenadas a procesar:', lines)

start_time = time.time()
cont = 0

# Leemos el archivo línea por línea (Siguiendo la estructura original)
with open(gcode_path) as gcode:
    for line in gcode:
        line = line.strip()
        # Buscamos X e Y en el texto usando un patrón de Regex
        coord = re.findall(r'[XY].?\d+.\d+', line)
        
        if coord:
            # Separamos los valores numéricos de las letras X e Y (usamos split)
            xx = coord[0].split('X')[1]
            yy = coord[1].split('Y')[1]
            
            # --- LÓGICA DE COMPENSACIÓN Z (Mejora de trazado) ---
            # Si el brazo está muy atrás (Y > 150), usamos una altura Z mayor
            if float(yy) > 150:
                z_value = 210
            # Si está en la zona media o cercana, bajamos un poco la altura Z
            elif float(yy) > 50:
                z_value = 208.5
            else:
                z_value = 208.5
            
            # Ejecutamos el movimiento lineal con los offsets definidos para la mesa
            arm.set_position(x=-44 - float(xx), y=-228 - float(yy), z=z_value, 
                             roll=180, pitch=0, yaw=0, speed=100, wait=True)
            
            # Contador de progreso para el usuario
            cont += 1
            if cont % 100 == 0:
                print(f"Líneas procesadas: {cont} de {lines}. Restan: {lines-cont}")

# --- RUTINA FINAL DE SALIDA (Tus 3 líneas extra de seguridad) ---
print(f"\n¡Dibujo terminado en {time.time() - start_time:.1f} segundos!")
arm.set_position(z=250, roll=180, pitch=0, yaw=0, speed=100, wait=True) # Elevación segura
arm.set_position(x=-44, y=-335, z=250, roll=180, pitch=0, yaw=0, speed=100, wait=True) # Retira atrás
arm.move_gohome(wait=True) # Home final y desconexión

arm.disconnect()
