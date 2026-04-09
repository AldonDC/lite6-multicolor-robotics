"""
Proyecto: Google Logo Multicolor con xArm (Versión con Escala)
Archivo: colors-draw.py
"""

import os
import sys
import time
import re

# Cargamos el SDK
sys.path.append(os.path.join(os.path.dirname(__file__), 'xArm-Python-SDK'))
from xarm.wrapper import XArmAPI

# --- CONFIGURACIÓN DE TUS ARCHIVOS ---
archivos_multicolor = [
    {"archivo": "azul_0001.gnc", "color": "AZUL"},
    {"archivo": "rojo_0001.gnc", "color": "ROJO"},
    {"archivo": "verde_0001.gnc", "color": "VERDE"}
]

# --- POSICIÓN MANUAL Y ESCALA ---
X_BASE = 95.6
Y_BASE = 321.1
Z_UP   = 150.0 # Altura de seguridad inicial (más margen para plumones)
ESCALA = 0.5  # <--- AJUSTADO para 10x10 cm 
ROLL   = -178.9
PITCH  = 3.5
YAW    = 112.2

# --- CONFIGURACIÓN DE IP ---
if len(sys.argv) >= 2:
    ip = sys.argv[1]
else:
    ip = input('Por favor, ingresa la IP de tu xArm: ')

# Inicialización
arm = XArmAPI(ip)
print("Limpiando errores previos...")
arm.clean_error()
arm.motion_enable(enable=True)
arm.set_mode(0)
arm.set_state(state=0)

def limpiar_robot():
    """Función de utilidad para desbloquear el robot si hay errores."""
    code = arm.get_err_warn_code()[0]
    if code != 0 or arm.state == 4:
        print(f"⚠️ Detectado error {code} o estado bloqueado. Limpiando...")
        arm.clean_error()
        arm.motion_enable(enable=True)
        arm.set_mode(0)
        arm.set_state(0)
        time.sleep(1)

limpiar_robot()

print(f"\n🚀 INICIANDO PROYECTO (Escala: {ESCALA * 100}%) 🚀")

# --- LOOP PARA DIBUJAR CADA COLOR ---
for item in archivos_multicolor:
    path = os.path.join("/home/alfonso/Documents/8 Semestre/last_bloque/", item["archivo"])
    
    if not os.path.exists(path):
        print(f"\n⚠️ Saltando {item['archivo']}: No se encontró el archivo.")
        continue

    # 1. POSICIONAR PARA CAMBIO
    print(f"\n🎨 COLOR: {item['color']}")
    limpiar_robot()
    arm.set_position(x=X_BASE, y=Y_BASE, z=Z_UP, roll=ROLL, pitch=PITCH, yaw=YAW, 
                     speed=100, wait=True, is_radian=False)
    
    while input(f">>> Pon el plumón {item['color']}, escribe 'a' y dale Enter: ").lower() != "a":
        pass

    # --- AJUSTE INTERACTIVO DE ALTURA ---
    print(f"\n🎮 Ajuste de altura para {item['color']}:")
    print("Controles: 'a' + Enter (Subir 1mm) | 'd' + Enter (Bajar 1mm) | Solo Enter (Confirmar)")
    
    # Empezamos desde la altura de seguridad actual
    _, pos = arm.get_position(is_radian=False)
    temp_z = pos[2]

    while True:
        comando = input(f"   [Z actual: {temp_z:.1f}mm] Mover (a/d) o Confirmar (Enter): ").lower()
        
        if comando == 'a':
            temp_z += 1.5
        elif comando == 'd':
            temp_z -= 1.5
        elif comando == '':
            current_z_draw = temp_z
            print(f"✅ Altura confirmada: {current_z_draw}mm")
            break
        else:
            print("⚠️ Usa 'a', 'd' o Enter.")
            continue
            
        limpiar_robot()
        arm.set_position(x=X_BASE, y=Y_BASE, z=temp_z, roll=ROLL, pitch=PITCH, yaw=YAW, 
                         speed=20, wait=True, is_radian=False)

    print(f"🚀 Dibujando {item['archivo']}...")

    curr_x = 0.0
    curr_y = 0.0
    cont = 0

    with open(path) as gcode:
        for line in gcode:
            line = line.strip()
            
            found_x = re.search(r'X([-+]?\d*\.\d+|\d+)', line)
            found_y = re.search(r'Y([-+]?\d*\.\d+|\d+)', line)
            
            if found_x or found_y:
                if found_x: curr_x = float(found_x.group(1))
                if found_y: curr_y = float(found_y.group(1))
                
                # APLICAMOS ESCALA A LOS VALORES DEL G-CODE
                scaled_x = curr_x * ESCALA
                scaled_y = curr_y * ESCALA
                
                # Calculamos posición real restando de la base
                real_x = X_BASE - scaled_x
                real_y = Y_BASE - scaled_y
                
                code = arm.set_position(x=real_x, y=real_y, z=current_z_draw, 
                                        roll=ROLL, pitch=PITCH, yaw=YAW, 
                                        speed=50, wait=True, is_radian=False)
                
                if code != 0:
                    print(f"⚠️ Aviso Red {code}. Limpiando...")
                    arm.clean_error()
                    arm.set_state(0)
                
                cont += 1
                if cont % 50 == 0: print(f"[{item['color']}] Trazo {cont}...")

    # Levantamos al terminar el color (Usando la última posición escalada)
    arm.set_position(x=X_BASE - (curr_x * ESCALA), y=Y_BASE - (curr_y * ESCALA), z=Z_UP, 
                     roll=ROLL, pitch=PITCH, yaw=YAW, speed=100, wait=True)
    print(f"✅ {item['color']} terminado.")

# --- SALIDA FINAL ---
print("\n🎉 ¡PROYECTO COMPLETADO! 🎉")
arm.set_position(x=X_BASE, y=Y_BASE, z=Z_UP + 30, roll=ROLL, pitch=PITCH, yaw=YAW, speed=100, wait=True)
arm.disconnect()
