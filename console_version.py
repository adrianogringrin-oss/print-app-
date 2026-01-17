#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Консольная версия программы для извлечения принтов
Работает БЕЗ GUI, используя только консоль
"""

import sys
import os
from pathlib import Path

def lazy_import_modules():
    """Ленивая загрузка модулей"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        return True, Image, ImageEnhance, ImageFilter, None
    except ImportError as e:
        return False, None, None, None, str(e)

def remove_background_pil(image_path, output_path, threshold=50):
    """Удаление фона используя только PIL (без OpenCV)"""
    try:
        from PIL import Image
        import numpy as np
        
        # Открываем изображение
        img = Image.open(image_path).convert('RGBA')
        img_array = np.array(img)
        
        # Простой алгоритм удаления фона на основе яркости
        # Предполагаем, что фон светлее принта
        gray = img_array[:, :, :3].mean(axis=2)  # Средняя яркость
        mask = gray < (255 - threshold)  # Все темнее порога - принт
        
        # Создаем альфа-канал
        alpha = np.ones((img_array.shape[0], img_array.shape[1]), dtype=np.uint8) * 255
        alpha[mask] = 255
        alpha[~mask] = 0
        
        # Применяем маску
        img_array[:, :, 3] = alpha
        result = Image.fromarray(img_array, 'RGBA')
        
        # Сохраняем результат
        result.save(output_path, "PNG")
        return True, None
        
    except Exception as e:
        return False, str(e)

def enhance_image(image_path, output_path, sharpness=1.5, contrast=1.2):
    """Улучшение качества изображения"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        
        img = Image.open(image_path)
        
        # Улучшение резкости
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)
        
        # Улучшение контраста
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        
        # Дополнительное улучшение резкости
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        img.save(output_path, "PNG")
        return True, None
        
    except Exception as e:
        return False, str(e)

def main():
    """Главная функция консольной версии"""
    print("=" * 60)
    print("Консольная версия программы извлечения принтов")
    print("=" * 60)
    print()
    
    # Проверяем доступность модулей
    print("Проверка модулей...")
    modules_ok, Image, ImageEnhance, ImageFilter, error = lazy_import_modules()
    
    if not modules_ok:
        print(f"❌ Ошибка: Не удалось загрузить PIL/Pillow: {error}")
        print()
        print("Установите Pillow:")
        print("  pip3 install Pillow")
        return
    
    print("✓ Pillow загружен")
    
    # Пробуем загрузить numpy и cv2 (опционально)
    try:
        import numpy as np
        import cv2
        print("✓ OpenCV и numpy доступны")
        has_opencv = True
    except ImportError:
        print("⚠ OpenCV недоступен, будет использован простой алгоритм PIL")
        has_opencv = False
    
    print()
    print("=" * 60)
    print("Использование:")
    print("=" * 60)
    print("1. Введите путь к изображению")
    print("2. Программа обработает его и сохранит результат")
    print()
    
    # Запрашиваем путь к изображению
    while True:
        image_path = input("Введите путь к изображению (или 'q' для выхода): ").strip()
        
        if image_path.lower() == 'q':
            print("Выход из программы")
            break
        
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            continue
        
        # Определяем путь для сохранения
        input_path = Path(image_path)
        output_path = input_path.parent / f"{input_path.stem}_processed.png"
        
        print(f"\nОбработка изображения: {image_path}")
        print(f"Результат будет сохранен: {output_path}")
        
        # Удаление фона
        print("\n1. Удаление фона...")
        if has_opencv:
            # Используем более продвинутый метод
            try:
                img = Image.open(image_path).convert('RGBA')
                img_array = np.array(img)
                
                # Используем простой алгоритм
                gray = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY)
                _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
                
                img_array[:, :, 3] = mask
                result = Image.fromarray(img_array, 'RGBA')
                result.save(output_path, "PNG")
                print("✓ Фон удален (OpenCV метод)")
            except Exception as e:
                print(f"⚠ Ошибка OpenCV метода: {e}")
                print("Используется простой метод PIL...")
                success, error = remove_background_pil(image_path, str(output_path))
                if not success:
                    print(f"❌ Ошибка: {error}")
                    continue
                print("✓ Фон удален (PIL метод)")
        else:
            success, error = remove_background_pil(image_path, str(output_path))
            if not success:
                print(f"❌ Ошибка: {error}")
                continue
            print("✓ Фон удален (PIL метод)")
        
        # Улучшение качества
        enhance_choice = input("\nУлучшить качество изображения? (y/n): ").strip().lower()
        if enhance_choice == 'y':
            print("2. Улучшение качества...")
            temp_path = str(output_path)
            success, error = enhance_image(temp_path, str(output_path))
            if success:
                print("✓ Качество улучшено")
            else:
                print(f"⚠ Ошибка улучшения: {error}")
        
        print(f"\n✅ Готово! Результат сохранен: {output_path}")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
