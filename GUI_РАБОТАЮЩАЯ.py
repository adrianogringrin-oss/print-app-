#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI приложение для извлечения принтов - БЕЗОПАСНАЯ ВЕРСИЯ
Ленивая загрузка всех модулей для избежания крашей
"""

import sys
import os

# Безопасная загрузка tkinter
def safe_import_tkinter():
    """Безопасная загрузка tkinter"""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
        return tk, filedialog, messagebox, ttk, None
    except ImportError as e:
        return None, None, None, None, str(e)

# Загружаем tkinter сразу (нужен для GUI)
tk, filedialog, messagebox, ttk, tk_error = safe_import_tkinter()

if tk is None:
    print(f"❌ Ошибка: tkinter недоступен: {tk_error}")
    print("\nУстановите tkinter:")
    print("  brew install python-tk@3.14")
    input("\nНажмите Enter для выхода...")
    sys.exit(1)

# Ленивая загрузка остальных модулей
_pil_loaded = False
_numpy_loaded = False
_cv2_loaded = False
Image = ImageTk = ImageEnhance = ImageFilter = None
np = None
cv2 = None

def lazy_import_pil():
    """Ленивая загрузка PIL"""
    global Image, ImageTk, ImageEnhance, ImageFilter, _pil_loaded
    if not _pil_loaded:
        try:
            from PIL import Image as _Image, ImageTk as _ImageTk
            from PIL import ImageEnhance as _ImageEnhance, ImageFilter as _ImageFilter
            Image = _Image
            ImageTk = _ImageTk
            ImageEnhance = _ImageEnhance
            ImageFilter = _ImageFilter
            _pil_loaded = True
            return True, None
        except Exception as e:
            return False, str(e)
    return True, None

def lazy_import_numpy():
    """Ленивая загрузка numpy"""
    global np, _numpy_loaded
    if not _numpy_loaded:
        try:
            import numpy as _np
            np = _np
            _numpy_loaded = True
            return True, None
        except Exception as e:
            return False, str(e)
    return True, None

def lazy_import_cv2():
    """Ленивая загрузка cv2"""
    global cv2, _cv2_loaded
    if not _cv2_loaded:
        try:
            import cv2 as _cv2
            cv2 = _cv2
            _cv2_loaded = True
            return True, None
        except Exception as e:
            return False, str(e)
    return True, None

class PrintExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение принтов и надписей")
        self.root.geometry("1200x800")
        
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.selected_region = None
        
        # Загружаем PIL для интерфейса
        success, error = lazy_import_pil()
        if not success:
            messagebox.showerror("Ошибка", f"Не удалось загрузить Pillow:\n{error}")
            sys.exit(1)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg="#2196F3", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🎨 Извлечение принтов и надписей с изображений",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2196F3"
        ).pack(pady=15)
        
        # Основной контент
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - кнопки
        left_panel = tk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_panel.pack_propagate(False)
        
        button_style = {
            "font": ("Arial", 12),
            "padx": 20,
            "pady": 10,
            "width": 25
        }
        
        tk.Button(
            left_panel,
            text="📁 Загрузить изображение",
            command=self.load_image,
            bg="#4CAF50",
            fg="white",
            **button_style
        ).pack(pady=10, fill=tk.X)
        
        self.select_btn = tk.Button(
            left_panel,
            text="✂️ Выбрать область",
            command=self.select_region,
            bg="#FF9800",
            fg="white",
            state=tk.DISABLED,
            **button_style
        )
        self.select_btn.pack(pady=10, fill=tk.X)
        
        tk.Button(
            left_panel,
            text="🔍 Извлечь принт",
            command=self.extract_print,
            bg="#2196F3",
            fg="white",
            state=tk.DISABLED,
            **button_style
        ).pack(pady=10, fill=tk.X)
        
        tk.Button(
            left_panel,
            text="✨ Улучшить качество",
            command=self.enhance_quality,
            bg="#9C27B0",
            fg="white",
            state=tk.DISABLED,
            **button_style
        ).pack(pady=10, fill=tk.X)
        
        tk.Button(
            left_panel,
            text="💾 Сохранить PNG",
            command=self.save_png,
            bg="#F44336",
            fg="white",
            state=tk.DISABLED,
            **button_style
        ).pack(pady=10, fill=tk.X)
        
        # Информация
        info_frame = tk.LabelFrame(left_panel, text="Информация", padx=10, pady=10)
        info_frame.pack(pady=20, fill=tk.X)
        
        self.info_label = tk.Label(
            info_frame,
            text="Загрузите изображение\nдля начала работы",
            font=("Arial", 10),
            justify=tk.LEFT,
            wraplength=250
        )
        self.info_label.pack()
        
        # Правая панель - изображения
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Оригинал
        orig_frame = tk.LabelFrame(right_panel, text="Оригинальное изображение", padx=10, pady=10)
        orig_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.orig_canvas = tk.Canvas(orig_frame, bg="gray90", width=550, height=600)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Результат
        result_frame = tk.LabelFrame(right_panel, text="Результат", padx=10, pady=10)
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.result_canvas = tk.Canvas(result_frame, bg="gray90", width=550, height=600)
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Переменные для выбора области
        self.selecting = False
        self.start_x = self.start_y = None
        self.rect_id = None
        
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
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                self.selected_region = None
                self.processed_image = None
                
                # Обновляем интерфейс
                self.display_image(self.original_image, self.orig_canvas)
                self.select_btn.config(state=tk.NORMAL)
                self.info_label.config(
                    text=f"Изображение загружено:\n{os.path.basename(file_path)}\n"
                         f"Размер: {self.original_image.size[0]}x{self.original_image.size[1]}"
                )
                messagebox.showinfo("Успех", "Изображение загружено!\nВыберите область для извлечения.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{e}")
    
    def display_image(self, image, canvas):
        """Отображение изображения на канвасе"""
        canvas.delete("all")
        
        if image is None:
            return
        
        # Масштабирование
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 550
            canvas_height = 600
        
        img_width, img_height = image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        display_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Создаем фото
        if display_image.mode == 'RGBA':
            bg = Image.new('RGB', display_image.size, (255, 255, 255))
            bg.paste(display_image, mask=display_image.split()[3])
            display_image = bg
        
        photo = ImageTk.PhotoImage(display_image)
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor=tk.CENTER)
        canvas.image = photo
    
    def select_region(self):
        """Интерактивный выбор области"""
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return
        
        self.selecting = True
        self.orig_canvas.config(cursor="cross")
        
        def on_click(event):
            if self.selecting:
                self.start_x = event.x
                self.start_y = event.y
                if self.rect_id:
                    self.orig_canvas.delete(self.rect_id)
        
        def on_drag(event):
            if self.selecting and self.start_x is not None:
                if self.rect_id:
                    self.orig_canvas.delete(self.rect_id)
                self.rect_id = self.orig_canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    outline="red", width=3
                )
        
        def on_release(event):
            if self.selecting and self.start_x is not None:
                # Переводим координаты в масштаб оригинала
                canvas_width = self.orig_canvas.winfo_width()
                canvas_height = self.orig_canvas.winfo_height()
                
                if canvas_width <= 1:
                    canvas_width = 550
                if canvas_height <= 1:
                    canvas_height = 600
                
                img_width, img_height = self.original_image.size
                scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
                
                x1 = int(min(self.start_x, event.x) / scale)
                y1 = int(min(self.start_y, event.y) / scale)
                x2 = int(max(self.start_x, event.x) / scale)
                y2 = int(max(self.start_y, event.y) / scale)
                
                # Ограничиваем границами
                x1 = max(0, min(x1, img_width))
                y1 = max(0, min(y1, img_height))
                x2 = max(0, min(x2, img_width))
                y2 = max(0, min(y2, img_height))
                
                if x2 > x1 and y2 > y1:
                    self.selected_region = (x1, y1, x2, y2)
                    self.info_label.config(
                        text=f"Область выбрана:\n"
                             f"X: {x1}-{x2}, Y: {y1}-{y2}\n"
                             f"Размер: {x2-x1}x{y2-y1}"
                    )
                    # Включаем кнопку извлечения
                    for widget in self.root.winfo_children():
                        if isinstance(widget, tk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, tk.Frame):
                                    for btn in child.winfo_children():
                                        if isinstance(btn, tk.Button) and "Извлечь" in btn.cget("text"):
                                            btn.config(state=tk.NORMAL)
                else:
                    messagebox.showwarning("Ошибка", "Выберите область правильно!")
                
                self.selecting = False
                self.orig_canvas.config(cursor="")
        
        self.orig_canvas.bind("<Button-1>", on_click)
        self.orig_canvas.bind("<B1-Motion>", on_drag)
        self.orig_canvas.bind("<ButtonRelease-1>", on_release)
        
        messagebox.showinfo("Выбор области", "Зажмите левую кнопку мыши и выделите область для извлечения")
    
    def extract_print(self):
        """Извлечение принта"""
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return
        
        if self.selected_region is None:
            messagebox.showwarning("Предупреждение", "Сначала выберите область для извлечения!")
            return
        
        try:
            # Ленивая загрузка numpy и cv2
            success, error = lazy_import_numpy()
            if not success:
                messagebox.showerror("Ошибка", f"Не удалось загрузить numpy:\n{error}")
                return
            
            success, error = lazy_import_cv2()
            if not success:
                messagebox.showerror("Ошибка", f"Не удалось загрузить OpenCV:\n{error}\n\nИспользуется простой метод PIL")
                # Используем простой метод без OpenCV
                self.extract_print_simple()
                return
            
            # Обрезаем область
            x1, y1, x2, y2 = self.selected_region
            cropped = self.original_image.crop((x1, y1, x2, y2))
            cropped_array = np.array(cropped.convert('RGBA'))
            
            # Удаляем фон с OpenCV
            gray = cv2.cvtColor(cropped_array[:, :, :3], cv2.COLOR_RGB2GRAY)
            
            # Адаптивное пороговое значение
            adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # Пороги для удаления фона
            _, mask1 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            _, mask2 = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
            
            mask = cv2.bitwise_or(mask1, mask2)
            mask = cv2.bitwise_and(mask, adaptive)
            
            # Улучшаем маску
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.GaussianBlur(mask, (3, 3), 0)
            
            # Применяем маску
            cropped_array[:, :, 3] = mask
            
            self.processed_image = Image.fromarray(cropped_array, 'RGBA')
            self.display_image(self.processed_image, self.result_canvas)
            
            # Включаем кнопки
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Frame):
                            for btn in child.winfo_children():
                                if isinstance(btn, tk.Button):
                                    if "Улучшить" in btn.cget("text") or "Сохранить" in btn.cget("text"):
                                        btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Успех", "Принт извлечен!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении:\n{e}")
    
    def extract_print_simple(self):
        """Простое извлечение без OpenCV"""
        try:
            x1, y1, x2, y2 = self.selected_region
            cropped = self.original_image.crop((x1, y1, x2, y2))
            
            # Простое удаление фона через PIL
            cropped = cropped.convert('RGBA')
            data = cropped.getdata()
            
            new_data = []
            for item in data:
                # Если пиксель очень светлый (фон), делаем прозрачным
                if item[0] > 240 and item[1] > 240 and item[2] > 240:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            
            cropped.putdata(new_data)
            self.processed_image = cropped
            self.display_image(self.processed_image, self.result_canvas)
            
            messagebox.showinfo("Успех", "Принт извлечен (простой метод)!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении:\n{e}")
    
    def enhance_quality(self):
        """Улучшение качества"""
        if not hasattr(self, 'processed_image') or self.processed_image is None:
            messagebox.showwarning("Предупреждение", "Сначала извлеките принт!")
            return
        
        try:
            img = self.processed_image.copy()
            
            # Резкость
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)
            
            # Контраст
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)
            
            # Фильтр
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
            
            self.processed_image = img
            self.display_image(self.processed_image, self.result_canvas)
            
            messagebox.showinfo("Успех", "Качество улучшено!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при улучшении:\n{e}")
    
    def save_png(self):
        """Сохранение результата"""
        if not hasattr(self, 'processed_image') or self.processed_image is None:
            messagebox.showwarning("Предупреждение", "Нет обработанного изображения для сохранения!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить PNG",
            defaultextension=".png",
            filetypes=[("PNG файлы", "*.png"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                self.processed_image.save(file_path, "PNG", optimize=True)
                messagebox.showinfo("Успех", f"Изображение сохранено:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{e}")

def main():
    """Главная функция с полной обработкой ошибок"""
    try:
        # Создаем главное окно
        root = tk.Tk()
        
        # Проверяем, что окно создано
        root.update_idletasks()
        
        # Создаем приложение
        app = PrintExtractorGUI(root)
        
        # Обновляем окно
        root.update_idletasks()
        
        # Запускаем главный цикл
        root.mainloop()
        
    except SystemError as e:
        # Критические системные ошибки (включая возможные краши на macOS)
        error_msg = str(e)
        print(f"❌ Системная ошибка: {error_msg}")
        
        # Пробуем показать диалог через osascript
        import subprocess
        subprocess.run([
            'osascript', '-e',
            f'display dialog "Ошибка при запуске программы:\n\n{error_msg}\n\nВозможна проблема совместимости с macOS.\n\nИспользуйте консольную версию: python3 ИЗВЛЕЧЕНИЕ_ПРИНТА.py" buttons {{"OK"}} default button "OK" with icon stop'
        ], stderr=subprocess.DEVNULL)
        
        sys.exit(1)
        
    except KeyboardInterrupt:
        # Пользователь прервал программу
        sys.exit(0)
        
    except Exception as e:
        # Все остальные ошибки
        error_msg = str(e)
        print(f"❌ Ошибка: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Пробуем показать диалог
        try:
            import subprocess
            subprocess.run([
                'osascript', '-e',
                f'display dialog "Ошибка при запуске:\n\n{error_msg}\n\nПроверьте, что все зависимости установлены." buttons {{"OK"}} default button "OK" with icon caution'
            ], stderr=subprocess.DEVNULL, timeout=5)
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
