#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ВЕБ-ВЕРСИЯ С ИИ ПОДДЕРЖКОЙ
Использует OpenAI Vision API для точного извлечения объектов по текстовому описанию
"""

import sys
import os

# ДОБАВЛЯЕМ ПУТИ К БИБЛИОТЕКАМ ПЕРЕД ИМПОРТОМ
# Добавляем только путь к Homebrew Python 3.14 (где установлены библиотеки)
user_site_314 = os.path.expanduser('~/Library/Python/3.14/lib/python/site-packages')

if os.path.exists(user_site_314) and user_site_314 not in sys.path:
    sys.path.insert(0, user_site_314)

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
except ImportError as e:
    # Пробуем добавить путь к Homebrew Python библиотекам
    try:
        user_site_314 = os.path.expanduser('~/Library/Python/3.14/lib/python/site-packages')
        if os.path.exists(user_site_314):
            sys.path.insert(0, user_site_314)
        from PIL import Image, ImageFilter, ImageChops
    except ImportError:
        print("❌ Pillow не установлен. Установите: pip3 install Pillow")
        print(f"   Ошибка: {e}")
        sys.exit(1)

# Проверяем наличие OpenAI
HAS_OPENAI = False
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    # Пути уже добавлены выше, просто проверяем снова
    try:
        import openai
        HAS_OPENAI = True
    except ImportError:
        HAS_OPENAI = False
        # Не выводим ошибку - ИИ функции будут недоступны, но программа продолжит работу

# Глобальные переменные
global_image = None
global_result = None
global_prompt = ""  # Сохраняем промпт пользователя для улучшения удаления фона
OPENAI_API_KEY = None

def load_openai_key():
    """Загрузка API ключа OpenAI"""
    global OPENAI_API_KEY
    # Проверяем переменную окружения
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Проверяем файл с ключом
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
        return None, "OpenAI API ключ не найден. Создайте файл ~/.openai_api_key или установите переменную OPENAI_API_KEY"
    
    try:
        # Открываем и конвертируем изображение
        image = Image.open(image_path)
        
        # Конвертируем в base64
        buffer = io.BytesIO()
        # Конвертируем в RGB если нужно
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            rgb_image.save(buffer, format='PNG')
        else:
            image.save(buffer, format='PNG')
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Получаем размер изображения для промпта
        img_width, img_height = image.size
        
        # Анализируем промпт для определения типа задачи
        prompt_lower = user_prompt.lower()
        is_entire_image = any(word in prompt_lower for word in ['весь', 'целиком', 'entire', 'whole', 'все', 
                                                                'весь текст', 'весь изображение', 'целое изображение',
                                                                'со всего', 'from entire', 'from whole'])
        is_text_extraction = any(word in prompt_lower for word in ['текст', 'надпись', 'text', 'inscription', 
                                                                    'только текст', 'only text', 'извлеки текст'])
        
        if is_entire_image:
            # Если пользователь просит извлечь ВСЕ изображение - возвращаем всю область
            return {
                'x1': 0,
                'y1': 0,
                'x2': img_width,
                'y2': img_height
            }, None
        
        # Формируем улучшенный промпт для ИИ с учетом деталей
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
        
        # Анализируем промпт для специальной обработки текста
        prompt_lower = user_prompt.lower()
        is_text_extraction = any(word in prompt_lower for word in ['текст', 'надпись', 'text', 'inscription', 
                                                                    'только текст', 'only text', 'извлеки текст'])
        
        if is_text_extraction:
            user_message = f"""Find the COMPLETE bounding box for: {user_prompt}

Image dimensions: {img_width} x {img_height} pixels.

SPECIAL INSTRUCTIONS FOR TEXT EXTRACTION:
- Include ALL text/inscriptions - every word, every letter, from top to bottom, left to right
- Add GENEROUS margin (15-20 pixels) around the text area
- The box should contain ALL visible text on the ENTIRE page
- Include the entire text area, not just individual words
- If user says "весь" (all), "целиком" (entire), "со всего" (from entire) - include the ENTIRE image
- Better to include too much than to miss any text
- Make the box MUCH LARGER than the text to ensure nothing is cut off

Return ONLY the JSON object with coordinates, for example:
{{"x1": 100, "y1": 50, "x2": 400, "y2": 300}}

Do not include any other text, explanations, or formatting."""
        else:
            user_message = f"""Find the COMPLETE bounding box for: {user_prompt}

Image dimensions: {img_width} x {img_height} pixels.

