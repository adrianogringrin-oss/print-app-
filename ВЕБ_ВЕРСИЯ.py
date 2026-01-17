#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВЕБ-ВЕРСИЯ - работает в браузере, не требует нативных библиотек
Решает проблему с крашем macOS
"""

import sys
import os
import json
import base64
import io
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading
import urllib.parse
from collections import Counter

try:
    from PIL import Image, ImageFilter, ImageChops
except ImportError:
    print("❌ Pillow не установлен. Установите: pip3 install Pillow")
    sys.exit(1)

def detect_strong_edges(image):
    """Обнаружение только сильных краев (игнорируя шум)"""
    # Конвертируем в grayscale и применяем легкое размытие для уменьшения шума
    gray = image.convert('L')
    gray = gray.filter(ImageFilter.GaussianBlur(radius=0.5))  # Легкое размытие для удаления шума
    
    width, height = gray.size
    gray_data = list(gray.getdata())
    
    # Создаем карту краев
    edge_map = Image.new('L', (width, height), 0)
    edge_pixels = [0] * (width * height)
    
    # ВЫСОКИЙ порог для сильных краев (фильтруем шум агрессивно)
    edge_threshold = 70  # Только действительно сильные края
    
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            idx = y * width + x
            
            # Упрощенный Sobel operator для обнаружения краев
            # Горизонтальный градиент
            gx = abs(gray_data[(y-1)*width + x+1] + 2*gray_data[y*width + x+1] + gray_data[(y+1)*width + x+1] -
                     gray_data[(y-1)*width + x-1] - 2*gray_data[y*width + x-1] - gray_data[(y+1)*width + x-1])
            
            # Вертикальный градиент
            gy = abs(gray_data[(y+1)*width + x-1] + 2*gray_data[(y+1)*width + x] + gray_data[(y+1)*width + x+1] -
                     gray_data[(y-1)*width + x-1] - 2*gray_data[(y-1)*width + x] - gray_data[(y-1)*width + x+1])
            
            # Вычисляем силу края
            edge_strength = (gx + gy) / 8  # Нормализуем
            
            # Только СИЛЬНЫЕ края (фильтруем шум)
            if edge_strength > edge_threshold:
                edge_pixels[idx] = min(255, int(edge_strength))
    
    edge_map.putdata(edge_pixels)
    
    # Легкое морфологическое закрытие для соединения близких краев (только для текста/линий)
    edge_map = edge_map.filter(ImageFilter.MaxFilter(size=1))
    
    return edge_map

def remove_background_advanced(image):
    """Продвинутое удаление фона с защитой тонких деталей"""
    width, height = image.size
    
    # Конвертируем в RGBA если еще не
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # ОБНАРУЖЕНИЕ КРАЕВ - только сильные края (игнорируя шум)
    edge_map = detect_strong_edges(image)
    edge_data = list(edge_map.getdata())
    
    # Получаем данные пикселей оригинала
    pixels = list(image.getdata())
    
    # Анализируем края изображения для определения фона
    edge_colors = []
    
    # Верхняя и нижняя границы
    for x in range(width):
        edge_colors.append(pixels[x])  # Верх
        edge_colors.append(pixels[(height-1) * width + x])  # Низ
    
    # Левая и правая границы
    for y in range(height):
        edge_colors.append(pixels[y * width])  # Лево
        edge_colors.append(pixels[y * width + width - 1])  # Право
    
    # Находим наиболее распространенный цвет на краях (фон)
    edge_colors_rgb = [(r, g, b) for r, g, b, a in edge_colors]
    if edge_colors_rgb:
        most_common_colors = Counter(edge_colors_rgb).most_common(3)
        bg_colors = [color for color, count in most_common_colors]
    else:
        bg_colors = [(255, 255, 255), (240, 240, 240), (200, 200, 200)]
    
    # Создаем новое изображение с прозрачностью
    new_pixels = []
    
    for i, pixel in enumerate(pixels):
        r, g, b, a = pixel
        y_pos = i // width
        x_pos = i % width
        
        # Получаем силу края для этого пикселя
        edge_strength = edge_data[i] if i < len(edge_data) else 0
        
        # Если это ОЧЕНЬ СИЛЬНЫЙ край - защищаем пиксель (не удаляем!)
        # Используем очень высокий порог чтобы фильтровать весь шум
        is_edge = edge_strength > 100  # Очень высокий порог - только явные края объектов
        
        # Проверяем, является ли пиксель фоном
        min_distance = float('inf')
        
        for bg_r, bg_g, bg_b in bg_colors:
            # Вычисляем расстояние цвета (чувствительность)
            color_distance = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            min_distance = min(min_distance, color_distance)
        
        # АДАПТИВНЫЙ ПОРОГ
        if is_edge:
            # Для краев используем более строгий порог, но не слишком строгий
            # чтобы не удалить края, которые немного похожи на фон
            threshold = 30  # Защита деталей, но не слишком мягко
        else:
            # Для остальных пикселей - нормальный порог
            threshold = 35
        
        is_background = min_distance < threshold
        
        # Дополнительная проверка: очень светлые или очень темные пиксели
        # НО! Не удаляем если это сильный край!
        if not is_background and not is_edge:
            # Очень светлый фон (белый, светло-серый) - более строгая проверка
            if r > 250 and g > 250 and b > 250:
                is_background = True
            # Очень темный фон (черный, темно-серый) - более строгая проверка
            elif r < 20 and g < 20 and b < 20:
                is_background = True
            # Однотонный серый фон - только очень явный фон
            elif abs(r - g) < 10 and abs(g - b) < 10 and abs(r - b) < 10:
                avg_brightness = (r + g + b) / 3
                if avg_brightness > 230:  # Очень светлый серый (почти белый)
                    is_background = True
                elif avg_brightness < 30:  # Очень темный серый (почти черный)
                    is_background = True
        
        # Если это край - НИКОГДА не удаляем, даже если похож на фон!
        if is_edge and is_background:
            is_background = False
        
        if is_background:
            # Делаем пиксель прозрачным
            # Для фона делаем полностью прозрачным без плавности (меньше артефактов)
            new_pixels.append((255, 255, 255, 0))
        else:
            # Оставляем пиксель полностью непрозрачным
            new_pixels.append((r, g, b, 255))
    
    # Создаем новое изображение
    result = Image.new('RGBA', (width, height))
    result.putdata(new_pixels)
    
    # Постобработка: очистка шума и артефактов
    # Создаем маску
    mask = Image.new('L', (width, height), 0)
    mask_pixels = []
    
    for pixel in new_pixels:
        if pixel[3] > 0:  # Если не прозрачный
            mask_pixels.append(255)
        else:
            mask_pixels.append(0)
    
    mask.putdata(mask_pixels)
    
    # МОРФОЛОГИЧЕСКАЯ ОЧИСТКА - удаляем мелкие изолированные пиксели (шум)
    # Закрытие для соединения близких областей
    mask = mask.filter(ImageFilter.MaxFilter(size=1))
    # Открытие для удаления мелких отверстий
    mask = mask.filter(ImageFilter.MinFilter(size=1))
    
    # Применяем очень легкое размытие только к маске для плавных краев
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    # Применяем маску к результату
    result = Image.composite(result, Image.new('RGBA', (width, height), (255, 255, 255, 0)), mask)
    
    return result

# Глобальные переменные для хранения данных
global_image = None
global_result = None
selected_region = None

class WebHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        path = urllib.parse.urlparse(self.path).path
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif path == '/image':
            self.send_image()
        elif path == '/result':
            self.get_result()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/extract':
            self.extract_region()
        elif self.path == '/save':
            self.handle_save()
        else:
            self.send_error(404)
    
    def send_image(self):
        """Отправка изображения"""
        global global_image
        if global_image is None:
            self.send_error(404)
            return
        
        try:
            # Конвертируем в base64
            buffer = io.BytesIO()
            global_image.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'data': img_data,
                'width': global_image.size[0],
                'height': global_image.size[1]
            }).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_upload(self):
        """Обработка загрузки файла"""
        global global_image
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Нет данных")
            
            post_data = self.rfile.read(content_length)
            
            # Парсим multipart/form-data
            # Ищем границу
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(b'--' + boundary)
                
                for part in parts:
                    if b'Content-Type:' in part:
                        # Нашли файл
                        header_end = part.find(b'\r\n\r\n')
                        if header_end > 0:
                            file_data = part[header_end+4:]
                            # Убираем завершающий \r\n
                            file_data = file_data.rstrip(b'\r\n')
                            global_image = Image.open(io.BytesIO(file_data))
                            break
            
            if global_image is None:
                raise ValueError("Не удалось распарсить файл")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def extract_region(self):
        """Извлечение области"""
        global global_image, global_result, selected_region
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            x1 = int(data.get('x1', 0))
            y1 = int(data.get('y1', 0))
            x2 = int(data.get('x2', 0))
            y2 = int(data.get('y2', 0))
            
            if global_image is None:
                raise ValueError("Изображение не загружено")
            
            # Обрезаем
            cropped = global_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
            # УЛУЧШЕННОЕ УДАЛЕНИЕ ФОНА
            cropped = remove_background_advanced(cropped)
            global_result = cropped
            
            # Конвертируем в base64 для отправки
            buffer = io.BytesIO()
            cropped.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'data': img_data,
                'width': cropped.size[0],
                'height': cropped.size[1]
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def get_result(self):
        """Получение результата"""
        global global_result
        if global_result is None:
            self.send_error(404)
            return
        
        try:
            buffer = io.BytesIO()
            global_result.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('Content-Disposition', 'attachment; filename="extracted.png"')
            self.send_header('Content-Length', str(len(img_data)))
            self.end_headers()
            self.wfile.write(img_data)
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_save(self):
        """Обработка сохранения"""
        global global_result
        if global_result is None:
            self.send_error(404)
            return
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            save_path = data.get('path', '')
            if not save_path:
                raise ValueError("Путь не указан")
            
            global_result.save(save_path, "PNG", optimize=True)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def log_message(self, format, *args):
        """Отключаем логирование"""
        pass

# HTML шаблон
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Извлечение принтов</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2196F3;
            text-align: center;
        }
        .button {
            background: #2196F3;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin: 10px 5px;
        }
        .button:hover {
            background: #1976D2;
        }
        .button.danger {
            background: #F44336;
        }
        .button.success {
            background: #4CAF50;
        }
        #imageCanvas {
            border: 2px solid #ddd;
            border-radius: 5px;
            cursor: crosshair;
            display: block;
            margin: 20px auto;
            max-width: 100%;
        }
        #resultCanvas {
            border: 2px solid #ddd;
            border-radius: 5px;
            display: block;
            margin: 20px auto;
            max-width: 100%;
        }
        .info {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        input[type="file"] {
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Извлечение принтов и надписей</h1>
        
        <div class="controls">
            <input type="file" id="fileInput" accept="image/*">
            <button class="button" onclick="document.getElementById('fileInput').click()">📁 Загрузить изображение</button>
        </div>
        
        <div id="imageContainer"></div>
        <div id="resultContainer" style="display:none;">
            <h2>Результат:</h2>
            <canvas id="resultCanvas"></canvas>
            <div class="controls">
                <button class="button success" onclick="downloadResult()">💾 Скачать PNG</button>
            </div>
        </div>
        
        <div class="info" id="info"></div>
    </div>
    
    <script>
        let image = null;
        let canvas = null;
        let ctx = null;
        let startX = 0, startY = 0;
        let isDrawing = false;
        let rect = null;
        let scale = 1;
        
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    loadImage();
                } else {
                    alert('Ошибка загрузки: ' + data.error);
                }
            });
        });
        
        function loadImage() {
            fetch('/image')
            .then(r => r.json())
            .then(data => {
                if (!data.success) {
                    alert('Ошибка загрузки изображения');
                    return;
                }
                
                image = new Image();
                image.src = 'data:image/png;base64,' + data.data;
                image.onload = function() {
                    canvas = document.createElement('canvas');
                    canvas.id = 'imageCanvas';
                    ctx = canvas.getContext('2d');
                    
                    originalWidth = data.width;
                    originalHeight = data.height;
                    
                    // Масштабируем для отображения
                    const maxWidth = 1000;
                    const maxHeight = 800;
                    scale = Math.min(maxWidth / data.width, maxHeight / data.height, 1);
                    
                    canvas.width = data.width * scale;
                    canvas.height = data.height * scale;
                    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                    
                    document.getElementById('imageContainer').innerHTML = '';
                    document.getElementById('imageContainer').appendChild(canvas);
                    document.getElementById('info').innerHTML = 
                        'Изображение загружено. Зажмите ЛКМ и выделите область для извлечения, затем нажмите "Извлечь".';
                    
                    // Добавляем кнопку извлечения
                    const extractBtn = document.createElement('button');
                    extractBtn.className = 'button success';
                    extractBtn.textContent = '🔍 Извлечь принт';
                    extractBtn.onclick = extractRegion;
                    extractBtn.style.display = 'block';
                    extractBtn.style.margin = '20px auto';
                    document.getElementById('imageContainer').appendChild(extractBtn);
                    
                    setupCanvasEvents();
                };
            });
        }
        
        let selection = {x1: 0, y1: 0, x2: 0, y2: 0};
        let originalWidth = 0, originalHeight = 0;
        
        function setupCanvasEvents() {
            canvas.addEventListener('mousedown', function(e) {
                const rect = canvas.getBoundingClientRect();
                startX = (e.clientX - rect.left) / scale;
                startY = (e.clientY - rect.top) / scale;
                isDrawing = true;
            });
            
            canvas.addEventListener('mousemove', function(e) {
                if (!isDrawing) return;
                const rect = canvas.getBoundingClientRect();
                const currentX = (e.clientX - rect.left) / scale;
                const currentY = (e.clientY - rect.top) / scale;
                
                // Сохраняем координаты в оригинальном масштабе
                selection.x1 = Math.round(Math.min(startX, currentX));
                selection.y1 = Math.round(Math.min(startY, currentY));
                selection.x2 = Math.round(Math.max(startX, currentX));
                selection.y2 = Math.round(Math.max(startY, currentY));
                
                // Перерисовываем изображение
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                
                // Рисуем прямоугольник
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 3;
                ctx.strokeRect(
                    selection.x1 * scale,
                    selection.y1 * scale,
                    (selection.x2 - selection.x1) * scale,
                    (selection.y2 - selection.y1) * scale
                );
            });
            
            canvas.addEventListener('mouseup', function(e) {
                isDrawing = false;
            });
        }
        
        function extractRegion() {
            if (!image || !canvas) {
                alert('Сначала загрузите изображение и выделите область!');
                return;
            }
            
            if (selection.x2 <= selection.x1 || selection.y2 <= selection.y1) {
                alert('Сначала выделите область мышью!');
                return;
            }
            
            fetch('/extract', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(selection)
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const resultCanvas = document.getElementById('resultCanvas');
                    const resultCtx = resultCanvas.getContext('2d');
                    const resultImg = new Image();
                    resultImg.src = 'data:image/png;base64,' + data.data;
                    resultImg.onload = function() {
                        resultCanvas.width = resultImg.width;
                        resultCanvas.height = resultImg.height;
                        resultCtx.drawImage(resultImg, 0, 0);
                        document.getElementById('resultContainer').style.display = 'block';
                        document.getElementById('info').innerHTML = 
                            '✓ Принт извлечен! Размер: ' + data.width + ' x ' + data.height + ' пикселей';
                    };
                } else {
                    alert('Ошибка извлечения: ' + data.error);
                }
            })
            .catch(err => {
                alert('Ошибка при извлечении: ' + err);
            });
        }
        
        function downloadResult() {
            window.location.href = '/result';
        }
    </script>
</body>
</html>'''

def start_server(port=8000):
    """Запуск веб-сервера"""
    server = HTTPServer(('localhost', port), WebHandler)
    print(f"\n{'='*60}")
    print("  🌐 ВЕБ-ИНТЕРФЕЙС ДЛЯ ИЗВЛЕЧЕНИЯ ПРИНТОВ")
    print("="*60)
    print(f"\n✓ Сервер запущен на: http://localhost:{port}")
    print("  Браузер должен открыться автоматически...")
    print("\n  Для остановки нажмите Ctrl+C\n")
    
    # Открываем браузер
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        server.shutdown()

def main():
    """Главная функция"""
    try:
        start_server()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
