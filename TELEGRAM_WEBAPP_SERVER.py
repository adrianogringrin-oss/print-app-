#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-сервер для Telegram Mini App - СЕРВЕРНАЯ ВЕРСИЯ
Адаптированная версия для работы на сервере без macOS-зависимостей
"""

import sys
import os
import json
import base64
import io
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from collections import Counter

# Импорты без macOS-специфичных путей
from PIL import Image, ImageFilter, ImageChops

# Локальное хранилище сессий (бот и веб-сервер в разных контейнерах Railway — общая память недоступна).
# Импорт TELEGRAM_BOT_SERVER убран: он тянет python-telegram-bot и мог вызывать 502 при старте.
user_sessions = {}
def get_user_image(user_id):
    return user_sessions.get(user_id)

# Проверяем наличие OpenAI
HAS_OPENAI = False
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

OPENAI_API_KEY = None

def load_openai_key():
    """Загрузка API ключа OpenAI"""
    global OPENAI_API_KEY
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    key_file = os.path.expanduser('~/.openai_api_key')
    if not OPENAI_API_KEY and os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                OPENAI_API_KEY = f.read().strip()
        except:
            pass
    
    return OPENAI_API_KEY is not None

def extract_with_ai(image_path, user_prompt):
    """Извлечение объекта с помощью OpenAI Vision API"""
    if not HAS_OPENAI:
        return None, "OpenAI не установлен"
    
    if not load_openai_key():
        return None, "OpenAI API ключ не найден"
    
    try:
        image = Image.open(image_path)
        
        buffer = io.BytesIO()
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            rgb_image.save(buffer, format='PNG')
        else:
            image.save(buffer, format='PNG')
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        img_width, img_height = image.size
        
        prompt_lower = user_prompt.lower()
        is_entire_image = any(word in prompt_lower for word in ['весь', 'целиком', 'entire', 'whole', 'все', 
                                                                'весь текст', 'весь изображение', 'целое изображение',
                                                                'со всего', 'from entire', 'from whole'])
        
        if is_entire_image:
            return {
                'x1': 0,
                'y1': 0,
                'x2': img_width,
                'y2': img_height
            }, None
        
        system_prompt = """You are an expert image segmentation assistant. Your task is to identify the COMPLETE bounding box of the content described by the user.

CRITICAL INSTRUCTIONS:
1. You MUST include the ENTIRE content - from edge to edge, top to bottom, left to right
2. DO NOT crop or cut off any part - include EVERYTHING visible
3. The bounding box should include ALL text, ALL images, ALL decorations, ALL details
4. Add a GENEROUS margin (10-20 pixels) around the content to ensure nothing is cut off
5. The bounding box should be SIGNIFICANTLY LARGER than the content itself
6. If the user mentions "весь" (all), "целиком" (entire), "со всего" (from entire) - include the ENTIRE image
7. If extracting text - include ALL text from top to bottom, left to right
8. If extracting a design - include the COMPLETE design with all its parts

The image size is {}x{} pixels.
Return ONLY a valid JSON object with pixel coordinates in this exact format: {{"x1": number, "y1": number, "x2": number, "y2": number}}
Where:
- (x1, y1) is the top-left corner - make it WELL ABOVE and WELL LEFT of the content
- (x2, y2) is the bottom-right corner - make it WELL BELOW and WELL RIGHT of the content
- All coordinates are in pixels
- x1 < x2 and y1 < y2
- Coordinates must be within image bounds (0 to width/height)
- IMPORTANT: Make the box MUCH LARGER than the content - add 15-20 pixel margin on ALL sides

Remember: BETTER TO INCLUDE TOO MUCH than to crop anything! If unsure, make the box larger!""".format(img_width, img_height)
        
        prompt_lower = user_prompt.lower()
        is_text_extraction = any(word in prompt_lower for word in ['текст', 'надпись', 'text', 'inscription', 
                                                                    'только текст', 'only text', 'извлеки текст'])
        
        if is_text_extraction:
            user_message = f"""Find the COMPLETE bounding box for: {user_prompt}

Image dimensions: {img_width} x {img_height} pixels.