CRITICAL REQUIREMENTS:
- Include the ENTIRE print/design - do NOT crop any edges
- Add 5-10 pixel margin around the print to ensure nothing is cut off
- Include ALL text, ALL images, ALL parts of the design
- The box should be LARGER than the print itself
- Better to include too much than to crop the print

Return ONLY the JSON object with coordinates, for example:
{{"x1": 100, "y1": 50, "x2": 400, "y2": 300}}

Do not include any other text, explanations, or formatting."""
        
        # Вызываем OpenAI Vision API
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Используем более дешевую модель для начала
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        # Парсим ответ
        result_text = response.choices[0].message.content.strip()
        
        # Извлекаем JSON из ответа (может быть многострочным)
        import re
        # Ищем JSON объект (может быть на нескольких строках)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
        if json_match:
            try:
                coords = json.loads(json_match.group())
                # Проверяем наличие нужных полей
                if all(k in coords for k in ['x1', 'y1', 'x2', 'y2']):
                    # Нормализуем координаты относительно изображения
                    img_width, img_height = image.size
                    
                    # Расширяем область на 10-15% чтобы не обрезать края
                    # Для текста расширяем еще больше
                    prompt_lower = user_prompt.lower() if user_prompt else ""
                    is_text = any(word in prompt_lower for word in ['текст', 'надпись', 'text'])
                    
                    if is_text:
                        # Для текста расширяем на 15% - важно не обрезать буквы
                        margin_x = int((coords['x2'] - coords['x1']) * 0.15)
                        margin_y = int((coords['y2'] - coords['y1']) * 0.15)
                    else:
                        # Для других изображений - 10%
                        margin_x = int((coords['x2'] - coords['x1']) * 0.10)
                        margin_y = int((coords['y2'] - coords['y1']) * 0.10)
                    
                    # Проверяем размер области - если она слишком маленькая относительно изображения, расширяем
                    area_width = coords['x2'] - coords['x1']
                    area_height = coords['y2'] - coords['y1']
                    area_ratio = (area_width * area_height) / (img_width * img_height)
                    
                    # Если область меньше 30% изображения и пользователь просил "весь" или "целиком" - расширяем до всего изображения
                    if area_ratio < 0.3 and any(word in prompt_lower for word in ['весь', 'целиком', 'entire', 'whole', 'все', 'со всего']):
                        coords['x1'] = 0
                        coords['y1'] = 0
                        coords['x2'] = img_width
                        coords['y2'] = img_height
                    else:
                        coords['x1'] = max(0, min(int(coords['x1']) - margin_x, img_width))
                        coords['y1'] = max(0, min(int(coords['y1']) - margin_y, img_height))
                        coords['x2'] = max(coords['x1'] + 1, min(int(coords['x2']) + margin_x, img_width))
                        coords['y2'] = max(coords['y1'] + 1, min(int(coords['y2']) + margin_y, img_height))
                    return coords, None
                else:
                    return None, f"Неполные координаты в ответе ИИ: {coords}"
            except json.JSONDecodeError as e:
                return None, f"Ошибка парсинга JSON от ИИ: {e}\nОтвет: {result_text}"
        else:
            # Попробуем найти координаты в тексте другим способом
            # Иногда ИИ пишет координаты в виде текста
            nums = re.findall(r'\d+', result_text)
            if len(nums) >= 4:
                try:
                    coords = {
                        'x1': int(nums[0]),
                        'y1': int(nums[1]),
                        'x2': int(nums[2]),
                        'y2': int(nums[3])
                    }
                    img_width, img_height = image.size
                    coords['x1'] = max(0, min(coords['x1'], img_width))
                    coords['y1'] = max(0, min(coords['y1'], img_height))
                    coords['x2'] = max(coords['x1'] + 1, min(coords['x2'], img_width))
                    coords['y2'] = max(coords['y1'] + 1, min(coords['y2'], img_height))
                    return coords, None
                except:
                    pass
            
            return None, f"Не удалось извлечь координаты из ответа ИИ: {result_text}"
            
    except Exception as e:
        return None, f"Ошибка ИИ: {str(e)}"

def remove_background_for_text(image):
    """
    Специальный алгоритм для извлечения текста - удаляет фон листа, оставляет только текст
    """
    width, height = image.size
    pixels = list(image.getdata())
    
    # Конвертируем в grayscale для анализа яркости
    gray = image.convert('L')
    gray_pixels = list(gray.getdata())
    
    # Анализируем распределение яркости для определения текста и фона
    # Текст обычно темный (низкая яркость), фон светлый (высокая яркость)
    
    # Анализируем распределение яркости для определения текста и фона
    brightness_values = [p for p in gray_pixels]
    
    # Находим минимальную и максимальную яркость
    min_brightness = min(brightness_values) if brightness_values else 0
    max_brightness = max(brightness_values) if brightness_values else 255
    avg_brightness = sum(brightness_values) / len(brightness_values) if brightness_values else 128
    
    # Сортируем яркости для нахождения медианы
    sorted_brightness = sorted(brightness_values)
    median_brightness = sorted_brightness[len(sorted_brightness) // 2] if sorted_brightness else 128
    
    # АГРЕССИВНЫЙ ПОРОГ для текста: используем более строгий критерий
    # Текст должен быть ЗНАЧИТЕЛЬНО темнее фона
    text_threshold = median_brightness * 0.5
    
    # Дополнительно: если средняя яркость высокая (светлый фон), делаем порог еще строже
    if avg_brightness > 180:  # Очень светлый фон (белая бумага)
        text_threshold = min(text_threshold, 90)  # Более строгий порог для текста
    elif avg_brightness > 150:  # Светлый фон
        text_threshold = min(text_threshold, 110)
    
    new_pixels = []
    
    for i, pixel in enumerate(pixels):
        r, g, b, a = pixel
        brightness = gray_pixels[i]
        
        # АГРЕССИВНОЕ УДАЛЕНИЕ ФОНА:
        # 1. Если пиксель очень светлый (> 180) - точно фон, удаляем
        # 2. Если пиксель светлее порога - фон, удаляем
        # 3. Если пиксель средний (между порогом и 150) - проверяем соседей
        
        if brightness > 180:  # Очень светлый - точно фон (более агрессивно)
            new_pixels.append((255, 255, 255, 0))
        elif brightness > text_threshold:
            # Светлее порога - проверяем является ли это частью текста
            # Анализируем соседние пиксели
            y_pos = i // width
            x_pos = i % width
            
            # Проверяем есть ли рядом темные пиксели (текст)
            has_dark_neighbor = False
            
            for dy in [-2, -1, 0, 1, 2]:
                for dx in [-2, -1, 0, 1, 2]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x_pos + dx, y_pos + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        n_idx = ny * width + nx
                        n_brightness = gray_pixels[n_idx]
                        # Если сосед темный (текст) - это может быть край текста
                        if n_brightness < text_threshold:
                            has_dark_neighbor = True
                            break
                if has_dark_neighbor:
                    break
            
            # Если рядом есть темные пиксели И сам пиксель не очень светлый - сохраняем (край текста)
            if has_dark_neighbor and brightness < 130:  # Более строгий порог для краев
                new_pixels.append((r, g, b, 255))
            else:
                # Это фон (клетчатая бумага, линии) - удаляем
                new_pixels.append((255, 255, 255, 0))
        else:
            # Темный пиксель - это текст, сохраняем
            new_pixels.append((r, g, b, 255))
    
    result = Image.new('RGBA', (width, height))
    result.putdata(new_pixels)
    
    # ДОПОЛНИТЕЛЬНАЯ АГРЕССИВНАЯ ОЧИСТКА:
    # Удаляем все средние и светлые пиксели которые не являются частью текста
    result_pixels = list(result.getdata())
    cleaned_pixels = []
    
    for i, pixel in enumerate(result_pixels):
        r, g, b, a = pixel
        brightness = gray_pixels[i]
        
        if a > 0:  # Если пиксель не прозрачный
            # АГРЕССИВНО: удаляем все что светлее 130 (клетчатая бумага, линии)
            # Только очень темные пиксели (< 90) или пиксели рядом с темными сохраняем
            if brightness > 130:
                # Проверяем есть ли рядом темные пиксели
                y_pos = i // width
                x_pos = i % width
                has_dark_nearby = False
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x_pos + dx, y_pos + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            n_idx = ny * width + nx
                            n_brightness = gray_pixels[n_idx]
                            if n_brightness < 90:  # Очень темный сосед (текст) - более строгий порог
                                has_dark_nearby = True
                                break
                    if has_dark_nearby:
                        break
                
                if not has_dark_nearby:
                    # Нет темных соседей - это фон, удаляем
                    cleaned_pixels.append((255, 255, 255, 0))
                else:
                    # Есть темные соседи - это край текста, сохраняем
                    cleaned_pixels.append(pixel)
            else:
                # Темный пиксель - текст, сохраняем
                cleaned_pixels.append(pixel)
        else:
            cleaned_pixels.append(pixel)
    
    result.putdata(cleaned_pixels)
    
    # ФИНАЛЬНАЯ АГРЕССИВНАЯ ОЧИСТКА:
    # Удаляем все что не является явным текстом
    final_pixels = []
    for i, pixel in enumerate(cleaned_pixels):
        r, g, b, a = pixel
        brightness = gray_pixels[i]
        
        if a > 0:  # Если пиксель не прозрачный
            # ФИНАЛЬНАЯ ПРОВЕРКА: удаляем все что светлее 120
            # Только очень темные пиксели (< 80) или пиксели рядом с очень темными сохраняем
            if brightness > 120:
                # Проверяем есть ли рядом ОЧЕНЬ темные пиксели (явный текст)
                y_pos = i // width
                x_pos = i % width
                has_very_dark_nearby = False
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x_pos + dx, y_pos + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            n_idx = ny * width + nx
                            n_brightness = gray_pixels[n_idx]
                            if n_brightness < 80:  # Очень темный сосед (явный текст)
                                has_very_dark_nearby = True
                                break
                    if has_very_dark_nearby:
                        break
                
                if not has_very_dark_nearby:
                    # Нет очень темных соседей - это фон (клетки), удаляем
                    final_pixels.append((255, 255, 255, 0))
                else:
                    # Есть очень темные соседи - это край текста, сохраняем
                    final_pixels.append(pixel)
            else:
                # Темный пиксель - текст, сохраняем
                final_pixels.append(pixel)
        else:
            final_pixels.append(pixel)
    
    result.putdata(final_pixels)
    
    # Морфологическая очистка для удаления мелких артефактов фона
    mask = Image.new('L', (width, height), 0)
    mask_pixels = [255 if p[3] > 0 else 0 for p in final_pixels]
    mask.putdata(mask_pixels)
    
    # Удаляем маленькие островки (артефакты фона) - более агрессивно
    mask = mask.filter(ImageFilter.MaxFilter(size=3))  # Размер должен быть нечетным (1, 3, 5...)
    mask = mask.filter(ImageFilter.MinFilter(size=3))
    
    # Легкое размытие для сглаживания краев текста
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    result = Image.composite(result, Image.new('RGBA', (width, height), (255, 255, 255, 0)), mask)
    
    return result

def detect_edges(image):
    """Обнаружение краев/границ для защиты объектов от удаления"""
    width, height = image.size
    if image.mode != 'L':
        gray = image.convert('L')
    else:
        gray = image
    
    # Создаем карту краев используя разницу яркости
    edge_pixels_list = [0] * (width * height)
    gray_pixels = list(gray.getdata())
    
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            idx = y * width + x
            center = gray_pixels[idx]
            
            # Проверяем соседние пиксели
            neighbors = [
                gray_pixels[(y-1) * width + x],      # верх
                gray_pixels[(y+1) * width + x],      # низ
                gray_pixels[y * width + (x-1)],      # лево
                gray_pixels[y * width + (x+1)],      # право
            ]
            
            # Вычисляем максимальную разницу с соседями
            max_diff = max(abs(center - n) for n in neighbors)
            
            # Если есть сильный контраст - это граница объекта
            edge_pixels_list[idx] = min(255, max_diff * 2)
    
    return edge_pixels_list

def remove_background_smart(image, ai_guidance=None, user_prompt="", original_image=None, selected_region=None):
    """
    Улучшенное удаление фона - защищает объекты от удаления через анализ границ
    Специальная обработка для текста - удаляет фон листа, оставляет только текст
    
    Args:
        image: изображение для обработки (может быть обрезанным)
        original_image: исходное полное изображение (для анализа фона при ручном выборе)
        selected_region: кортеж (x1, y1, x2, y2) выбранной области в исходном изображении
    """
    width, height = image.size
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    pixels = list(image.getdata())
    
    # Проверяем является ли это извлечением текста
    prompt_lower = user_prompt.lower() if user_prompt else ""
    is_text_extraction = any(word in prompt_lower for word in ['текст', 'надпись', 'text', 'inscription', 
                                                                'только текст', 'only text', 'извлеки текст'])
    
    # Для текста используем специальный алгоритм
    if is_text_extraction:
        return remove_background_for_text(image)
    
    # ОБНАРУЖАЕМ ГРАНИЦЫ ОБЪЕКТОВ - это защитит их от удаления
    edge_pixels_list = detect_edges(image)
    
    # Анализируем края для определения цвета фона
    # ВАЖНО: если есть исходное изображение и выбранная область - анализируем фон ВНЕ выбранной области!
    edge_colors = []
    edge_zone = 0.15  # 15% от края - зона для анализа фона
    
    # Если есть исходное изображение и выбранная область - используем его для анализа фона
    if original_image is not None and selected_region is not None:
        orig_width, orig_height = original_image.size
        if original_image.mode != 'RGBA':
            original_image = original_image.convert('RGBA')
        orig_pixels = list(original_image.getdata())
        x1, y1, x2, y2 = selected_region
        
        # Анализируем края ИСХОДНОГО изображения, но ИСКЛЮЧАЯ выбранную область
        edge_width = int(orig_width * edge_zone)
        edge_height = int(orig_height * edge_zone)
        
        for y in range(orig_height):
            for x in range(orig_width):
                # Только края исходного изображения
                if (x < edge_width or x >= orig_width - edge_width or 
                    y < edge_height or y >= orig_height - edge_height):
                    # ИСКЛЮЧАЕМ выбранную область - она может быть объектом!
                    if not (x1 <= x <= x2 and y1 <= y <= y2):
                        edge_colors.append(orig_pixels[y * orig_width + x])
    else:
        # Стандартный анализ - края текущего изображения
        edge_width = int(width * edge_zone)
        edge_height = int(height * edge_zone)
        
        for y in range(height):
            for x in range(width):
                # Только края
                if (x < edge_width or x >= width - edge_width or 
                    y < edge_height or y >= height - edge_height):
                    edge_colors.append(pixels[y * width + x])
    
    edge_width = int(width * edge_zone)
    edge_height = int(height * edge_zone)
    
    for y in range(height):
        for x in range(width):
            # Только края
            if (x < edge_width or x >= width - edge_width or 
                y < edge_height or y >= height - edge_height):
                edge_colors.append(pixels[y * width + x])
    
    # Определяем фон по краям
    edge_colors_rgb = [(r, g, b) for r, g, b, a in edge_colors]
    if edge_colors_rgb:
        most_common_colors = Counter(edge_colors_rgb).most_common(3)
        bg_colors = [color for color, count in most_common_colors]
    else:
        bg_colors = [(255, 255, 255), (240, 240, 240), (200, 200, 200)]
    
    # Анализируем промпт пользователя для понимания задачи
    aggressive_mode = False
    if user_prompt:
        prompt_lower = user_prompt.lower()
        # Если пользователь явно просит удалить фон, быть более агрессивным
        if any(word in prompt_lower for word in ['убери фон', 'удали фон', 'remove background', 
                                                  'убери задний', 'удали задний', 'серый фон', 'gray background']):
            aggressive_mode = True
    
    # Анализируем однородность фона для улучшения удаления
    # Проверяем похожие цвета по всей области (для определения однородного фона майки)
    bg_color_variations = []
    for bg_r, bg_g, bg_b in bg_colors:
        # Находим все пиксели похожие на этот фон
        similar_count = 0
        for pixel in pixels:
            r, g, b, _ = pixel
            dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            if dist < 40:  # Похожий цвет
                similar_count += 1
        bg_color_variations.append((bg_r, bg_g, bg_b, similar_count))
    
    # Выбираем самый распространенный цвет фона
    bg_color_variations.sort(key=lambda x: x[3], reverse=True)
    primary_bg_color = bg_color_variations[0][:3] if bg_color_variations else bg_colors[0]
    
    new_pixels = []
    
    for i, pixel in enumerate(pixels):
        r, g, b, a = pixel
        y_pos = i // width
        x_pos = i % width
        
        # Вычисляем расстояние до ближайшего края
        dist_x = min(x_pos, width - x_pos)
        dist_y = min(y_pos, height - y_pos)
        dist_to_edge = min(dist_x, dist_y)
        
        # Нормализуем расстояние (0 = на краю, 1 = в центре)
        max_dist = min(width, height) / 2
        normalized_dist = dist_to_edge / max_dist if max_dist > 0 else 0
        
        # Проверяем расстояние до цвета фона
        min_distance = float('inf')
        for bg_r, bg_g, bg_b in bg_colors:
            color_distance = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            min_distance = min(min_distance, color_distance)
        
        # ЗАЩИТА ОБЪЕКТОВ: проверяем карту границ
        edge_strength = edge_pixels_list[i] if i < len(edge_pixels_list) else 0
        
        # Улучшенный АДАПТИВНЫЙ ПОРОГ с защитой объектов:
        # - На краях изображения (0-20%): агрессивное удаление ТОЛЬКО если нет границы объекта
        # - Средняя зона (20-60%): консервативное удаление
        # - В центре (60-100%): очень консервативное - почти не удаляем
        
        # Улучшенные пороги для более агрессивного удаления однородного фона
        if normalized_dist < 0.2:
            # Край изображения - очень агрессивное удаление однородного фона
            threshold = 40 if aggressive_mode else 35  # Более агрессивно для удаления фона
        elif normalized_dist < 0.5:
            # Средняя зона - агрессивное удаление однородного фона
            base_threshold = 35 if aggressive_mode else 40
            threshold = base_threshold + (normalized_dist - 0.2) * 10  # 35/40 до 38/43
        else:
            # Центр - умеренное удаление, но проверяем однородность
            threshold = 40 if aggressive_mode else 45
        
        # Если пиксель на границе объекта - НИКОГДА не удаляем!
        if edge_strength > 30:  # Сильная граница - защищаем
            is_background = False
        elif edge_strength > 15:  # Средняя граница - защищаем
            is_background = False
        else:
            # Нет границы - проверяем как обычно
            is_background = min_distance < threshold
            
            # Дополнительно: если цвет очень близок к основному фону - удаляем даже в центре
            if not is_background:
                distance_to_primary = ((r - primary_bg_color[0]) ** 2 + 
                                       (g - primary_bg_color[1]) ** 2 + 
                                       (b - primary_bg_color[2]) ** 2) ** 0.5
                # Если очень близко к однородному фону (фон майки) - удаляем
                if distance_to_primary < 30:  # Более агрессивный порог для однородного фона
                    is_background = True
        
        # Дополнительная защита: анализ соседних пикселей
        # Если вокруг много разных цветов (не фона) - это часть объекта
        if is_background:  # Только если уже решили удалить
            neighbor_colors = []
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x_pos + dx, y_pos + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        n_idx = ny * width + nx
                        nr, ng, nb, _ = pixels[n_idx]
                        # Проверяем расстояние до фона
                        n_dist = float('inf')
                        for bg_r, bg_g, bg_b in bg_colors:
                            n_color_dist = ((nr - bg_r) ** 2 + (ng - bg_g) ** 2 + (nb - bg_b) ** 2) ** 0.5
                            n_dist = min(n_dist, n_color_dist)
                        neighbor_colors.append(n_dist)
            
            if neighbor_colors:
                # Если большинство соседей НЕ фон - это часть объекта!
                non_bg_neighbors = sum(1 for d in neighbor_colors if d > 35)
                if non_bg_neighbors >= len(neighbor_colors) * 0.4:  # 40% соседей не фон
                    is_background = False  # Защищаем - это часть объекта
        
        # Дополнительная проверка: явный однотонный фон (более агрессивно)
        if not is_background:
            # Очень светлый однотонный фон (белый/светло-серый) - удаляем если нет границы
            if edge_strength < 15 and r > 240 and g > 240 and b > 240 and abs(r - g) < 15 and abs(g - b) < 15:
                is_background = True
            # Очень темный однотонный фон (черный/темно-серый) - удаляем если нет границы
            elif edge_strength < 15 and r < 30 and g < 30 and b < 30:
                is_background = True
            # Средне-серый однотонный фон (серый/бирюзовый фон майки) - удаляем более агрессивно
            elif (edge_strength < 15 and abs(r - g) < 25 and abs(g - b) < 25 and 
                  140 < (r + g + b) / 3 < 210):  # Расширенный диапазон для серого фона
                is_background = True
        
        if is_background:
            new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append((r, g, b, 255))
    
    result = Image.new('RGBA', (width, height))
    result.putdata(new_pixels)
    
    # Создаем маску и улучшаем удаление фона
    mask = Image.new('L', (width, height), 0)
    mask_pixels = [255 if p[3] > 0 else 0 for p in new_pixels]
    mask.putdata(mask_pixels)
    
    # Морфологическая очистка для удаления мелких артефактов фона
    mask = mask.filter(ImageFilter.MaxFilter(size=1))
    mask = mask.filter(ImageFilter.MinFilter(size=1))
    
    # Легкое размытие краев маски для плавности
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    result = Image.composite(result, Image.new('RGBA', (width, height), (255, 255, 255, 0)), mask)
    
    return result

# HTML шаблон будет такой же, но с добавлением поля для ввода промпта
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Извлечение принтов с ИИ</title>
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
        .button:hover { background: #1976D2; }
        .button.success { background: #4CAF50; }
        .button.danger { background: #F44336; }
        #imageCanvas, #resultCanvas {
            border: 2px solid #ddd;
            border-radius: 5px;
            cursor: crosshair;
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
        input[type="file"], textarea {
            display: none;
        }
        .ai-section {
            background: #fff3e0;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            border: 2px solid #ff9800;
        }
        .ai-section textarea {
            display: block;
            width: 100%;
            min-height: 80px;
            padding: 10px;
            margin: 10px 0;
            border: 2px solid #ff9800;
            border-radius: 5px;
            font-size: 14px;
        }
        .method-selector {
            margin: 20px 0;
            text-align: center;
        }
        .method-selector label {
            margin: 0 15px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Извлечение принтов и надписей (с ИИ)</h1>
        
        <div class="method-selector">
            <label><input type="radio" name="method" value="manual" checked> Ручной выбор области</label>
            <label><input type="radio" name="method" value="ai" id="aiMethodRadio"> ИИ по описанию</label>
        </div>
        
        <div id="aiSection" class="ai-section" style="display:none;">
            <h3>🤖 ИИ извлечение</h3>
            <p>Опишите что нужно извлечь из изображения:</p>
            <textarea id="aiPrompt" placeholder="Например: 'надпись LINKIN PARK', 'картинка с женщиной', 'логотип Олимпиада-80' и т.д."></textarea>
            <button class="button success" onclick="extractWithAI()">🔍 ИИ: Извлечь по описанию</button>
            <div id="aiStatus"></div>
        </div>
        
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
        let scale = 1;
        let selection = {x1: 0, y1: 0, x2: 0, y2: 0};
        let originalWidth = 0, originalHeight = 0;
        
        // Проверка доступности ИИ при загрузке страницы
        let aiAvailable = false;
        fetch('/check_ai')
        .then(r => r.json())
        .then(data => {
            aiAvailable = data.available || false;
            if (!aiAvailable) {
                // Отключаем ИИ режим если недоступен
                const aiRadio = document.getElementById('aiMethodRadio');
                if (aiRadio) {
                    aiRadio.disabled = true;
                    aiRadio.parentElement.innerHTML += '<span style="color:red;"> (недоступно)</span>';
                }
                if (data.has_openai && !data.has_key) {
                    document.getElementById('aiStatus').innerHTML = 
                        '<div style="color:orange; margin-top:10px;">⚠ OpenAI установлен, но API ключ не найден. Создайте файл ~/.openai_api_key</div>';
                } else if (!data.has_openai) {
                    document.getElementById('aiStatus').innerHTML = 
                        '<div style="color:red; margin-top:10px;">❌ OpenAI не установлен. Установите: pip3 install openai</div>';
                }
            }
        })
        .catch(err => {
            console.log('ИИ проверка не удалась:', err);
        });
        
        document.querySelectorAll('input[name="method"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'ai' && !aiAvailable) {
                    alert('ИИ функции недоступны. Проверьте что OpenAI установлен и API ключ настроен.');
                    document.querySelector('input[name="method"][value="manual"]').checked = true;
                    document.getElementById('aiSection').style.display = 'none';
                    return;
                }
                document.getElementById('aiSection').style.display = 
                    this.value === 'ai' ? 'block' : 'none';
            });
        });
        
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
                originalWidth = data.width;
                originalHeight = data.height;
                
                image.onload = function() {
                    canvas = document.createElement('canvas');
                    canvas.id = 'imageCanvas';
                    ctx = canvas.getContext('2d');
                    
                    const maxWidth = 1000;
                    const maxHeight = 800;
                    scale = Math.min(maxWidth / data.width, maxHeight / data.height, 1);
                    
                    canvas.width = data.width * scale;
                    canvas.height = data.height * scale;
                    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                    
                    document.getElementById('imageContainer').innerHTML = '';
                    document.getElementById('imageContainer').appendChild(canvas);
                    document.getElementById('info').innerHTML = 
                        'Изображение загружено. Выберите метод извлечения.';
                    
                    const extractBtn = document.createElement('button');
                    extractBtn.className = 'button success';
                    extractBtn.textContent = '🔍 Извлечь принт (ручной)';
                    extractBtn.onclick = extractRegion;
                    extractBtn.style.display = 'block';
                    extractBtn.style.margin = '20px auto';
                    document.getElementById('imageContainer').appendChild(extractBtn);
                    
                    setupCanvasEvents();
                };
            });
        }
        
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
                
                selection.x1 = Math.round(Math.min(startX, currentX));
                selection.y1 = Math.round(Math.min(startY, currentY));
                selection.x2 = Math.round(Math.max(startX, currentX));
                selection.y2 = Math.round(Math.max(startY, currentY));
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
                
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
            
            extractAndProcess(selection);
        }
        
        function extractWithAI() {
            const prompt = document.getElementById('aiPrompt').value.trim();
            if (!prompt) {
                alert('Введите описание что нужно извлечь!');
                return;
            }
            
            document.getElementById('aiStatus').innerHTML = '⏳ ИИ анализирует изображение...';
            
            fetch('/extract_ai', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: prompt})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success && data.coords) {
                    document.getElementById('aiStatus').innerHTML = 
                        '✓ Область определена ИИ. Обрабатываю...';
                    
                    // Автоматически извлекаем
                    setTimeout(() => {
                        extractAndProcess(data.coords);
                    }, 500);
                } else {
                    document.getElementById('aiStatus').innerHTML = 
                        '❌ Ошибка: ' + (data.error || 'Не удалось определить область');
                }
            })
            .catch(err => {
                document.getElementById('aiStatus').innerHTML = 
                    '❌ Ошибка: ' + err.message;
            });
        }
        
        function extractAndProcess(coords) {
            fetch('/extract', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(coords)
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
                alert('Ошибка: ' + err.message);
            });
        }
        
        function downloadResult() {
            window.location.href = '/result';
        }
    </script>
</body>
</html>'''

class WebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
        elif path == '/check_ai':
            # Проверка доступности ИИ
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Используем глобальные переменные модуля
            has_key = load_openai_key() if HAS_OPENAI else False
            
            self.wfile.write(json.dumps({
                'has_openai': HAS_OPENAI,
                'has_key': has_key,
                'available': HAS_OPENAI and has_key
            }).encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        elif self.path == '/extract':
            self.extract_region()
        elif self.path == '/extract_ai':
            self.extract_with_ai()
        else:
            self.send_error(404)
    
    def send_image(self):
        global global_image
        if global_image is None:
            self.send_error(404)
            return
        
        try:
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
        global global_image
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise ValueError("Нет данных")
            
            post_data = self.rfile.read(content_length)
            
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(b'--' + boundary)
                
                for part in parts:
                    if b'Content-Type:' in part:
                        header_end = part.find(b'\r\n\r\n')
                        if header_end > 0:
                            file_data = part[header_end+4:].rstrip(b'\r\n')
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
    
    def extract_with_ai(self):
        global global_image, global_prompt
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            prompt = data.get('prompt', '')
            if not prompt:
                raise ValueError("Промпт не указан")
            
            # Сохраняем промпт для использования в удалении фона
            global_prompt = prompt
            
            if global_image is None:
                raise ValueError("Изображение не загружено")
            
            # Сохраняем временное изображение
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                global_image.save(tmp.name, 'PNG')
                tmp_path = tmp.name
            
            # Используем ИИ для определения области
            coords, error = extract_with_ai(tmp_path, prompt)
            
            # Удаляем временный файл
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            if error:
                raise ValueError(error)
            
            if coords:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'coords': coords
                }).encode())
            else:
                raise ValueError("ИИ не смог определить область")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())
    
    def extract_region(self):
        global global_image, global_result, global_prompt
        
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
            
            cropped = global_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
            # Используем улучшенный алгоритм удаления фона
            # ВАЖНО: передаем исходное изображение и координаты выбранной области,
            # чтобы алгоритм анализировал фон ВНЕ выбранной области, а не края обрезанного изображения
            result = remove_background_smart(
                cropped, 
                user_prompt=global_prompt,
                original_image=global_image,
                selected_region=(x1, y1, x2, y2)
            )
            global_result = result
            # Очищаем промпт после использования (для следующего запроса)
            global_prompt = ""
            
            buffer = io.BytesIO()
            result.save(buffer, format='PNG')
            img_data = base64.b64encode(buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'data': img_data,
                'width': result.size[0],
                'height': result.size[1]
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def get_result(self):
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
    
    def log_message(self, format, *args):
        pass

def start_server(port=8000):
    server = HTTPServer(('localhost', port), WebHandler)
    print(f"\n{'='*60}")
    print("  🌐 ВЕБ-ИНТЕРФЕЙС С ИИ ПОДДЕРЖКОЙ")
    print("="*60)
    print(f"\n✓ Сервер запущен на: http://localhost:{port}")
    print("  Браузер должен открыться автоматически...")
    
    if HAS_OPENAI:
        if load_openai_key():
            print("  ✓ OpenAI API ключ найден - ИИ функции доступны")
        else:
            print("  ⚠ OpenAI API ключ не найден")
            print("    Создайте файл ~/.openai_api_key с вашим API ключом")
            print("    Или установите переменную окружения: export OPENAI_API_KEY='your-key'")
    else:
        print("  ⚠ OpenAI не установлен - ИИ функции недоступны")
        print("    Установите: pip3 install openai")
    
    print("\n  Для остановки нажмите Ctrl+C\n")
    
    threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nОстановка сервера...")
        server.shutdown()

def main():
    try:
        start_server()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
