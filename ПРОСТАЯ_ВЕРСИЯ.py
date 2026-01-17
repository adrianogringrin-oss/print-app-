#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ПРОСТАЯ РАБОТАЮЩАЯ ВЕРСИЯ программы извлечения принтов
Просто запустите и следуйте инструкциям
"""

import sys
import os

print("=" * 60)
print("ПРОГРАММА ДЛЯ ИЗВЛЕЧЕНИЯ ПРИНТОВ С ОДЕЖДЫ")
print("=" * 60)
print()

# Проверка и установка модулей
print("Проверка модулей...")
missing_modules = []

try:
    from PIL import Image, ImageEnhance, ImageFilter
    print("✓ Pillow установлен")
except ImportError:
    print("✗ Pillow НЕ установлен")
    missing_modules.append("Pillow")

try:
    import numpy as np
    print("✓ numpy установлен")
except ImportError:
    print("✗ numpy НЕ установлен")
    missing_modules.append("numpy")

try:
    import cv2
    print("✓ OpenCV установлен")
    has_opencv = True
except ImportError:
    print("⚠ OpenCV НЕ установлен (будет использован простой метод)")
    has_opencv = False

if missing_modules:
    print()
    print("❌ ОТСУТСТВУЮТ МОДУЛИ:", ", ".join(missing_modules))
    print()
    print("Установите их командой:")
    print(f"  python3 -m pip install {' '.join(missing_modules)}")
    if not has_opencv:
        print("  python3 -m pip install opencv-python")
    print()
    print("Или запустите скрипт установки:")
    print("  ./install_dependencies.sh")
    print()
    input("Нажмите Enter для выхода...")
    sys.exit(1)

print()
print("=" * 60)
print("ВСЕ МОДУЛИ УСТАНОВЛЕНЫ!")
print("=" * 60)
print()

# Функция удаления фона
def remove_background(image_path, output_path):
    """Удаление фона из изображения"""
    try:
        print(f"Обработка: {os.path.basename(image_path)}")
        
        if has_opencv:
            # Метод с OpenCV (лучше)
            try:
                from PIL import Image
                
                # Открываем изображение
                img = Image.open(image_path)
                print(f"  Размер оригинала: {img.size[0]}x{img.size[1]}")
                img = img.convert('RGBA')
                img_array = np.array(img)
                
                # Конвертируем в grayscale
                gray = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY)
                
                # Адаптивное пороговое значение
                adaptive = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, 11, 2
                )
                
                # Простой порог (удаляем светлый фон)
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
                
                # Комбинируем
                final_mask = cv2.bitwise_and(mask, adaptive)
                
                # Улучшаем маску
                kernel = np.ones((5, 5), np.uint8)
                final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
                final_mask = cv2.GaussianBlur(final_mask, (5, 5), 0)
                
                # Применяем маску
                img_array[:, :, 3] = final_mask
                result = Image.fromarray(img_array, 'RGBA')
                
                # Сохраняем файл
                result.save(output_path, "PNG", optimize=True)
                
                # Проверяем, что файл сохранился
                if not os.path.exists(output_path):
                    return False, "Файл не был сохранен"
                
                return True, None
            except Exception as e:
                return False, f"Ошибка OpenCV метода: {str(e)}"
        else:
            # Простой метод с PIL
            try:
                from PIL import Image
                
                # Открываем изображение
                img = Image.open(image_path)
                print(f"  Размер оригинала: {img.size[0]}x{img.size[1]}")
                img = img.convert('RGBA')
                img_array = np.array(img)
                
                # Средняя яркость
                gray = img_array[:, :, :3].mean(axis=2)
                
                # Маска: все темнее 200 - это принт
                mask = gray < 200
                
                # Создаем альфа-канал
                alpha = np.ones((img_array.shape[0], img_array.shape[1]), dtype=np.uint8) * 255
                alpha[mask] = 255  # Принт - непрозрачный
                alpha[~mask] = 0   # Фон - прозрачный
                
                img_array[:, :, 3] = alpha
                result = Image.fromarray(img_array, 'RGBA')
                
                # Сохраняем файл
                result.save(output_path, "PNG", optimize=True)
                
                # Проверяем, что файл сохранился
                if not os.path.exists(output_path):
                    return False, "Файл не был сохранен"
                
                return True, None
            except Exception as e:
                return False, f"Ошибка PIL метода: {str(e)}"
    except Exception as e:
        return False, f"Критическая ошибка: {str(e)}"

def enhance_image(image_path, output_path):
    """Улучшение качества"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        img = Image.open(image_path)
        
        # Резкость
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        # Контраст
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Фильтр
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        img.save(output_path, "PNG")
        return True, None
    except Exception as e:
        return False, str(e)

