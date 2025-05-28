import tempfile
import os
from flask import Flask, request, redirect, send_file
from skimage import io
import base64
import glob
import numpy as np

app = Flask(__name__)

# Crear directorio de datos si no existe
DATA_DIR = os.path.join(tempfile.gettempdir(), 'squid_game_data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Definir las carpetas de formas
SHAPE_FOLDERS = {
    "X": os.path.join(DATA_DIR, "X"),
    "O": os.path.join(DATA_DIR, "O"),
    "■": os.path.join(DATA_DIR, "cuadrado"),
    "▲": os.path.join(DATA_DIR, "triangulo")
}

# Crear carpetas para cada forma
for folder in SHAPE_FOLDERS.values():
    if not os.path.exists(folder):
        os.makedirs(folder)

main_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Squid Game Drawing Challenge</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-image: url('/fondo.jpg');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
            color: white;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .header {
            width: 100%;
            background-color: rgba(255, 0, 128, 0.8); /* Semi-transparent background */
            padding: 20px 0;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        }
        .logo {
            max-width: 400px;
            margin: 0 auto;
        }
        .logo h1 {
            color: #ffffff; /* Bright white color */
            font-size: 3.5rem;
            margin-bottom: 10px;
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.9), 
                         -1px -1px 0 #000, 
                         1px -1px 0 #000, 
                         -1px 1px 0 #000, 
                         1px 1px 0 #000; /* Multiple shadows for better outline */
            letter-spacing: 4px;
        }
        .logo h2 {
            color: #ffffff;
            font-size: 2rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
        }
        .container {
            width: 90%;
            max-width: 800px;
            display: flex;
            flex-direction: column;
            align-items: center;
            background-color: #1e1e1e;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(255, 0, 128, 0.2);
        }
        h1 {
            color: #ff0080;
            font-size: 2.5rem;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .canvas-container {
            position: relative;
            margin: 20px 0;
        }

        /* Contenedor blanco detrás del canvas */
        .canvas-background {
            background-color: #ffffff;
            border-radius: 10px;
            display: inline-block;
        }

        canvas {
            background-color: transparent;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(255, 0, 128, 0.3);
        }
        .button {
            background-color: #ff0080;
            color: white;
            border: none;
            padding: 12px 24px;
            margin: 10px;
            font-size: 1.2rem;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .button:hover {
            background-color: #d5006b;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
        }
        .timer {
            font-size: 2rem;
            color: #ff0080;
            margin: 10px 0;
        }
        .shape-display {
            font-size: 3rem;
            margin: 20px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ff80ab; /* Lighter pink color for better visibility */
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8); /* Add shadow for better contrast */
        }
        .shape-icon {
            width: 60px;
            height: 60px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-left: 15px;
            border: 3px solid #ff0080;
            font-weight: bold;
            font-size: 40px;
            background-color: rgba(0, 0, 0, 0.5); /* Semi-transparent background */
            color: #ffffff; /* Bright white for the shape icon */
        }
        .footer {
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
        .buttons-container {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        #squareShape {
            border-radius: 0;
        }
        #circleShape {
            border-radius: 50%;
        }
        #xShape {
            position: relative;
        }
        #xShape:before, #xShape:after {
            content: '';
            position: absolute;
            width: 80%;
            height: 3px;
            background-color: #ff0080;
            top: 50%;
            left: 10%;
        }
        #xShape:before {
            transform: rotate(45deg);
        }
        #xShape:after {
            transform: rotate(-45deg);
        }
        .admin-buttons {
            margin-bottom: 15px;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
        }
        .admin-button {
            background-color: #333;
            color: white;
            border: 1px solid #ff0080;
            padding: 8px 15px;
            margin: 5px;
            font-size: 0.9rem;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .admin-button:hover {
            background-color: #ff0080;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <h1>SQUID GAME</h1>
            <h2>Desafío de Dibujo</h2>
        </div>
    </div>
    
    <div class="container">
        <div class="shape-display">
            Dibuja: <span id="shapeText"></span>
            <div id="shapeIcon" class="shape-icon"></div>
        </div>
        
        <div class="canvas-container">
            <div class="canvas-background">
                <canvas id="myCanvas" width="300" height="300"></canvas>
            </div>
        </div>
        
        <div class="buttons-container">
            <button id="clearButton" class="button">Borrar</button>
            <button id="submitButton" class="button">Enviar</button>
        </div>
    </div>
    
    <div class="footer">
        <div class="admin-buttons">
            <button id="prepareDataButton" class="admin-button">Procesar Datos</button>
            <button id="downloadXButton" class="admin-button">Descargar X.npy</button>
            <button id="downloadYButton" class="admin-button">Descargar Y.npy</button>
        </div>
        &copy; 2025 Squid Game Drawing Challenge
    </div>

    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <script>
        var mousePressed = false;
        var lastX, lastY;
        var ctx;
        var currentShape;        // Formas que usaremos
        const shapes = ["X", "O", "■", "▲"];
        const shapeNames = {
            "X": "una X",
            "O": "un Círculo",
            "■": "un Cuadrado",
            "▲": "un Triángulo"
        };

        function getRandomShape() {
            return shapes[Math.floor(Math.random() * shapes.length)];
        }

        function displayShape(shape) {
            document.getElementById('shapeText').innerText = shapeNames[shape];
            const iconEl = document.getElementById('shapeIcon');
            
            // Limpiar estilo anterior
            iconEl.style = "";
            iconEl.innerHTML = "";
              if (shape === "X") {
                iconEl.innerHTML = "X";
            } else if (shape === "O") {
                iconEl.innerHTML = "O";
            } else if (shape === "■") {
                iconEl.innerHTML = "■";
            } else if (shape === "▲") {
                iconEl.innerHTML = "▲";
            }
        }

        function initCanvas() {
            // activar transparencia en el canvas
            ctx = document.getElementById('myCanvas').getContext("2d", { alpha: true });
            
            // Limpiar canvas a fondo transparente
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

            // Elegir forma aleatoria
            currentShape = getRandomShape();
            displayShape(currentShape);

            // Configurar eventos de dibujo
            $('#myCanvas').mousedown(function (e) {
                mousePressed = true;
                draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
            });

            $('#myCanvas').mousemove(function (e) {
                if (mousePressed) {
                    draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
                }
            });

            $('#myCanvas').mouseup(function (e) {
                mousePressed = false;
            });
            
            $('#myCanvas').mouseleave(function (e) {
                mousePressed = false;
            });

            // Soporte táctil para dispositivos móviles
            $('#myCanvas').on('touchstart', function (e) {
                var touch = e.originalEvent.touches[0] || e.originalEvent.changedTouches[0];
                mousePressed = true;
                draw(touch.pageX - $(this).offset().left, touch.pageY - $(this).offset().top, false);
                e.preventDefault();
            });

            $('#myCanvas').on('touchmove', function (e) {
                if (mousePressed) {
                    var touch = e.originalEvent.touches[0] || e.originalEvent.changedTouches[0];
                    draw(touch.pageX - $(this).offset().left, touch.pageY - $(this).offset().top, true);
                }
                e.preventDefault();
            });

            $('#myCanvas').on('touchend', function (e) {
                mousePressed = false;
                e.preventDefault();
            });

            // Botón de borrar
            $('#clearButton').click(function() {
                clearCanvas();
            });

            // Botón de enviar
            $('#submitButton').click(function() {
                submitDrawing();
            });
        }

        function draw(x, y, isDown) {
            if (isDown) {
                ctx.beginPath();
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 15;
                ctx.lineJoin = "round";
                ctx.lineCap = "round";
                ctx.moveTo(lastX, lastY);
                ctx.lineTo(x, y);
                ctx.closePath();
                ctx.stroke();
            }
            lastX = x; lastY = y;
        }

        function clearCanvas() {
            // Borrar trazos dejando fondo transparente
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        }

        function submitDrawing() {
            var canvas = document.getElementById('myCanvas');
            var imageData = canvas.toDataURL();
            
            // Crear datos del formulario
            var formData = new FormData();
            formData.append('shape', currentShape);
            formData.append('myImage', imageData);
            
            // Enviar al servidor
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (response.ok) {
                    // Limpiar lienzo y obtener nueva forma
                    clearCanvas();
                    currentShape = getRandomShape();
                    displayShape(currentShape);
                    
                    // Mensaje de éxito
                    alert('¡Dibujo enviado correctamente!');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Hubo un error al enviar el dibujo.');
            });
        }

        // Inicializar cuando se carga la página
        window.onload = function() {
            initCanvas();
            
            // Añadir eventos para botones de administrador
            document.getElementById('prepareDataButton').addEventListener('click', function() {
                // Mostrar estado de carga
                const button = this;
                const originalText = button.innerText;
                button.disabled = true;
                button.innerText = "Procesando...";
                
                // Hacer llamada AJAX en lugar de navegar a una nueva página
                fetch('/prepare')
                    .then(response => response.text())
                    .then(data => {
                        alert(data); // Show the server's response message
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error al procesar los datos');
                    })
                    .finally(() => {
                        // Restaurar estado del botón
                        button.disabled = false;
                        button.innerText = originalText;
                    });
            });
            
            document.getElementById('downloadXButton').addEventListener('click', function() {
                window.location.href = '/X.npy';
            });
            
            document.getElementById('downloadYButton').addEventListener('click', function() {
                window.location.href = '/y.npy';
            });
        };
    </script>
</body>
</html>
"""

@app.route("/")
def main():
    return main_html

@app.route('/fondo.jpg')
def serve_background():
    return send_file('fondo.jpg')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Extraer datos de la imagen de la solicitud POST
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        shape = request.form.get('shape')
        
        # Usar la carpeta correspondiente del diccionario
        shape_folder = SHAPE_FOLDERS[shape]
        
        # Guardar la imagen decodificada en un archivo temporal dentro de la carpeta
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix='.png', dir=shape_folder) as fh:
            fh.write(base64.b64decode(img_data))
        
        print(f"Imagen de {shape} subida correctamente")
        return redirect("/", code=302)
        
    except Exception as err:
        print("Error al subir la imagen:")
        print(err)
        return "Error al subir la imagen", 500

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    # Preparar las imágenes y etiquetas para el conjunto de datos
    images = []
    shapes = ["X", "O", "■", "▲"]
    labels = []
    
    for shape in shapes:
        folder = SHAPE_FOLDERS[shape]
        filelist = glob.glob(f'{folder}/*.png')
        
        if filelist:  # Check if there are any files
            images_read = io.concatenate_images(io.imread_collection(filelist))
            # extraer solo canal alfa
            if images_read.ndim == 4:
                images_read = images_read[:, :, :, 3]
            
            shape_labels = np.array([shape] * images_read.shape[0])
            images.append(images_read)
            labels.append(shape_labels)
    
    if images:  # Only proceed if we have images
        # Apilar todas las imágenes y etiquetas
        images = np.vstack(images)
        labels = np.concatenate(labels)
        
        # Guardar matrices para entrenamiento en el directorio de datos
        np_x_path = os.path.join(DATA_DIR, 'X.npy')
        np_y_path = os.path.join(DATA_DIR, 'y.npy')
        
        np.save(np_x_path, images)
        np.save(np_y_path, labels)
        return "¡Conjunto de datos preparado con éxito!"
    else:
        return "No se encontraron imágenes para preparar el conjunto de datos"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file(os.path.join(DATA_DIR, 'X.npy'))

@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file(os.path.join(DATA_DIR, 'y.npy'))

if __name__ == "__main__":
    # Run the Flask app
    # Use port from environment variable for Railway compatibility
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)