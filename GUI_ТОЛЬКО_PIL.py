#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI приложение для извлечения принтов - РАБОЧАЯ ВЕРСИЯ
Использует только PIL - работает на всех системах без проблемных зависимостей
"""

import sys
import os

# Безопасная загрузка tkinter
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("❌ tkinter недоступен")
    sys.exit(1)

# Безопасная загрузка PIL
try:
    from PIL import Image, ImageTk, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("❌ Pillow не установлен. Установите: pip install Pillow")
    sys.exit(1)

print("✓ Модули загружены успешно")

class PrintExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение принтов и надписей")
        self.root.geometry("1200x800")
        
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.selected_region = None
        
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
        
        self.extract_btn = tk.Button(
            left_panel,
            text="🔍 Извлечь принт",
            command=self.extract_print,
            bg="#2196F3",
            fg="white",
            state=tk.DISABLED,
            **button_style
        )
        self.extract_btn.pack(pady=10, fill=tk.X)
        
        self.enhance_btn = tk.Button(
            left_panel,
            text="✨ Улучшить качество",
            command=self.enhance_quality,
            bg="#9C27B0",
            fg="white",
            state=tk.DISABLED,
            **button_style
        )
        self.enhance_btn.pack(pady=10, fill=tk.X)
        
        self.save_btn = tk.Button(
            left_panel,
            text="💾 Сохранить PNG",
            command=self.save_png,
            bg="#F44336",
            fg="white",
            state=tk.DISABLED,
            **button_style
        )
        self.save_btn.pack(pady=10, fill=tk.X)
        
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
                self.extract_btn.config(state=tk.DISABLED)
                self.enhance_btn.config(state=tk.DISABLED)
                self.save_btn.config(state=tk.DISABLED)
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
                    self.extract_btn.config(state=tk.NORMAL)
                    messagebox.showinfo("Область выбрана", "Область выбрана!\nНажмите 'Извлечь принт'")
                else:
                    messagebox.showwarning("Ошибка", "Выберите область правильно!")
                
                self.selecting = False
                self.orig_canvas.config(cursor="")
        
        self.orig_canvas.bind("<Button-1>", on_click)
        self.orig_canvas.bind("<B1-Motion>", on_drag)
        self.orig_canvas.bind("<ButtonRelease-1>", on_release)
        
        messagebox.showinfo("Выбор области", "Зажмите левую кнопку мыши и выделите область для извлечения")
    
    def extract_print(self):
        """Извлечение принта (только PIL, без numpy/cv2)"""
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return
        
        if self.selected_region is None:
            messagebox.showwarning("Предупреждение", "Сначала выберите область для извлечения!")
            return
        
        try:
            # Обрезаем область
            x1, y1, x2, y2 = self.selected_region
            cropped = self.original_image.crop((x1, y1, x2, y2))
            
            # Конвертируем в RGBA
            cropped = cropped.convert('RGBA')
            
            # Удаляем фон используя только PIL
            # Простой метод: удаляем светлые пиксели (фон)
            data = cropped.getdata()
            
            new_data = []
            for item in data:
                r, g, b, a = item
                
                # Если пиксель очень светлый (белый/светлый фон), делаем прозрачным
                if r > 230 and g > 230 and b > 230:
                    new_data.append((255, 255, 255, 0))  # Прозрачный
                # Если пиксель очень темный (тень/темный фон), тоже прозрачный
                elif r < 30 and g < 30 and b < 30:
                    new_data.append((0, 0, 0, 0))  # Прозрачный
                else:
                    # Это принт - оставляем
                    new_data.append(item)
            
            cropped.putdata(new_data)
            
            self.processed_image = cropped
            self.display_image(self.processed_image, self.result_canvas)
            
            # Включаем кнопки
            self.enhance_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Успех", "Принт извлечен!\nТеперь можно улучшить качество и сохранить.")
            
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
            
            # Фильтр резкости
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
    """Главная функция"""
    try:
        root = tk.Tk()
        app = PrintExtractorGUI(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_msg = f"Критическая ошибка: {e}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        # Показываем ошибку в диалоге
        try:
            messagebox.showerror("Критическая ошибка", error_msg)
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
