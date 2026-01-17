#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ - только консоль, БЕЗ GUI
Работает на всех системах без проблем
"""

import sys
import os
from pathlib import Path

# Импорты
try:
    from PIL import Image
except ImportError:
    print("❌ Pillow не установлен. Установите: pip3 install Pillow")
    sys.exit(1)

def print_header():
    """Красивый заголовок"""
    print("\n" + "="*60)
    print("  🎨 ИЗВЛЕЧЕНИЕ ПРИНТОВ И НАДПИСЕЙ")
    print("="*60 + "\n")

def get_file_path():
    """Получение пути к файлу"""
    print("1️⃣  Загрузка изображения")
    print("-" * 60)
    
    while True:
        file_path = input("Введите путь к изображению (или перетащите файл сюда): ").strip()
        
        # Убираем кавычки если пользователь перетащил файл
        file_path = file_path.strip('"').strip("'")
        
        if not file_path:
            print("❌ Путь не может быть пустым!")
            continue
        
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            continue
        
        if os.path.isdir(file_path):
            print(f"❌ Это директория, а не файл!")
            continue
        
        try:
            img = Image.open(file_path)
            width, height = img.size
            print(f"✓ Изображение загружено: {os.path.basename(file_path)}")
            print(f"  Размер: {width} x {height} пикселей\n")
            return file_path, img, width, height
        except Exception as e:
            print(f"❌ Ошибка при загрузке: {e}\n")

def get_coordinates(img_width, img_height):
    """Получение координат области"""
    print("2️⃣  Выбор области для извлечения")
    print("-" * 60)
    print(f"Размер изображения: {img_width} x {img_height} пикселей")
    print("\nВведите координаты области:")
    print("  Формат: x1 y1 x2 y2")
    print(f"  Пример: 100 100 {img_width//2} {img_height//2}")
    print("  (x1, y1 - левый верхний угол)")
    print("  (x2, y2 - правый нижний угол)\n")
    
    while True:
        try:
            coords = input("Координаты: ").strip().split()
            
            if len(coords) != 4:
                print("❌ Нужно 4 числа (x1 y1 x2 y2)")
                continue
            
            x1, y1, x2, y2 = map(int, coords)
            
            # Проверяем границы
            x1 = max(0, min(x1, img_width))
            y1 = max(0, min(y1, img_height))
            x2 = max(0, min(x2, img_width))
            y2 = max(0, min(y2, img_height))
            
            if x2 <= x1:
                print("❌ x2 должно быть больше x1")
                continue
            
            if y2 <= y1:
                print("❌ y2 должно быть больше y1")
                continue
            
            print(f"✓ Область выбрана: X={x1}-{x2}, Y={y1}-{y2}")
            print(f"  Размер: {x2-x1} x {y2-y1} пикселей\n")
            return (x1, y1, x2, y2)
            
        except ValueError:
            print("❌ Введите только числа!")
        except KeyboardInterrupt:
            print("\n\nПрервано пользователем")
            sys.exit(0)

def extract_print(image, coords):
    """Извлечение принта"""
    print("3️⃣  Извлечение принта...")
    print("-" * 60)
    
    try:
        x1, y1, x2, y2 = coords
        
        # Обрезаем область
        cropped = image.crop((x1, y1, x2, y2))
        cropped = cropped.convert('RGBA')
        
        print("  Обработка изображения...")
        
        # Удаляем фон
        data = cropped.getdata()
        new_data = []
        transparent_count = 0
        
        for item in data:
            r, g, b, a = item
            # Удаляем светлый фон
            if r > 230 and g > 230 and b > 230:
                new_data.append((255, 255, 255, 0))
                transparent_count += 1
            # Удаляем темный фон
            elif r < 30 and g < 30 and b < 30:
                new_data.append((0, 0, 0, 0))
                transparent_count += 1
            else:
                new_data.append(item)
        
        cropped.putdata(new_data)
        
        width, height = cropped.size
        print(f"✓ Принт извлечен!")
        print(f"  Размер: {width} x {height} пикселей")
        print(f"  Прозрачных пикселей: {transparent_count}\n")
        
        return cropped
        
    except Exception as e:
        print(f"❌ Ошибка при извлечении: {e}")
        return None

def save_image(image):
    """Сохранение результата"""
    print("4️⃣  Сохранение результата")
    print("-" * 60)
    
    while True:
        output_path = input("Введите путь для сохранения (.png): ").strip().strip('"').strip("'")
        
        if not output_path:
            print("❌ Путь не может быть пустым!")
            continue
        
        # Добавляем расширение если нет
        if not output_path.lower().endswith('.png'):
            output_path += '.png'
        
        # Проверяем директорию
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            print(f"❌ Директория не существует: {output_dir}")
            continue
        
        try:
            image.save(output_path, "PNG", optimize=True)
            
            # Проверяем что файл сохранен
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"\n✅ ИЗОБРАЖЕНИЕ СОХРАНЕНО!")
                print(f"  Файл: {output_path}")
                print(f"  Размер: {file_size:,} байт")
                print(f"\n{'='*60}\n")
                return True
            else:
                print("❌ Файл не был сохранен!")
                
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")

def main():
    """Главная функция"""
    try:
        print_header()
        
        # Шаг 1: Загрузка
        file_path, image, img_width, img_height = get_file_path()
        
        # Шаг 2: Координаты
        coords = get_coordinates(img_width, img_height)
        
        # Шаг 3: Извлечение
        result = extract_print(image, coords)
        if result is None:
            print("\n❌ Не удалось извлечь принт")
            sys.exit(1)
        
        # Шаг 4: Сохранение
        if save_image(result):
            print("Готово! Можно использовать результат для печати.\n")
        else:
            print("\n❌ Не удалось сохранить файл")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
