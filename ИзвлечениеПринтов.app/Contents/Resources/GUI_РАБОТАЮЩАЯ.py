#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
МИНИМАЛЬНАЯ GUI версия - только базовые модули
Работает без проблемных зависимостей
"""

import sys
import os

# Шаг 1: Проверяем tkinter (БЕЗ print - может вызывать проблемы)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception as e:
    print(f"❌ Ошибка tkinter: {e}")
    sys.exit(1)

# Шаг 2: Проверяем PIL (только базовый импорт)
try:
    from PIL import Image
except Exception as e:
    try:
        import tkinter.messagebox as mb
        mb.showerror("Ошибка", f"Pillow не установлен:\n{e}\n\nУстановите:\npip3 install Pillow")
    except:
        print(f"❌ Ошибка PIL: {e}")
    sys.exit(1)

# Шаг 3: Загружаем остальные модули PIL только при необходимости
def load_pil_modules():
    """Ленивая загрузка модулей PIL"""
    global ImageTk, ImageEnhance, ImageFilter
    try:
        from PIL import ImageTk, ImageEnhance, ImageFilter
        return True, None
    except Exception as e:
        return False, str(e)

class SimplePrintExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение принтов")
        self.root.geometry("1000x700")
        
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.selected_region = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        tk.Label(
            self.root,
            text="🎨 Извлечение принтов и надписей",
            font=("Arial", 16, "bold"),
            pady=10
        ).pack()
        
        # Кнопки
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack()
        
        tk.Button(
            button_frame,
            text="📁 Загрузить изображение",
            command=self.load_image,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            width=25
        ).pack(pady=5)
        
        self.select_btn = tk.Button(
            button_frame,
            text="✂️ Выбрать область",
            command=self.select_region,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            padx=20,
            pady=10,
            width=25,
            state=tk.DISABLED
        )
        self.select_btn.pack(pady=5)
        
        self.extract_btn = tk.Button(
            button_frame,
            text="🔍 Извлечь принт",
            command=self.extract_print,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            width=25,
            state=tk.DISABLED
        )
        self.extract_btn.pack(pady=5)
        
        self.save_btn = tk.Button(
            button_frame,
            text="💾 Сохранить PNG",
            command=self.save_png,
            font=("Arial", 12),
            bg="#F44336",
            fg="white",
            padx=20,
            pady=10,
            width=25,
            state=tk.DISABLED
        )
        self.save_btn.pack(pady=5)
        
        # Изображения
        image_frame = tk.Frame(self.root)
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Оригинал
        orig_label = tk.LabelFrame(image_frame, text="Оригинал")
        orig_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.orig_canvas = tk.Canvas(orig_label, bg="gray90", width=450, height=500)
        self.orig_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Результат
        result_label = tk.LabelFrame(image_frame, text="Результат")
        result_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.result_canvas = tk.Canvas(result_label, bg="gray90", width=450, height=500)
        self.result_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.selecting = False
        self.start_x = self.start_y = None
        self.rect_id = None
        
    def load_image(self):
        """Загрузка изображения"""
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                self.image_path = file_path
                self.original_image = Image.open(file_path)
                self.selected_region = None
                self.processed_image = None
                
                self.display_image(self.original_image, self.orig_canvas)
                self.select_btn.config(state=tk.NORMAL)
                messagebox.showinfo("Успех", "Изображение загружено!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить:\n{e}")
    
    def display_image(self, image, canvas):
        """Отображение изображения"""
        canvas.delete("all")
        if image is None:
            return
        
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1:
            w = 450
        if h <= 1:
            h = 500
        
        img_w, img_h = image.size
        scale = min(w / img_w, h / img_h, 1.0)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        display_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        if display_img.mode == 'RGBA':
            bg = Image.new('RGB', display_img.size, (255, 255, 255))
            bg.paste(display_img, mask=display_img.split()[3])
            display_img = bg
        
        # Загружаем ImageTk только сейчас
        success, error = load_pil_modules()
        if success:
            photo = ImageTk.PhotoImage(display_img)
        else:
            # Если ImageTk не работает, используем простой способ
            messagebox.showwarning("Предупреждение", f"ImageTk недоступен: {error}\nИзображение может не отображаться")
            return
        
        canvas.create_image(w // 2, h // 2, image=photo, anchor=tk.CENTER)
        canvas.image = photo
    
    def select_region(self):
        """Выбор области"""
        if self.original_image is None:
            return
        
        self.selecting = True
        self.orig_canvas.config(cursor="cross")
        
        def on_click(event):
            self.start_x = event.x
            self.start_y = event.y
            if self.rect_id:
                self.orig_canvas.delete(self.rect_id)
        
        def on_drag(event):
            if self.start_x is not None:
                if self.rect_id:
                    self.orig_canvas.delete(self.rect_id)
                self.rect_id = self.orig_canvas.create_rectangle(
                    self.start_x, self.start_y, event.x, event.y,
                    outline="red", width=3
                )
        
        def on_release(event):
            if self.start_x is not None:
                canvas_w = self.orig_canvas.winfo_width()
                canvas_h = self.orig_canvas.winfo_height()
                if canvas_w <= 1:
                    canvas_w = 450
                if canvas_h <= 1:
                    canvas_h = 500
                
                img_w, img_h = self.original_image.size
                scale = min(canvas_w / img_w, canvas_h / img_h, 1.0)
                
                x1 = int(min(self.start_x, event.x) / scale)
                y1 = int(min(self.start_y, event.y) / scale)
                x2 = int(max(self.start_x, event.x) / scale)
                y2 = int(max(self.start_y, event.y) / scale)
                
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))
                
                if x2 > x1 and y2 > y1:
                    self.selected_region = (x1, y1, x2, y2)
                    self.extract_btn.config(state=tk.NORMAL)
                    messagebox.showinfo("Готово", "Область выбрана!")
                
                self.selecting = False
                self.orig_canvas.config(cursor="")
        
        self.orig_canvas.bind("<Button-1>", on_click)
        self.orig_canvas.bind("<B1-Motion>", on_drag)
        self.orig_canvas.bind("<ButtonRelease-1>", on_release)
        
        messagebox.showinfo("Выбор", "Зажмите ЛКМ и выделите область")
    
    def extract_print(self):
        """Извлечение принта"""
        if self.selected_region is None:
            return
        
        try:
            x1, y1, x2, y2 = self.selected_region
            cropped = self.original_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
            # Удаляем фон
            data = cropped.getdata()
            new_data = []
            for item in data:
                r, g, b, a = item
                if r > 230 and g > 230 and b > 230:
                    new_data.append((255, 255, 255, 0))
                elif r < 30 and g < 30 and b < 30:
                    new_data.append((0, 0, 0, 0))
                else:
                    new_data.append(item)
            
            cropped.putdata(new_data)
            self.processed_image = cropped
            self.display_image(self.processed_image, self.result_canvas)
            self.save_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Успех", "Принт извлечен!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка:\n{e}")
    
    def save_png(self):
        """Сохранение"""
        if self.processed_image is None:
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить PNG",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")]
        )
        
        if file_path:
            try:
                self.processed_image.save(file_path, "PNG")
                messagebox.showinfo("Успех", f"Сохранено:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка сохранения:\n{e}")

def main():
    """Главная функция с максимальной защитой"""
    try:
        # Создаем окно с минимальными настройками
        root = tk.Tk()
        
        # Устанавливаем минимальные свойства окна
        root.title("Извлечение принтов")
        root.geometry("1000x700")
        
        # Обновляем окно чтобы убедиться что оно создано
        root.update_idletasks()
        
        # Создаем приложение
        app = SimplePrintExtractor(root)
        
        # Еще раз обновляем
        root.update_idletasks()
        
        # Запускаем главный цикл
        root.mainloop()
        
    except SystemError as e:
        # Системные ошибки (включая возможные краши)
        error_msg = str(e)
        print(f"❌ Системная ошибка: {error_msg}")
        try:
            messagebox.showerror("Системная ошибка", 
                f"Ошибка при запуске:\n{error_msg}\n\n"
                "Возможна проблема совместимости с macOS.\n"
                "Используйте консольную версию:\n"
                "python3 ИЗВЛЕЧЕНИЕ_ПРИНТА.py")
        except:
            pass
        sys.exit(134)
        
    except KeyboardInterrupt:
        sys.exit(0)
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка: {error_msg}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Ошибка", f"Ошибка:\n{error_msg}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
