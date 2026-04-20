# 📚 Wiki Módulo 1: Diseño e Implementación de Interfaz de Control (Lite 6)

Este documento contiene la fundamentación técnica, el diseño arquitectónico y la documentación a nivel de código de la interfaz gráfica desarrollada para la manipulación y automatización del cobot **UFactory Lite 6**, cumpliendo con los requerimientos del Módulo 1.

---

## 1. Diseño de la Interfaz (UI/UX)

El diseño de la interfaz fue concebido bajo metodologías de jerarquía visual orientadas a entornos industriales (*God-Tier / Aerospace aesthetic*). La meta es ofrecer un entorno seguro, altamente legible y que agrupe las tareas cinemáticas y lógicas en módulos estancos.

### Arquitectura Gráfica
- **Layout Principal:** Estructura clásica tipo *Dashboard* con una barra lateral estática (`Sidebar`) y un contenedor central dinámico (`QStackedWidget`), lo que permite que la interfaz sea escalable en un futuro si se añaden más pestañas de control.
- **HUD y Telemetría:** Se implementó una barra superior persistente para la **Telemetría en tiempo real**. El usuario nunca pierde de vista las coordenadas actuales (X, Y, Z) ni el estado de conexión del robot, crítico para la prevención de accidentes.
- **Sistema de Estilos (QSS):** Se disoció la lógica visual en un archivo independiente `styles.qss`. Presenta un "Dark Mode" de alto contraste (`#05070a`), tarjetas (*Cards*) con efecto translúcido para agrupar controles, e iconografía vectorial pura (SVGs embebidos) garantizando nitidez en cualquier configuración de pantalla.

---

## 💻 2. Documentación del Código de la Interfaz

La aplicación de escritorio se construyó bajo el patrón **Modelo-Vista-Controlador (agrupado)** utilizando la librería `PyQt6` para Python.

### Estructura de *Threading* Asíncrono
Uno de los mayores retos técnicos fue evitar que la interfaz "se congelara" al mandar rutinas pesadas o recibir imágenes de la cámara.
1. **Hilo de Visión (`CameraThread`):** Hereda de `QThread`. Captura instantes de `cv2.VideoCapture` de manera asíncrona a 30 FPS. Transforma los frames de BGR (OpenCV) a RGB y luego a `QPixmap` para renderizarlos en la GUI. A través de **Señales** (`pyqtSignal`), notifica al hilo principal (`main_ui`) cuando detecta una nueva morfología.
2. **Workers de Robótica (`RobotWorker`):** Instancia la API del Lite 6. Se delega en un hilo apartado para que el intérprete G-Code o el flujo de dibujo geométrico puedan comandarse con llamadas de espera (`wait=True`) sin interrumpir las actualizaciones del contador en pantalla ni la telemetría.

---

## ⚙️ 3. Funciones de Servicio a Peticiones (Cumplimiento de Puntos)

A continuación se desglosan los procesos y funciones de backend que operativizan directamente las exigencias métricas establecidas:

### Petición 1: Manipulación Tridimensional y Evaluación de Trayectorias
- **Implementación:** Archivo `robot_controller.py`.
- **Capa UI:** Pestaña "Manual Manipulation".
- **Función Clave:** `move_to(self, x, y, z, wait=True)`
- **Descripción:** El usuario inserta distancias a través de las cajas de espín (SpinBoxes). Antes de comandar el robot a través del SDK `set_position`, la función invoca a un **Middleware de Seguridad** interno llamado `check_collision()`.
  - *Manejo Anti-colisiones:* Si la instrucción implica un movimiento con $Z < 0$ (choque contra la mesa de montaje) o con un radio polar a la base prohibido ($X^2 + Y^2 < 100^2$), el código interrumpe el flujo, emite un estado de error hacia PyQt6 y previene el desastre.

### Petición 2: Generación Paramétrica (Cuadrado, Triángulo, Círculo de 5cm)
- **Implementación:** Archivo `robot_controller.py`.
- **Capa UI:** Pestaña "Geometric Shapes".
- **Funciones Clave:** `draw_square()`, `draw_triangle()`, `draw_circle()`
- **Descripción:** Las tareas paramétricas calculan sus propios rumbos antes de mandarlos al controlador.
  - Para el **Cuadrado**: Una macro lineal simple sumando/restando $50\text{mm}$ fijos en los ejes cartesianos desde el punto basal.
  - Para el **Triángulo Equilátero**: Generación nodal aplicando trigonometría. La altura $h$ se calcula como $\approx 0.866 \times \text{lado}$.
  - Para el **Círculo**: Interpolación discreta por tramos iterando el radio ($r=25\text{mm}$), mapeando $\cos$ y $\sin$ en intervalos finos para asemejar el barrido cinemático.

### Petición 3: Dibujo a partir de Código-G (.ngc)
- **Implementación:** Archivo `robot_controller.py` y `main_ui.py`.
- **Capa UI:** Pestaña "G-Code Engine".
- **Función Clave:** `run_gcode(filepath, scale)`
- **Descripción:** Generamos un *Parser* de código G. Extrae mediante expresiones regulares (`re.search`) todos los comandos posicionales `X... Y...`. El sistema inyecta un factor de escala y un origen matricial (`X_BASE`, `Y_BASE`) para re-mapear la simulación y forzar que independientemente del alcance nativo de Inkscape, todo se concentre en el rectángulo de trabajo seguro de la mesa del Cobot. Actualiza reactivamente una `QProgressBar` en la interfaz.

### Petición 4: Visión y Secuenciado (Triángulo $\rightarrow$ Cuadrado $\rightarrow$ Círculo)
- **Implementación:** Motor `vision_engine.py` en conjunción con `run_vision_sequence()`.
- **Capa UI:** Pestaña "Computer Vision".
- **Descripción:**
  1. *Percepción*: `VisionEngine.detect_shapes()` toma una captura en vivo, binariza y obtiene los contornos de los trozos de papel con OpenCV. Por medio de aproximaciones poligonales (`cv2.approxPolyDP`) diferencia los 3 vértices de un triángulo frente a los $\geq 8$ de una curva (círculo).
  2. *Extracción*: El motor extrae los centroides ($rx, ry$) localizados de cada figura en la escena y los reporta en un diccionario ordenado.
  3. *Ejecución Pautada*: La función en el controlador lee las posiciones desde memoria y fuerza el inicio forzoso de la navegación en orden lexicográfico absoluto impuesto en una lista estática `sequence = ["triangle", "square", "circle"]`. Se navega el brazo hacia $X/Y$, provocando un zambullido Z sobre la misma.