# Основной цикл
while True:
    print()
    print("-" * 60)
    image_path = input("Введите путь к изображению (или 'q' для выхода): ").strip()
    
    # Убираем кавычки если есть
    if image_path.startswith('"') and image_path.endswith('"'):
        image_path = image_path[1:-1]
    if image_path.startswith("'") and image_path.endswith("'"):
        image_path = image_path[1:-1]
    
    if image_path.lower() == 'q':
        print("Выход из программы")
        break
    
    # Проверка существования пути
    if not os.path.exists(image_path):
        print(f"❌ Путь не найден: {image_path}")
        print("Проверьте правильность пути к файлу")
        continue
    
    # Проверка, что это файл, а не папка
    if os.path.isdir(image_path):
        print(f"❌ Ошибка: Это папка, а не файл!")
        print(f"   Путь: {image_path}")
        print()
        print("Укажите полный путь к ФАЙЛУ изображения, например:")
        print(f"   {image_path}имя_файла.jpg")
        print()
        continue
    
    if not os.path.isfile(image_path):
        print(f"❌ Ошибка: Не удалось определить файл: {image_path}")
        continue
    
    # Проверка расширения файла
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif']:
        print(f"⚠ Предупреждение: Нестандартное расширение файла: {ext}")
        print("Продолжить? (y/n): ", end='')
        response = input().strip().lower()
        if response != 'y':
            continue
    
    # Определяем путь для сохранения
    input_path = os.path.splitext(image_path)[0]
    output_path = f"{input_path}_processed.png"
    
    print()
    print("Обработка изображения...")
    print(f"Результат будет сохранен: {output_path}")
    print()
    
    # Удаление фона
    print("1. Удаление фона...")
    success, error = remove_background(image_path, output_path)
    
    if not success:
        print(f"❌ Ошибка при удалении фона: {error}")
        print("Попробуйте другое изображение")
        continue
    
    # Проверяем, что файл действительно сохранился
    if not os.path.exists(output_path):
        print(f"❌ Ошибка: Файл не был сохранен: {output_path}")
        continue
    
    file_size = os.path.getsize(output_path)
    if file_size == 0:
        print(f"⚠ Предупреждение: Файл сохранен, но пустой (0 байт)")
        os.remove(output_path)
        continue
    
    print(f"✓ Фон удален! Файл сохранен ({file_size} байт)")
    
    # Улучшение качества (опционально)
    enhance = input("\nУлучшить качество изображения? (y/n): ").strip().lower()
    if enhance == 'y':
        print("2. Улучшение качества...")
        temp_path = output_path + ".temp"
        try:
            success, error = enhance_image(output_path, temp_path)
            if success and os.path.exists(temp_path):
                # Заменяем оригинал улучшенной версией
                os.replace(temp_path, output_path)
                new_size = os.path.getsize(output_path)
                print(f"✓ Качество улучшено! Размер файла: {new_size} байт")
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"⚠ Ошибка улучшения: {error}")
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"⚠ Ошибка улучшения: {e}")
    
    # Финальная проверка
    if not os.path.exists(output_path):
        print(f"❌ Критическая ошибка: Файл исчез: {output_path}")
        continue
    
    final_size = os.path.getsize(output_path)
    
    print()
    print("=" * 60)
    print("✅ ГОТОВО! Результат успешно сохранен:")
    print(f"   {output_path}")
    print(f"   Размер файла: {final_size} байт")
    print("=" * 60)
    print()
    
    # Предлагаем открыть файл
    open_file = input("Открыть обработанное изображение? (y/n): ").strip().lower()
    if open_file == 'y':
        try:
            os.system(f'open "{output_path}"')
            print("✓ Изображение открыто")
        except:
            print("⚠ Не удалось открыть файл автоматически")

print("\nСпасибо за использование программы!")
