# Reporte Técnico: Robótica Reconfigurable, Colaborativa y Control Cinemático con Lite 6

---

## Tabla de Contenidos

1. [Introducción y Fundamentos Teóricos](#1-introducción-y-fundamentos-teóricos)
2. [Análisis de Robots Colaborativos en la Industria](#2-análisis-de-robots-colaborativos-en-la-industria)
3. [Diseño del Experimento: Metodología y Control](#3-diseño-del-experimento-metodología-y-control)
4. [Flujo de Software: De Inkscape a Trayectorias Reales](#4-flujo-de-software-de-inkscape-a-trayectorias-reales)
5. [Resultados: Ejecución del Trazado Multicolor](#5-resultados-ejecución-del-trazado-multicolor)
6. [Conclusiones Técnicas y Futuras Aplicaciones](#6-conclusiones-técnicas-y-futuras-aplicaciones)
7. [Referencias Bibliográficas](#7-referencias-bibliográficas)

---

## 1. Introducción y Fundamentos Teóricos

### 1.1 Robots Reconfigurables (SMR)

Los robots reconfigurables poseen la capacidad de alterar su morfología para adaptarse a tareas dinámicas. Se clasifican principalmente en arquitecturas de **celosía (lattice)** y de **cadena (chain)**.

* **Alcances Actuales:** Exploración en entornos extremos (espacio y volcanes) y manufactura modular.
* **Costos de Mercado:** Los prototipos de investigación como el *SuperBot* pueden costar desde **$5,000 USD por módulo**. Sistemas industriales robustos superan los **$60,000 USD**.

### 1.2 El Auge de la Robótica Colaborativa (Cobots)

Los cobots están diseñados para operar de forma segura junto a seres humanos mediante el cumplimiento de normativas estrictas como la **ISO/TS 15066**.

---

## 2. Análisis de Robots Colaborativos en la Industria

### 2.1 Comparativa de Modelos y Precios

| Modelo                          | Especialidad                  | Precio Estimado | Modos de Operación                   |
| :------------------------------ | :---------------------------- | :-------------- | :------------------------------------ |
| **UFactory Lite 6**       | Educación e Industria Ligera | $3,000 USD      | API Python / Guía por bloques        |
| **Universal Robots UR5e** | Manufactura y Ensamblaje      | $35,000 USD     | Polyscope / Scripting industrial      |
| **Franka Emika Panda**    | Investigación y Sensibilidad | $30,000 USD     | Control de torque por canal de fuerza |

### 2.2 Herramientas y Efectores Finales (EOAT)

El Lite 6 permite el uso de diversos efectores:

1. **Grippers Eléctricos:** Para tareas de ensamble electrónico.
2. **Ventosas de vacío:** Para procesos de empaquetado (Pick & Place).
3. **Soportes Personalizados:** Como el utilizado en este experimento para el trazado artístico.

---

## 3. Diseño del Experimento: Metodología y Control

### 3.1 Arquitectura de Comunicación

El control del Lite 6 se establece mediante un protocolo **TCP/IP** sobre una conexión Ethernet de 100 Mbps.

* **Software:** Utilización de la librería `xarm-python-sdk`.
* **Modo de Control:** Control de posición cartesiana (Modo 0), optimizado para trayectorias de precisión milimétrica.

### 3.2 Calibración de la Herramienta (Tool Calibration)

La precisión del dibujo depende críticamente de la definición del eje $Z$.

* **Punto de Contacto:** Se definió el plano de dibujo como $Z=0$ relativo al sistema de coordenadas de usuario.
* **Comentario Personal:** La mayor dificultad radicó en que cada plumón físico posee una holgura distinta en la punta. Solucionamos esto implementando una pausa interactiva en el código para permitir el ajuste manual de altura antes de cada capa de color.

---

## 4. Flujo de Software: De Inkscape a Trayectorias Reales

### 4.1 Segmentación de Capas (Layers)

En **Inkscape**, el diseño se dividió estrictamente por capas cromáticas:

* **Capa 01:** Trazo base (Color 1).
* **Capa 02:** Detalles internos (Color 2).
* **Capa 03:** Contornos de contraste (Color 3).

### 4.2 Lógica del Intérprete de G-code

El script desarrollado abre los archivos `.ngc`, filtra las secuencias `G1` y las transforma en comandos ejecutables por el robot:

```python
# Lógica master de cambio de color
for archivo in lista_gcode:
    preparar_robot()
    ejecutar_movimiento(archivo)
    retraer_brazo_seguridad()
    pausa_manual() # Cambio de color físico
```

---

## 5. Resultados: Ejecución del Trazado Multicolor

### 5.1 Composición Cromática Final

Se logró una integración visual de tres colores con un margen de error de solapamiento menor a 0.5 mm.

### 5.2 Galería de Evidencias Técnicas

<p align="center">
  <img src="../assets/images/result_image.jpeg" alt="Resultado de 3 colores" width="450">
  <br>
  <b>Figura 1:</b> Resultado final del trazado multicolor (Rojo, Azul, Verde).
</p>


**Prueba de Validación Física:**
[Reproducir Video de Ejecución del Brazo Robótico](../assets/videos/execution_video.mp4)

---

## 6. Conclusiones Técnicas y Futuras Aplicaciones

### 6.1 Comprensión de la API del Lite 6

La API de Python ofrece una abstracción de alto nivel que facilita el prototipado rápido. Sin embargo, requiere una comprensión profunda de los límites cinemáticos para evitar **puntos de singularidad** donde el robot pierde movilidad.

### 6.2 Gemelos Digitales e Industria 4.0

Los **Gemelos Digitales** (Digital Twins) no son solo simuladores; son modelos que reflejan el estado físico en tiempo real.

1. **Simulación de Ensamblaje:** Permite validar el alcance de los seis ejes antes de mover el hardware real.
2. **Escalamiento Industrial:** Un proceso probado en el gemelo digital del Lite 6 puede migrarse de forma segura a robots de mayor escala en una línea de producción real sin riesgos operativos.

---

## 7. Referencias Bibliográficas

1. **Vicentini, F.** (2021). *Collaborative Robotics: Progress and Possibilities*. IEEE RA Magazine.
2. **Murata, S.** (2012). *Self-reconfigurable Robots: An Introduction*. Springer.
3. **ISO/TS 15066:2016.** *Collaborative robots safety requirements*.
4. **Grieves, M.** (2014). *Digital Twin: Manufacturing Excellence*.
5. **UFactory SDK.** *Open Source xArm Python Documentation*.
