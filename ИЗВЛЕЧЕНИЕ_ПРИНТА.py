#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для селективного извлечения принтов и надписей с изображений
Позволяет выбрать конкретную область (надпись, принт) и извлечь её в PNG без фона
"""

import sys
import os
from pathlib import Path

print("=" * 70)
print("  ПРОГРАММА ДЛЯ ИЗВЛЕЧЕНИЯ ПРИНТОВ И НАДПИСЕЙ")
print("=" * 70)
print()

# Проверка модулей
print("Проверка модулей...")
try:
    from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
    print("✓ Pillow установлен")
except ImportError:
    print("❌ Pillow не установлен. Установите: pip install Pillow")
    sys.exit(1)

try:
    import numpy as np
    print("✓ numpy установлен")
except ImportError:
    print("❌ numpy не установлен. Установите: pip install numpy")
    sys.exit(1)

try:
    import cv2
    print("✓ OpenCV установлен")
    has_opencv = True
except ImportError:
    print("⚠ OpenCV не установлен (будет использован простой метод)")
    has_opencv = False

print()

def select_region_interactive(image_path):
    """Интерактивный выбор области на изображении"""
    # Пробуем системный Python для tkinter
    import sys
    import subprocess
    
    # Сначала пробуем текущий Python
    try:
        from PIL import Image, ImageTk
        import tkinter as tk
    except ImportError:
        # Если не работает, пробуем системный Python
        sys_python = "/usr/bin/python3"
        if os.path.exists(sys_python):
            print("Использование системного Python для GUI...")
            script_path = os.path.abspath(__file__)
            subprocess.run([sys_python, script_path, "--select-region", image_path])
            return None
        else:
            print("❌ tkinter недоступен. Используйте ручной ввод координат.")
            return None
    
    try:
        
        # Открываем изображение
        img = Image.open(image_path)
        
        # Создаем окно для выбора
        root = tk.Tk()
        root.title("Выберите область для извлечения")
        
        # Масштабируем изображение для отображения
        display_width = 1000
        display_height = 700
        
        img_width, img_height = img.size
        scale = min(display_width / img_width, display_height / img_height, 1.0)
        display_size = (int(img_width * scale), int(img_height * scale))
        display_img = img.resize(display_size, Image.Resampling.LANCZOS)
        
        # Создаем canvas
        canvas = tk.Canvas(root, width=display_size[0], height=display_size[1], cursor="cross")
        canvas.pack()
        
        # Отображаем изображение
        photo = ImageTk.PhotoImage(display_img)
        canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.image = photo
        
        # Переменные для выбора
        start_x = start_y = end_x = end_y = None
        rect_id = None
        
        def on_button_press(event):
            nonlocal start_x, start_y, rect_id
            start_x = event.x
            start_y = event.y
            if rect_id:
                canvas.delete(rect_id)
        
        def on_move_press(event):
            nonlocal rect_id
            if start_x is not None and start_y is not None:
                if rect_id:
                    canvas.delete(rect_id)
                rect_id = canvas.create_rectangle(
                    start_x, start_y, event.x, event.y,
                    outline="red", width=2
                )
        
        def on_button_release(event):
            nonlocal end_x, end_y
            end_x = event.x
            end_y = event.y
        
        canvas.bind("<Button-1>", on_button_press)
        canvas.bind("<B1-Motion>", on_move_press)
        canvas.bind("<ButtonRelease-1>", on_button_release)
        
        # Кнопка подтверждения
        selected_region = None
        
        def confirm_selection():
            nonlocal selected_region
            if start_x is not None and start_y is not None and end_x is not None and end_y is not None:
                # Переводим координаты в масштаб оригинала
                x1 = int(min(start_x, end_x) / scale)
                y1 = int(min(start_y, end_y) / scale)
                x2 = int(max(start_x, end_x) / scale)
                y2 = int(max(start_y, end_y) / scale)
                
                # Ограничиваем границами изображения
                x1 = max(0, min(x1, img_width))
                y1 = max(0, min(y1, img_height))
                x2 = max(0, min(x2, img_width))
                y2 = max(0, min(y2, img_height))
                
                if x2 > x1 and y2 > y1:
                    selected_region = (x1, y1, x2, y2)
                    root.quit()
                else:
                    tk.messagebox.showwarning("Ошибка", "Выберите область правильно!")
            else:
                tk.messagebox.showwarning("Ошибка", "Выберите область на изображении!")
        
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Подтвердить выбор", command=confirm_selection,
                 bg="#4CAF50", fg="white", font=("Arial", 12), padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Отмена", command=lambda: root.quit(),
                 bg="#f44336", fg="white", font=("Arial", 12), padx=20, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Label(root, text="Зажмите левую кнопку мыши и выделите область для извлечения",
                font=("Arial", 10)).pack(pady=5)
        
        root.mainloop()
        root.destroy()
        
        return selected_region
        
    except Exception as e:
        print(f"⚠ Ошибка при интерактивном выборе: {e}")
        return None

def select_region_manual(image_path):
    """Ручной ввод координат области"""
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        print(f"\nРазмер изображения: {width}x{height}")
        print("\nВведите координаты области для извлечения:")
        print("(или нажмите Enter для выбора всего изображения)")
        
        try:
            x1 = input(f"X1 (левая граница, 0-{width}): ").strip()
            if not x1:
                return (0, 0, width, height)
            x1 = int(x1)
            
            y1 = input(f"Y1 (верхняя граница, 0-{height}): ").strip()
            if not y1:
                return (0, 0, width, height)
            y1 = int(y1)
            
            x2 = input(f"X2 (правая граница, {x1}-{width}): ").strip()
            if not x2:
                return (0, 0, width, height)
            x2 = int(x2)
            
            y2 = input(f"Y2 (нижняя граница, {y1}-{height}): ").strip()
            if not y2:
                return (0, 0, width, height)
            y2 = int(y2)
            
            # Проверка координат
            if x1 >= x2 or y1 >= y2:
                print("❌ Неверные координаты!")
                return None
            
            if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
                print("⚠ Координаты выходят за границы, будут обрезаны")
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
            
            return (x1, y1, x2, y2)
        except ValueError:
            print("❌ Неверный формат координат!")
            return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def extract_region_with_background_removal(image_path, region, output_path):
    """Извлечение области с удалением фона"""
    try:
        img = Image.open(image_path).convert('RGBA')
        width, height = img.size
        
        # Обрезаем область
        x1, y1, x2, y2 = region
        cropped = img.crop((x1, y1, x2, y2))
        cropped_array = np.array(cropped)
        
        print(f"  Область: {x2-x1}x{y2-y1} пикселей")
        
        if has_opencv:
            # Используем OpenCV для удаления фона
            # Конвертируем в grayscale
            gray = cv2.cvtColor(cropped_array[:, :, :3], cv2.COLOR_RGB2GRAY)
            
            # Адаптивное пороговое значение для лучшего определения границ
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Порог для удаления светлого фона
            _, mask1 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            
            # Порог для удаления темного фона (если принт светлый)
            _, mask2 = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
            
            # Комбинируем маски
            mask = cv2.bitwise_or(mask1, mask2)
            mask = cv2.bitwise_and(mask, adaptive)
            
            # Улучшаем маску
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)
            
            # Применяем маску
            cropped_array[:, :, 3] = mask
            result = Image.fromarray(cropped_array, 'RGBA')
        else:
            # Простой метод с PIL
            gray = cropped_array[:, :, :3].mean(axis=2)
            
            # Определяем порог автоматически (метод Оцу)
            # Для простоты используем фиксированный порог
            threshold = 200
            mask = gray < threshold
            
            alpha = np.ones((cropped_array.shape[0], cropped_array.shape[1]), dtype=np.uint8) * 255
            alpha[mask] = 255
            alpha[~mask] = 0
            
            cropped_array[:, :, 3] = alpha
            result = Image.fromarray(cropped_array, 'RGBA')
        
        # Сохраняем результат
        result.save(output_path, "PNG", optimize=True)
        return True, None
        
    except Exception as e:
        return False, str(e)

def enhance_extracted_image(image_path, output_path):
    """Улучшение качества извлеченного изображения"""
    try:
        img = Image.open(image_path)
        
        # Резкость
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.5)
        
        # Контраст
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # Фильтр
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
        
        img.save(output_path, "PNG", optimize=True)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """Главная функция"""
    print("=" * 70)
    print("  ИНСТРУКЦИЯ:")
    print("=" * 70)
    print("1. Загрузите изображение с принтом/надписью")
    print("2. Выберите область для извлечения (интерактивно или вручную)")
    print("3. Программа извлечет выбранную область и удалит фон")
    print("4. Результат сохранится в PNG с прозрачным фоном")
    print("=" * 70)
    print()
    
    while True:
        # Запрос пути к изображению
        image_path = input("Введите путь к изображению (или 'q' для выхода): ").strip()
        
        # Убираем кавычки
        if image_path.startswith('"') and image_path.endswith('"'):
            image_path = image_path[1:-1]
        if image_path.startswith("'") and image_path.endswith("'"):
            image_path = image_path[1:-1]
        
        if image_path.lower() == 'q':
            break
        
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            continue
        
        if not os.path.isfile(image_path):
            print(f"❌ Это папка, а не файл!")
            continue
        
        # Открываем изображение для проверки
        try:
            img = Image.open(image_path)
            print(f"✓ Изображение загружено: {img.size[0]}x{img.size[1]} пикселей")
        except Exception as e:
            print(f"❌ Ошибка открытия изображения: {e}")
            continue
        
        # Выбор метода выбора области
        print("\nВыберите способ выбора области:")
        print("1. Интерактивный (откроется окно для выделения) - требует tkinter")
        print("2. Ручной ввод координат - работает всегда")
        print("3. Извлечь всё изображение - обработает всё")
        
        choice = input("Ваш выбор (1/2/3): ").strip()
        
        region = None
        
        if choice == '1':
            print("\nОткрывается окно для выбора области...")
            try:
                region = select_region_interactive(image_path)
                if region is None:
                    print("⚠ Интерактивный выбор не удался (tkinter недоступен)")
                    print("Используйте вариант 2 (ручной ввод) или 3 (всё изображение)")
                    choice_retry = input("\nВыберите другой вариант (2/3) или Enter для пропуска: ").strip()
                    if choice_retry == '2':
                        choice = '2'
                    elif choice_retry == '3':
                        choice = '3'
                    else:
                        continue
            except Exception as e:
                print(f"⚠ Ошибка при интерактивном выборе: {e}")
                print("Используйте вариант 2 (ручной ввод) или 3 (всё изображение)")
                continue
        
        if choice == '2':
            region = select_region_manual(image_path)
        elif choice == '3':
            img = Image.open(image_path)
            region = (0, 0, img.size[0], img.size[1])
        
        if region is None:
            print("❌ Область не выбрана!")
            continue
        
        if region is None:
            print("❌ Область не выбрана!")
            continue
        
        # Определяем путь для сохранения
        input_path = os.path.splitext(image_path)[0]
        output_path = f"{input_path}_extracted.png"
        
        print(f"\nИзвлечение области...")
        print(f"Результат будет сохранен: {output_path}")
        
        # Извлекаем область
        success, error = extract_region_with_background_removal(image_path, region, output_path)
        
        if not success:
            print(f"❌ Ошибка: {error}")
            continue
        
        # Проверяем сохранение
        if not os.path.exists(output_path):
            print("❌ Файл не был сохранен!")
            continue
        
        file_size = os.path.getsize(output_path)
        print(f"✓ Область извлечена! Размер файла: {file_size} байт")
        
        # Улучшение качества
        enhance = input("\nУлучшить качество изображения? (y/n): ").strip().lower()
        if enhance == 'y':
            print("Улучшение качества...")
            temp_path = output_path + ".temp"
            success, error = enhance_extracted_image(output_path, temp_path)
            if success and os.path.exists(temp_path):
                os.replace(temp_path, output_path)
                print("✓ Качество улучшено!")
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"⚠ Ошибка улучшения: {error}")
        
        print()
        print("=" * 70)
        print("✅ ГОТОВО! Результат сохранен:")
        print(f"   {output_path}")
        print("=" * 70)
        print()
        
        # Открыть файл
        open_file = input("Открыть обработанное изображение? (y/n): ").strip().lower()
        if open_file == 'y':
            try:
                os.system(f'open "{output_path}"')
            except:
                pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
