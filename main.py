#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для извлечения принтов с одежды и обработки изображений
для печати на футболках, худи и других изделиях
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import os
from pathlib import Path

# Отложенная загрузка numpy и cv2 для избежания системных крашей на macOS
# Эти модули будут импортированы только при реальном использовании
_numpy_loaded = False
_cv2_loaded = False
np = None
cv2 = None

def lazy_import_numpy():
    """Ленивая загрузка numpy"""
    global np, _numpy_loaded
    if not _numpy_loaded:
        try:
            import numpy as _np
            np = _np
            _numpy_loaded = True
        except Exception as e:
            raise ImportError(f"Не удалось загрузить numpy: {e}")
    return np

def lazy_import_cv2():
    """Ленивая загрузка cv2"""
    global cv2, _cv2_loaded
    if not _cv2_loaded:
        try:
            import cv2 as _cv2
            cv2 = _cv2
            _cv2_loaded = True
        except Exception as e:
            raise ImportError(f"Не удалось загрузить opencv-python: {e}")
    return cv2

# rembg полностью исключен из программы из-за проблем совместимости с macOS
# Используются только методы OpenCV и GrabCut, которые работают стабильно


class PrintExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение принтов для печати")
        self.root.geometry("1000x700")
        
        self.original_image = None
        self.processed_image = None
        self.current_image_path = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        title_label = tk.Label(
            self.root, 
            text="Извлечение и обработка принтов", 
            font=("Arial", 16, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Фрейм для кнопок загрузки и сохранения
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack()
        
        tk.Button(
            control_frame,
            text="Загрузить изображение",
            command=self.load_image,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Удалить фон",
            command=self.remove_background,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Улучшить качество",
            command=self.enhance_quality,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame,
            text="Сохранить PNG",
            command=self.save_png,
            font=("Arial", 12),
            bg="#9C27B0",
            fg="white",
            padx=20,
            pady=5
        ).pack(side=tk.LEFT, padx=5)
        
        # Фрейм для параметров обработки
        params_frame = tk.LabelFrame(self.root, text="Параметры обработки", padx=10, pady=10)
        params_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Метод удаления фона
        tk.Label(params_frame, text="Метод удаления фона:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        # Определяем доступные методы
        # Используем только стабильные методы, которые работают на всех системах
        available_methods = ["opencv", "grabcut"]
        # Пользователь может использовать opencv или grabcut - они работают отлично
        
        self.bg_method_var = tk.StringVar(value=available_methods[0])
        bg_method_combo = ttk.Combobox(
            params_frame,
            textvariable=self.bg_method_var,
            values=available_methods,
            state="readonly",
            width=15
        )
        bg_method_combo.grid(row=0, column=1, padx=5)
        
        # Добавляем подсказку о методах
        hint_label = tk.Label(
            params_frame, 
            text="(opencv и grabcut работают стабильно на всех системах)",
            font=("Arial", 8),
            fg="gray"
        )
        hint_label.grid(row=0, column=2, padx=5, sticky=tk.W)
        
        # Порог для удаления фона (для OpenCV метода)
        tk.Label(params_frame, text="Порог (OpenCV):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.IntVar(value=50)
        threshold_scale = tk.Scale(
            params_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            length=200
        )
        threshold_scale.grid(row=1, column=1, padx=5)
        
        # Улучшение резкости
        tk.Label(params_frame, text="Резкость:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.sharpness_var = tk.DoubleVar(value=1.5)
        sharpness_scale = tk.Scale(
            params_frame,
            from_=0.0,
            to=3.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.sharpness_var,
            length=200
        )
        sharpness_scale.grid(row=2, column=1, padx=5)
        
        # Улучшение контраста
        tk.Label(params_frame, text="Контраст:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.contrast_var = tk.DoubleVar(value=1.2)
        contrast_scale = tk.Scale(
            params_frame,
            from_=0.0,
            to=3.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.contrast_var,
            length=200
        )
        contrast_scale.grid(row=3, column=1, padx=5)
        
        # Фрейм для изображений
        image_frame = tk.Frame(self.root)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Оригинальное изображение
        original_label_frame = tk.LabelFrame(image_frame, text="Оригинал")
        original_label_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.original_canvas = tk.Canvas(original_label_frame, bg="gray90", width=450, height=500)
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Обработанное изображение
        processed_label_frame = tk.LabelFrame(image_frame, text="Результат")
        processed_label_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.processed_canvas = tk.Canvas(processed_label_frame, bg="gray90", width=450, height=500)
        self.processed_canvas.pack(fill=tk.BOTH, expand=True)
        
    def load_image(self):
        """Загрузка изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("Все файлы", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.current_image_path = file_path
                self.original_image = Image.open(file_path)
                
                # Конвертируем в RGBA для работы с прозрачностью
                if self.original_image.mode != 'RGBA':
                    self.original_image = self.original_image.convert('RGBA')
                
                self.processed_image = self.original_image.copy()
                
                self.display_images()
                messagebox.showinfo("Успех", "Изображение загружено!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")
    
    def display_images(self):
        """Отображение изображений на канвасах"""
        # Отображение оригинального
        if self.original_image:
            self.display_image_on_canvas(self.original_image, self.original_canvas)
        
        # Отображение обработанного
        if self.processed_image:
            self.display_image_on_canvas(self.processed_image, self.processed_canvas)
    
    def display_image_on_canvas(self, image, canvas):
        """Отображение изображения на канвасе с масштабированием"""
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas.update_idletasks()
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
        
        # Масштабирование с сохранением пропорций
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создаем изображение с фоном для предпросмотра прозрачности
        if display_image.mode == 'RGBA':
            background = Image.new('RGB', display_image.size, (255, 255, 255))
            background.paste(display_image, mask=display_image.split()[3])
            display_image = background
        
        photo = ImageTk.PhotoImage(display_image)
        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor=tk.CENTER)
        canvas.image = photo  # Сохраняем ссылку
    
    def remove_background(self):
        """Удаление фона с изображения"""
        if not self.original_image:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return
        
        try:
            method = self.bg_method_var.get()
            
            # Пробуем использовать выбранный метод
            if method == "grabcut":
                # Используем GrabCut для более точного удаления
                self.remove_background_grabcut()
            else:
                # Базовый OpenCV метод
                self.remove_background_opencv()
            
            self.display_images()
            messagebox.showinfo("Успех", "Фон удален!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении фона: {str(e)}")
    
    def remove_background_grabcut(self):
        """Удаление фона с помощью GrabCut алгоритма"""
        try:
            np = lazy_import_numpy()
            cv2 = lazy_import_cv2()
        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить необходимые модули: {e}")
            return
        
        img_array = np.array(self.original_image)
        rgb = img_array[:, :, :3]
        
        # Создаем маску для GrabCut
        mask = np.zeros(rgb.shape[:2], np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        # Определяем прямоугольник вокруг центральной части (предполагаем, что принт в центре)
        height, width = rgb.shape[:2]
        rect = (int(width * 0.1), int(height * 0.1), 
                int(width * 0.8), int(height * 0.8))
        
        # Применяем GrabCut
        cv2.grabCut(rgb, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Создаем финальную маску
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')
        
        # Улучшаем маску
        kernel = np.ones((5, 5), np.uint8)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)
        mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)
        
        # Применяем маску
        rgba = img_array.copy()
        rgba[:, :, 3] = mask2
        
        self.processed_image = Image.fromarray(rgba, 'RGBA')
    
    def remove_background_opencv(self):
        """Базовое удаление фона с помощью OpenCV"""
        try:
            np = lazy_import_numpy()
            cv2 = lazy_import_cv2()
        except ImportError as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить необходимые модули: {e}")
            return
        
        img_array = np.array(self.original_image)
        threshold = self.threshold_var.get()
        
        # Создаем маску для удаления фона
        gray = cv2.cvtColor(img_array[:, :, :3], cv2.COLOR_RGB2GRAY)
        
        # Адаптивное пороговое значение для удаления однородного фона
        # Используем адаптивный метод для лучшей работы с разным освещением
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Дополнительная обработка для удаления фона
        # Предполагаем, что фон светлее принта (типично для одежды)
        _, mask1 = cv2.threshold(gray, 200 - threshold, 255, cv2.THRESH_BINARY_INV)
        _, mask2 = cv2.threshold(gray, 50 + threshold // 2, 255, cv2.THRESH_BINARY)
        
        # Комбинируем маски
        mask = cv2.bitwise_and(mask1, adaptive_thresh)
        mask = cv2.bitwise_or(mask, mask2)
        
        # Улучшаем маску морфологическими операциями
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Размываем края для плавного перехода
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        
        # Создаем RGBA изображение
        rgba = img_array.copy()
        rgba[:, :, 3] = mask
        
        self.processed_image = Image.fromarray(rgba, 'RGBA')
    
    def enhance_quality(self):
        """Улучшение качества изображения"""
        if not self.processed_image:
            if self.original_image:
                self.processed_image = self.original_image.copy()
            else:
                messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
                return
        
        try:
            img = self.processed_image.copy()
            
            # Улучшение резкости
            sharpness = self.sharpness_var.get()
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(sharpness)
            
            # Улучшение контраста
            contrast = self.contrast_var.get()
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # Дополнительное улучшение резкости через фильтр UnsharpMask
            # Этот фильтр помогает сделать края более четкими
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            # Умное увеличение разрешения (upscaling) - только если изображение маленькое
            # Для печати нужны высокие разрешения
            current_size = img.size
            max_dimension = max(current_size)
            
            # Если максимальная сторона меньше 2000px, увеличиваем в 2 раза
            # Но не превышаем 4000px для избежания огромных файлов
            if max_dimension < 2000 and max_dimension * 2 <= 4000:
                scale_factor = 2
                new_size = (current_size[0] * scale_factor, current_size[1] * scale_factor)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                messagebox.showinfo("Информация", 
                    f"Изображение увеличено с {current_size} до {new_size} для лучшего качества печати.")
            
            self.processed_image = img
            self.display_images()
            messagebox.showinfo("Успех", "Качество изображения улучшено!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при улучшении качества: {str(e)}")
    
    def save_png(self):
        """Сохранение обработанного изображения в PNG"""
        if not self.processed_image:
            messagebox.showwarning("Предупреждение", "Нет обработанного изображения для сохранения!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить PNG",
            defaultextension=".png",
            filetypes=[("PNG файлы", "*.png"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                # Убеждаемся, что изображение в формате RGBA
                if self.processed_image.mode != 'RGBA':
                    self.processed_image = self.processed_image.convert('RGBA')
                
                self.processed_image.save(file_path, "PNG", optimize=True)
                messagebox.showinfo("Успех", f"Изображение сохранено: {file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")


def main():
    """Главная функция запуска программы с безопасной обработкой ошибок"""
    try:
        # Создаем главное окно
        root = tk.Tk()
        app = PrintExtractor(root)
        # Запускаем главный цикл
        root.mainloop()
    except SystemError as e:
        # Обработка системных ошибок (включая возможные краши на macOS)
        print(f"Системная ошибка при запуске программы: {e}")
        print("Возможна проблема совместимости с macOS")
        input("Нажмите Enter для выхода...")
    except Exception as e:
        # Обработка всех остальных ошибок
        print(f"Ошибка при запуске программы: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()