SPECIAL INSTRUCTIONS FOR TEXT EXTRACTION:
- Include ALL text/inscriptions - every word, every letter, from top to bottom, left to right
- Include ALL lines of text - do not miss any
- Add generous margin (20 pixels) around ALL text
- If text spans multiple lines - include ALL lines from first to last
- Return coordinates that capture EVERYTHING"""
        else:
            user_message = f"""Find the COMPLETE bounding box for: {user_prompt}

Image dimensions: {img_width} x {img_height} pixels.

Return the bounding box coordinates as JSON: {{"x1": number, "y1": number, "x2": number, "y2": number}}"""
        
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]}
            ],
            max_tokens=200
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Парсим JSON из ответа
        json_match = re.search(r'\{[^}]+\}', response_text)
        if json_match:
            coords = json.loads(json_match.group())
            
            # Нормализуем координаты
            x1 = max(0, min(int(coords.get('x1', 0)), img_width))
            y1 = max(0, min(int(coords.get('y1', 0)), img_height))
            x2 = max(x1 + 1, min(int(coords.get('x2', img_width)), img_width))
            y2 = max(y1 + 1, min(int(coords.get('y2', img_height)), img_height))
            
            # Автоматически расширяем область на 10-15% чтобы не обрезать
            width = x2 - x1
            height = y2 - y1
            margin_x = int(width * 0.1)
            margin_y = int(height * 0.1)
            
            x1 = max(0, x1 - margin_x)
            y1 = max(0, y1 - margin_y)
            x2 = min(img_width, x2 + margin_x)
            y2 = min(img_height, y2 + margin_y)
            
            # Если область очень маленькая, но пользователь просил "весь" - расширяем до всего изображения
            area = (x2 - x1) * (y2 - y1)
            total_area = img_width * img_height
            if area < total_area * 0.1 and is_entire_image:
                x1, y1, x2, y2 = 0, 0, img_width, img_height
            
            return {
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2
            }, None
        else:
            return None, "Не удалось распарсить ответ ИИ"
            
    except Exception as e:
        return None, f"Ошибка ИИ: {str(e)}"

# Импортируем функции удаления фона из ВЕБ_ВЕРСИЯ_С_ИИ.py
# Для сервера создадим упрощенную версию или скопируем функции
def remove_background_for_text(image):
    """Специализированное удаление фона для текста"""
    width, height = image.size
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    pixels = list(image.getdata())
    gray_pixels = [int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b, a in pixels]
    
    # Используем медианную яркость для более точного определения текста
    sorted_brightness = sorted(gray_pixels)
    median_brightness = sorted_brightness[len(sorted_brightness) // 2]
    text_threshold = max(median_brightness - 30, 80)
    
    new_pixels = []
    for i, pixel in enumerate(pixels):
        r, g, b, a = pixel
        brightness = gray_pixels[i]
        y_pos = i // width
        x_pos = i % width
        
        if brightness > text_threshold:
            # Очень светлый пиксель - удаляем агрессивно
            if brightness > 200:
                new_pixels.append((255, 255, 255, 0))
                continue
            
            # Проверяем соседей (радиус 2 пикселя)
            has_dark_neighbor = False
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x_pos + dx, y_pos + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        n_idx = ny * width + nx
                        n_brightness = gray_pixels[n_idx]
                        if n_brightness < text_threshold - 20:
                            has_dark_neighbor = True
                            break
                if has_dark_neighbor:
                    break
            
            if has_dark_neighbor and brightness < 130:
                new_pixels.append((r, g, b, 255))
            else:
                new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append((r, g, b, 255))
    
    result = Image.new('RGBA', (width, height))
    result.putdata(new_pixels)
    
    # Морфологическая очистка
    mask = Image.new('L', (width, height), 0)
    mask_pixels = [255 if p[3] > 0 else 0 for p in new_pixels]
    mask.putdata(mask_pixels)
    
    mask = mask.filter(ImageFilter.MaxFilter(size=3))
    mask = mask.filter(ImageFilter.MinFilter(size=3))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    result = Image.composite(result, Image.new('RGBA', (width, height), (255, 255, 255, 0)), mask)
    
    return result

def detect_edges(image):
    """Обнаружение краев/границ для защиты объектов"""
    width, height = image.size
    if image.mode != 'L':
        gray = image.convert('L')
    else:
        gray = image
    
    edge_pixels_list = [0] * (width * height)
    gray_pixels = list(gray.getdata())
    
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            idx = y * width + x
            center = gray_pixels[idx]
            
            neighbors = [
                gray_pixels[(y-1) * width + x],
                gray_pixels[(y+1) * width + x],
                gray_pixels[y * width + (x-1)],
                gray_pixels[y * width + (x+1)],
            ]
            
            max_diff = max(abs(center - n) for n in neighbors)
            edge_pixels_list[idx] = min(255, max_diff * 2)
    
    return edge_pixels_list

def remove_background_smart(image, ai_guidance=None, user_prompt="", original_image=None, selected_region=None):
    """Улучшенное удаление фона"""
    width, height = image.size
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    pixels = list(image.getdata())
    
    prompt_lower = user_prompt.lower() if user_prompt else ""
    is_text_extraction = any(word in prompt_lower for word in ['текст', 'надпись', 'text', 'inscription', 
                                                                'только текст', 'only text', 'извлеки текст'])
    
    if is_text_extraction:
        return remove_background_for_text(image)
    
    edge_pixels_list = detect_edges(image)
    
    edge_colors = []
    edge_zone = 0.15
    
    if original_image is not None and selected_region is not None:
        orig_width, orig_height = original_image.size
        if original_image.mode != 'RGBA':
            original_image = original_image.convert('RGBA')
        orig_pixels = list(original_image.getdata())
        x1, y1, x2, y2 = selected_region
        
        edge_width = int(orig_width * edge_zone)
        edge_height = int(orig_height * edge_zone)
        
        for y in range(orig_height):
            for x in range(orig_width):
                if (x < edge_width or x >= orig_width - edge_width or 
                    y < edge_height or y >= orig_height - edge_height):
                    if not (x1 <= x <= x2 and y1 <= y <= y2):
                        edge_colors.append(orig_pixels[y * orig_width + x])
    else:
        edge_width = int(width * edge_zone)
        edge_height = int(height * edge_zone)
        
        for y in range(height):
            for x in range(width):
                if (x < edge_width or x >= width - edge_width or 
                    y < edge_height or y >= height - edge_height):
                    edge_colors.append(pixels[y * width + x])
    
    edge_colors_rgb = [(r, g, b) for r, g, b, a in edge_colors]
    if edge_colors_rgb:
        most_common_colors = Counter(edge_colors_rgb).most_common(3)
        bg_colors = [color for color, count in most_common_colors]
    else:
        bg_colors = [(255, 255, 255), (240, 240, 240), (200, 200, 200)]
    
    aggressive_mode = False
    if user_prompt:
        prompt_lower = user_prompt.lower()
        if any(word in prompt_lower for word in ['убери фон', 'удали фон', 'remove background', 
                                                  'убери задний', 'удали задний', 'серый фон', 'gray background']):
            aggressive_mode = True
    
    bg_color_variations = []
    for bg_r, bg_g, bg_b in bg_colors:
        similar_count = 0
        for pixel in pixels:
            r, g, b, _ = pixel
            dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            if dist < 40:
                similar_count += 1
        bg_color_variations.append((bg_r, bg_g, bg_b, similar_count))
    
    bg_color_variations.sort(key=lambda x: x[3], reverse=True)
    primary_bg_color = bg_color_variations[0][:3] if bg_color_variations else bg_colors[0]
    
    new_pixels = []
    
    for i, pixel in enumerate(pixels):
        r, g, b, a = pixel
        y_pos = i // width
        x_pos = i % width
        
        dist_x = min(x_pos, width - x_pos)
        dist_y = min(y_pos, height - y_pos)
        dist_to_edge = min(dist_x, dist_y)
        
        max_dist = min(width, height) / 2
        normalized_dist = dist_to_edge / max_dist if max_dist > 0 else 0
        
        min_distance = float('inf')
        for bg_r, bg_g, bg_b in bg_colors:
            color_distance = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            min_distance = min(min_distance, color_distance)
        
        edge_strength = edge_pixels_list[i] if i < len(edge_pixels_list) else 0
        
        if normalized_dist < 0.2:
            threshold = 40 if aggressive_mode else 35
        elif normalized_dist < 0.5:
            base_threshold = 35 if aggressive_mode else 40
            threshold = base_threshold + (normalized_dist - 0.2) * 10
        else:
            threshold = 40 if aggressive_mode else 45
        
        if edge_strength > 30:
            is_background = False
        elif edge_strength > 15:
            is_background = False
        else:
            is_background = min_distance < threshold
            
            if not is_background:
                distance_to_primary = ((r - primary_bg_color[0]) ** 2 + 
                                       (g - primary_bg_color[1]) ** 2 + 
                                       (b - primary_bg_color[2]) ** 2) ** 0.5
                if distance_to_primary < 30:
                    is_background = True
        
        if is_background:
            neighbor_colors = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x_pos + dx, y_pos + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        n_idx = ny * width + nx
                        nr, ng, nb, _ = pixels[n_idx]
                        n_dist = float('inf')
                        for bg_r, bg_g, bg_b in bg_colors:
                            n_color_dist = ((nr - bg_r) ** 2 + (ng - bg_g) ** 2 + (nb - bg_b) ** 2) ** 0.5
                            n_dist = min(n_dist, n_color_dist)
                        neighbor_colors.append(n_dist)
            
            if neighbor_colors:
                non_bg_neighbors = sum(1 for d in neighbor_colors if d > 35)
                if non_bg_neighbors >= len(neighbor_colors) * 0.4:
                    is_background = False
        
        if not is_background:
            if edge_strength < 15 and r > 240 and g > 240 and b > 240 and abs(r - g) < 15 and abs(g - b) < 15:
                is_background = True
            elif edge_strength < 15 and r < 30 and g < 30 and b < 30:
                is_background = True
            elif edge_strength < 15 and abs(r - g) < 20 and abs(g - b) < 20 and 140 < (r + g + b) / 3 < 210:
                is_background = True
        
        if is_background:
            new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append((r, g, b, 255))
    
    result = Image.new('RGBA', (width, height))
    result.putdata(new_pixels)
    
    mask = Image.new('L', (width, height), 0)
    mask_pixels = [255 if p[3] > 0 else 0 for p in new_pixels]
    mask.putdata(mask_pixels)
    
    mask = mask.filter(ImageFilter.MaxFilter(size=1))
    mask = mask.filter(ImageFilter.MinFilter(size=1))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    result = Image.composite(result, Image.new('RGBA', (width, height), (255, 255, 255, 0)), mask)
    
    return result

# Полный HTML шаблон (скопирован из оригинального TELEGRAM_WEBAPP.py)
# Для серверной версии используем встроенный шаблон
TELEGRAM_HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Извлечение принтов</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "SF Pro Display", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-attachment: fixed;
            background-size: 200% 200%;
            animation: gradientShift 15s ease infinite;
            color: #2d3748;
            padding: 15px;
            min-height: 100vh;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .container {
            max-width: 100%;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            padding: 25px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px rgba(255,255,255,0.5);
            backdrop-filter: blur(20px) saturate(180%);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin: 15px 0 20px 0;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            text-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
        }
        h2 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 20px 0 15px 0;
            font-weight: 700;
            font-size: 22px;
        }
        h3 {
            color: #667eea;
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 12px;
        }
        .mode-selector {
            display: flex;
            gap: 10px;
            margin: 15px 0;
            justify-content: center;
            flex-wrap: wrap;
        }
        .mode-selector label {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border: 2px solid transparent;
            border-radius: 16px;
            cursor: pointer;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05);
            font-weight: 500;
            position: relative;
            overflow: hidden;
        }
        .mode-selector label::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: left 0.5s;
        }
        .mode-selector label:hover::before { left: 100%; }
        .mode-selector label:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.12), 0 0 0 1px rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.3);
        }
        .mode-selector input[type="radio"] { margin: 0; }
        .mode-selector input[type="radio"]:checked + span { font-weight: 700; color: #667eea; }
        .mode-selector label:has(input[type="radio"]:checked) {
            border-color: #667eea;
            background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25), 0 0 0 2px rgba(102, 126, 234, 0.1);
        }
        .ai-section {
            margin: 20px 0;
            padding: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.05);
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        .ai-section h3 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            font-size: 20px;
        }
        .ai-section p {
            color: #4a5568;
            margin-bottom: 12px;
            font-weight: 500;
        }
        textarea {
            width: 100%;
            min-height: 100px;
            padding: 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 15px;
            margin: 12px 0;
            resize: vertical;
            background: #ffffff;
            color: #2d3748;
            font-family: inherit;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15), 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea::placeholder { color: #a0aec0; }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            border: none;
            padding: 16px 32px;
            border-radius: 16px;
            cursor: pointer;
            font-size: 17px;
            width: 100%;
            margin: 12px 0;
            font-weight: 700;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35), 0 0 0 1px rgba(255,255,255,0.1) inset;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            letter-spacing: 0.3px;
        }
        .button:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(102, 126, 234, 0.45), 0 0 0 1px rgba(255,255,255,0.2) inset;
        }
        .button.success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            box-shadow: 0 8px 24px rgba(17, 153, 142, 0.35), 0 0 0 1px rgba(255,255,255,0.1) inset;
        }
        .button.success:hover { box-shadow: 0 12px 32px rgba(17, 153, 142, 0.45), 0 0 0 1px rgba(255,255,255,0.2) inset; }
        canvas {
            border: 3px solid #667eea;
            border-radius: 20px;
            display: block;
            margin: 20px auto;
            max-width: 100%;
            touch-action: none;
            box-shadow: 0 12px 40px rgba(0,0,0,0.15), 0 0 0 1px rgba(102, 126, 234, 0.1);
            background: #fff;
            transition: all 0.3s ease;
        }
        .status {
            text-align: center;
            padding: 14px 18px;
            margin: 12px 0;
            border-radius: 14px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05);
            font-weight: 600;
            color: #2d3748;
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        .result-container {
            margin-top: 24px;
            padding: 24px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.12), 0 0 0 1px rgba(0,0,0,0.05);
            border: 1px solid rgba(56, 239, 125, 0.2);
        }
        #resultCanvas {
            border: 3px solid #38ef7d;
            box-shadow: 0 12px 40px rgba(56, 239, 125, 0.25), 0 0 0 1px rgba(56, 239, 125, 0.1);
        }
        .upload-section {
            margin: 20px 0;
            padding: 28px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1), 0 0 0 1px rgba(0,0,0,0.05);
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        .upload-section h3 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 18px;
            font-size: 20px;
            font-weight: 700;
        }
        .file-input-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        .file-input-wrapper input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        .file-input-label {
            display: block;
            padding: 16px 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 700;
            font-size: 17px;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.35), 0 0 0 1px rgba(255,255,255,0.1) inset;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            letter-spacing: 0.3px;
        }
        .file-input-label:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(102, 126, 234, 0.45), 0 0 0 1px rgba(255,255,255,0.2) inset;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Извлечение принтов</h1>
        <div id="uploadSection" class="upload-section">
            <h3>📸 Загрузите изображение</h3>
            <div class="file-input-wrapper">
                <input type="file" id="fileInput" accept="image/*" onchange="handleFileUpload(event)">
                <label for="fileInput" class="file-input-label">📁 Выбрать файл</label>
            </div>
            <div id="uploadStatus" class="status" style="display:none;"></div>
        </div>
        <div class="mode-selector" id="modeSelector" style="display:none;">
            <label>
                <input type="radio" name="method" value="manual" checked>
                <span>🖱️ Ручной выбор</span>
            </label>
            <label>
                <input type="radio" name="method" value="ai" id="aiMethodRadio">
                <span>🤖 ИИ по описанию</span>
            </label>
        </div>
        <div id="aiSection" class="ai-section" style="display:none;">
            <h3>🤖 ИИ извлечение</h3>
            <p>Опишите что нужно извлечь:</p>
            <textarea id="aiPrompt" placeholder="Например: 'извлеки весь текст', 'извлеки автомобиль'"></textarea>
            <button class="button success" onclick="extractWithAI()">🔍 ИИ: Извлечь</button>
            <div id="aiStatus" class="status"></div>
        </div>
        <div id="imageContainer">
            <canvas id="imageCanvas"></canvas>
            <button class="button" id="extractBtn" onclick="extractRegion()" style="display:none;">🔍 Извлечь принт</button>
        </div>
        <div id="resultContainer" class="result-container" style="display:none;">
            <h2>Результат:</h2>
            <canvas id="resultCanvas"></canvas>
            <button class="button success" onclick="downloadResult()">💾 Скачать PNG</button>
        </div>
        <div id="status" class="status"></div>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('user_id') || 'web_' + Date.now();
        let image = null;
        let canvas = document.getElementById('imageCanvas');
        let ctx = canvas.getContext('2d');
        let scale = 1;
        let selection = {x1: 0, y1: 0, x2: 0, y2: 0};
        let isDrawing = false;
        let startX, startY;
        if (userId && !userId.startsWith('web_')) {
            fetch(`/get_image?user_id=${userId}`)
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        loadImageFromData(data.data);
                        document.getElementById('uploadSection').style.display = 'none';
                    } else {
                        document.getElementById('uploadSection').style.display = 'block';
                    }
                })
                .catch(() => document.getElementById('uploadSection').style.display = 'block');
        } else {
            document.getElementById('uploadSection').style.display = 'block';
        }
        function loadImageFromData(imageData) {
            image = new Image();
            image.src = 'data:image/png;base64,' + imageData;
            image.onload = function() {
                const maxWidth = window.innerWidth - 40;
                const maxHeight = window.innerHeight * 0.5;
                scale = Math.min(maxWidth / image.width, maxHeight / image.height, 1);
                canvas.width = image.width * scale;
                canvas.height = image.height * scale;
                ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                document.getElementById('extractBtn').style.display = 'block';
                document.getElementById('modeSelector').style.display = 'flex';
                setupCanvasEvents();
            };
        }
        function handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;
            if (!file.type.startsWith('image/')) {
                document.getElementById('uploadStatus').textContent = '❌ Пожалуйста, выберите изображение';
                document.getElementById('uploadStatus').style.display = 'block';
                return;
            }
            document.getElementById('uploadStatus').textContent = '⏳ Загрузка...';
            document.getElementById('uploadStatus').style.display = 'block';
            const formData = new FormData();
            formData.append('image', file);
            formData.append('user_id', userId);
            fetch('/upload_image', { method: 'POST', body: formData })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('uploadStatus').textContent = '✅ Изображение загружено!';
                    document.getElementById('uploadSection').style.display = 'none';
                    loadImageFromData(data.data);
                } else {
                    document.getElementById('uploadStatus').textContent = '❌ Ошибка: ' + (data.error || 'Не удалось загрузить');
                }
            })
            .catch(err => document.getElementById('uploadStatus').textContent = '❌ Ошибка: ' + err.message);
        }
        document.querySelectorAll('input[name="method"]').forEach(radio => {
            radio.addEventListener('change', function() {
                document.getElementById('aiSection').style.display = this.value === 'ai' ? 'block' : 'none';
            });
        });
        function setupCanvasEvents() {
            ['mousedown', 'touchstart'].forEach(eventType => {
                canvas.addEventListener(eventType, function(e) {
                    e.preventDefault();
                    const rect = canvas.getBoundingClientRect();
                    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                    startX = (clientX - rect.left) / scale;
                    startY = (clientY - rect.top) / scale;
                    isDrawing = true;
                });
            });
            ['mousemove', 'touchmove'].forEach(eventType => {
                canvas.addEventListener(eventType, function(e) {
                    if (!isDrawing) return;
                    e.preventDefault();
                    const rect = canvas.getBoundingClientRect();
                    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
                    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
                    const currentX = (clientX - rect.left) / scale;
                    const currentY = (clientY - rect.top) / scale;
                    selection.x1 = Math.round(Math.min(startX, currentX));
                    selection.y1 = Math.round(Math.min(startY, currentY));
                    selection.x2 = Math.round(Math.max(startX, currentX));
                    selection.y2 = Math.round(Math.max(startY, currentY));
                    drawSelection();
                });
            });
            ['mouseup', 'touchend'].forEach(eventType => {
                canvas.addEventListener(eventType, function(e) { isDrawing = false; });
            });
        }
        function drawSelection() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
            if (selection.x2 > selection.x1 && selection.y2 > selection.y1) {
                ctx.strokeStyle = '#FF0000';
                ctx.lineWidth = 2;
                ctx.strokeRect(selection.x1 * scale, selection.y1 * scale, (selection.x2 - selection.x1) * scale, (selection.y2 - selection.y1) * scale);
            }
        }
        function extractRegion() {
            if (!image || selection.x2 <= selection.x1 || selection.y2 <= selection.y1) {
                tg.showAlert('Сначала выделите область!');
                return;
            }
            extractAndProcess(selection);
        }
        function extractWithAI() {
            const prompt = document.getElementById('aiPrompt').value.trim();
            if (!prompt) {
                tg.showAlert('Введите описание!');
                return;
            }
            document.getElementById('aiStatus').textContent = '⏳ ИИ анализирует...';
            fetch('/extract_ai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({prompt: prompt, user_id: userId})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success && data.coords) {
                    document.getElementById('aiStatus').textContent = '✓ Область определена';
                    setTimeout(() => extractAndProcess(data.coords), 500);
                } else {
                    document.getElementById('aiStatus').textContent = '❌ Ошибка: ' + (data.error || 'Не удалось определить');
                }
            })
            .catch(err => document.getElementById('aiStatus').textContent = '❌ Ошибка: ' + err.message);
        }
        function extractAndProcess(coords) {
            document.getElementById('status').textContent = '⏳ Обработка...';
            fetch('/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({...coords, user_id: userId})
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
                        document.getElementById('status').textContent = '✓ Готово! Размер: ' + data.width + ' x ' + data.height;
                    };
                } else {
                    tg.showAlert('Ошибка: ' + data.error);
                }
            })
            .catch(err => tg.showAlert('Ошибка: ' + err.message));
        }
        function downloadResult() {
            const resultCanvas = document.getElementById('resultCanvas');
            if (!resultCanvas) {
                tg.showAlert('Результат не готов');
                return;
            }
            document.getElementById('status').textContent = '⏳ Подготовка файла...';
            const downloadUrl = `/result?user_id=${userId}`;
            const isMobile = tg && tg.platform && (tg.platform === 'ios' || tg.platform === 'android');
            if (isMobile) {
                window.location.href = downloadUrl;
                setTimeout(() => {
                    document.getElementById('status').textContent = '✅ Файл скачан в галерею!';
                    tg.showAlert('✅ Файл скачан в галерею!');
                }, 1000);
            } else {
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = 'print_result.png';
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                setTimeout(() => {
                    document.body.removeChild(link);
                    document.getElementById('status').textContent = '✅ Файл скачан!';
                    tg.showAlert('✅ Файл скачан!');
                }, 500);
            }
        }
    </script>
</body>
</html>'''

# Глобальное хранилище результатов
user_results = {}

class TelegramWebAppHandler(BaseHTTPRequestHandler):
    """Обработчик запросов для Telegram Web App"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(TELEGRAM_HTML_TEMPLATE.encode('utf-8'))
        
        elif path == '/get_image':
            user_id = query.get('user_id', [None])[0]
            if user_id:
                session = get_user_image(user_id)
                if session and 'image' in session:
                    image = session['image']
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    img_data = base64.b64encode(buffer.getvalue()).decode()
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('ngrok-skip-browser-warning', 'true')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'data': img_data
                    }).encode())
                    return
            
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': 'Изображение не найдено'}).encode())
        
        elif path == '/result':
            user_id = query.get('user_id', [None])[0]
            if user_id and user_id in user_results:
                result = user_results[user_id]
                buffer = io.BytesIO()
                result.save(buffer, format='PNG')
                buffer.seek(0)
                file_data = buffer.getvalue()
                
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.send_header('Content-Disposition', 'attachment; filename="print_result.png"; filename*=UTF-8\'\'print_result.png')
                self.send_header('Content-Length', str(len(file_data)))
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.send_header('ngrok-skip-browser-warning', 'true')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Expose-Headers', 'Content-Disposition')
                self.end_headers()
                self.wfile.write(file_data)
            else:
                self.send_error(404)
        
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/upload_image':
            self.handle_upload_image()
        elif path == '/extract':
            self.handle_extract()
        elif path == '/extract_ai':
            self.handle_extract_ai()
        else:
            self.send_error(404)
    
    def handle_upload_image(self):
        """Обработка загрузки изображения"""
        try:
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                raise ValueError("Неверный формат запроса")
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            boundary_match = re.search(r'boundary=([^;]+)', content_type)
            if not boundary_match:
                raise ValueError("Не найден boundary")
            
            boundary = boundary_match.group(1).strip()
            boundary_bytes = ('--' + boundary).encode()
            
            parts = post_data.split(boundary_bytes)
            
            user_id = None
            image_data = None
            filename = None
            
            for part in parts:
                if not part.strip() or part.strip() == b'--':
                    continue
                
                if b'\r\n\r\n' not in part:
                    continue
                
                headers_part, body_part = part.split(b'\r\n\r\n', 1)
                headers_text = headers_part.decode('utf-8', errors='ignore')
                
                name_match = re.search(r'name="([^"]+)"', headers_text)
                if not name_match:
                    continue
                
                field_name = name_match.group(1)
                
                filename_match = re.search(r'filename="([^"]+)"', headers_text)
                if filename_match:
                    filename = filename_match.group(1)
                
                body = body_part.rstrip(b'\r\n')
                
                if field_name == 'user_id':
                    user_id = body.decode('utf-8', errors='ignore').strip()
                elif field_name == 'image' and filename:
                    image_data = body
            
            if not user_id:
                user_id = f'web_{int(time.time() * 1000)}'
            
            if not image_data:
                raise ValueError("Изображение не получено")
            
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(image_data)
            temp_file.close()
            
            image = Image.open(temp_file.name)
            user_sessions[user_id] = {
                'image_path': temp_file.name,
                'image': image,
                'file_id': filename or 'uploaded'
            }
            
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'data': img_data,
                'user_id': user_id
            }).encode())
            
        except Exception as e:
            error_msg = str(e)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': error_msg
            }).encode())
    
    def handle_extract(self):
        """Обработка извлечения области"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data.get('user_id')
            if not user_id:
                raise ValueError("user_id не указан")
            
            session = get_user_image(user_id)
            if not session or 'image_path' not in session:
                raise ValueError("Изображение не найдено")
            
            x1 = int(data.get('x1', 0))
            y1 = int(data.get('y1', 0))
            x2 = int(data.get('x2', 0))
            y2 = int(data.get('y2', 0))
            
            original_image = session['image']
            cropped = original_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
            result = remove_background_smart(
                cropped,
                user_prompt="",
                original_image=original_image,
                selected_region=(x1, y1, x2, y2)
            )
            
            user_results[user_id] = result
            
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'data': img_data,
                'width': result.size[0],
                'height': result.size[1]
            }).encode())
            
        except Exception as e:
            error_msg = str(e)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': error_msg
            }).encode())
    
    def handle_extract_ai(self):
        """Обработка ИИ извлечения"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data.get('user_id')
            prompt = data.get('prompt', '')
            
            if not user_id:
                raise ValueError("user_id не указан")
            
            session = get_user_image(user_id)
            if not session or 'image_path' not in session:
                raise ValueError("Изображение не найдено")
            
            coords, error = extract_with_ai(session['image_path'], prompt)
            
            if error:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('ngrok-skip-browser-warning', 'true')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': error}).encode())
                return
            
            original_image = session['image']
            x1, y1, x2, y2 = coords['x1'], coords['y1'], coords['x2'], coords['y2']
            cropped = original_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
            result = remove_background_smart(
                cropped,
                user_prompt=prompt,
                original_image=original_image,
                selected_region=(x1, y1, x2, y2)
            )
            
            user_results[user_id] = result
            
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'coords': coords,
                'data': img_data,
                'width': result.size[0],
                'height': result.size[1]
            }).encode())
            
        except Exception as e:
            error_msg = str(e)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('ngrok-skip-browser-warning', 'true')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': error_msg
            }).encode())


def main():
    """Главная функция"""
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), TelegramWebAppHandler)
    
    print(f"🌐 Веб-сервер запущен на порту {port}")
    print(f"📱 Web App URL: {os.environ.get('WEB_APP_URL', 'http://localhost:' + str(port))}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервера...")
        server.shutdown()


if __name__ == "__main__":
    main()
