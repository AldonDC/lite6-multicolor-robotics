# Lite 6 Control Engine: Pro Interface 🦾

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyQt6-UI_Framework-green?style=for-the-badge&logo=qt&logoColor=white" alt="PyQt6">
  <img src="https://img.shields.io/badge/OpenCV-Computer_Vision-red?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/Status-Production_Ready-success?style=for-the-badge" alt="Status">
</div>

---

## Visión General del Sistema
La **Lite 6 Control Engine** es una interfaz gráfica de usuario (GUI) de grado industrial diseñada específicamente para la operación colaborativa del robot **UFactory Lite 6**. Desarrollada bajo los lineamientos del bloque integrador, esta plataforma unifica la manipulación cinemática, el procesamiento de trayectorias vectoriales (G-Code) y rutinas de visión artificial en un único entorno de trabajo cohesivo y seguro.

## Arquitectura de Software Integrada
El sistema está dividido en cuatro módulos principales que responden a los requerimientos del proyecto:

1. **Manipulación Espacial Cartesian y Anti-Colisión:**
   - Control directo del *end-effector* mediante coordenadas espaciales (X, Y, Z).
   - Motor de validación de seguridad implementado en el backend que previene cinemáticamente daños a la superficie de trabajo o la base del robot.
2. **Síntesis Geométrica Paramétrica:**
   - Resolutores preconfigurados para trazar trayectorias estandarizadas de alta precisión:
     - Cuadrado exacto de $5\text{ cm} \times 5\text{ cm}$.
     - Triángulo equilátero con longitud de arista de $5\text{ cm}$.
     - Círculo perfecto de $5\text{ cm}$ de diámetro.
3. **Motor Intérprete Numérico (G-Code):**
   - Módulo de carga y *parsing* de trayectorias complejas (`.ngc`). El usuario suministra el vector de diseño y el sistema escala y genera un patrón seguro ajustado al envolvente de trabajo del Lite 6.
4. **Visión Artificial Estocástica:**
   - Detección de patrones en tiempo real alimentado por OpenCV.
   - Algoritmo de reconocimiento morfológico: Independientemente de cómo se sitúen las impresiones en el plano de trabajo, el robot forzará una secuencia de abordaje heurística estricta: **Triángulo $\rightarrow$ Cuadrado $\rightarrow$ Círculo**.

## Despliegue y Ejecución

**1. Instalar Dependencias del Entorno:**
Asegúrese de contar con los módulos gráficos y de visión requeridos para la ejecución.
```bash
pip install PyQt6 PyQt6-QtSvg opencv-python numpy
```

**2. Ejecutar la Plataforma Base:**
Desde la raíz de este directorio (`interfaz_cobot`), inicialice el *engine* principal:
```bash
python3 main_ui.py
```
> ⚠️ **Nota de Conectividad:** La interfaz está apuntando a la dirección IP estática local `192.168.1.164`. Para operar en hardware físico, garantice que el panel de control del robot se encuentre en dicha subred.

## 📋 Entregables Pendientes (Checklist de Proyecto)
Para finalizar la etapa de validación de este módulo, el equipo debe consolidar los siguientes artefactos de evaluación:

### 1. Elementos Operativos
- [ ] **Archivos de Trayectoria NC (`.ngc`)**: Almacenar en esta estructura el diseño o patrón vectorial a dibujar. El usuario entrega la trayectoria del archivo y el robot debe generar el trazo señalado (Requerimiento 3).
- [ ] **Evidencia Audiovisual de Visión y Geometría**: Entregar video comprobando las funcionalidades:
  - Dibujo físico sobre papel de: Cuadrado ($5\text{ cm}$), Triángulo equilátero ($5\text{ cm}$) y Círculo ($5\text{ cm}$ de diámetro).
  - Reconocimiento de cámara: Usuario imprime las 3 figuras. El robot debe posicionarse sobre Triángulo $\rightarrow$ Cuadrado $\rightarrow$ Círculo, demostrando robustez incluso si cambian las ubicaciones.

### 2. Documentación (WIKI del Módulo 1)
Deberá entregarse una WIKI en el mismo repositorio que el reporte del Módulo 1. La documentación requerida estrictamente es la siguiente:
- [ ] **Documentar el diseño de la interfaz:** Explicación técnica de la conceptualización de la UI, flujos de usuario y arquitectura gráfica (`main_ui.py` y `styles.qss`).
- [ ] **Documentar el código de la interfaz:** Desglose del ciclo de vida de PyQt6, manejo de *Threads* para la cámara en tiempo real e interacciones asíncronas del SDK de xArm.
- [ ] **Documentar las funciones de servicio:** Explicación detallada de los *callbacks* que dan servicio a las peticiones del bloque:
  1. *Manipulación 3D*: Explicación de la función `move_to` y la evaluación lógica *anti-colisión* de la trayectoria (flechas/coordenadas).
  2. *Geometría*: Explicación geométrica detrás de `draw_square`, `draw_triangle` y `draw_circle`.
  3. *Motor G-Code*: Lógica de la función `run_gcode` para mapear el archivo y generar la trayectoria.
  4. *Visión Robótica*: Flujo de la función `run_vision_sequence` acoplada al `VisionEngine` y ciclo ordenado de posiciones (Triángulo $\rightarrow$ Cuadrado $\rightarrow$ Círculo).

---
**Desarrollado en Tec de Monterrey [Robotics Intelligence]**
Link para el video de youtube: https://youtu.be/TVq4lMy1ARM
