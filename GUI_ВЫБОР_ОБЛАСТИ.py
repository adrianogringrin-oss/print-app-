#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI версия ТОЛЬКО для выбора области мышью
Минимальный код - должен работать стабильно
"""

import sys
import os

# Очищаем окружение
os.environ.pop('PYTHONPATH', None)

# Импорты
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    print("❌ tkinter недоступен")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("❌ Pillow не установлен")
    sys.exit(1)

class RegionSelector:
    """Простой селектор области"""
    
    def __init__(self, image_path):
        self.image_path = image_path
        self.selected_region = None
        self.start_x = self.start_y = None
        self.rect = None
        
        # Создаем окно
        self.root = tk.Tk()
        self.root.title("Выберите область для извлечения")
        
        # Загружаем изображение
        try:
            self.original_image = Image.open(image_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{e}")
            sys.exit(1)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Инструкция
        instruction = tk.Label(
            self.root,
            text="Зажмите ЛКМ и выделите область для извлечения, затем нажмите 'Готово'",
            font=("Arial", 12),
            pady=10
        )
        instruction.pack()
        
        # Canvas для изображения
        self.canvas = tk.Canvas(self.root, bg="gray90", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="✓ Готово",
            command=self.done,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="✗ Отмена",
            command=self.cancel,
            bg="#F44336",
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=10,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Отображаем изображение
        self.display_image()
        
        # Биндим события мыши
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
    def display_image(self):
        """Отображение изображения на канвасе"""
        # Получаем размеры canvas
        self.root.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        # Масштабируем изображение
        img_width, img_height = self.original_image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        display_img = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Конвертируем для tkinter
        if display_img.mode == 'RGBA':
            bg = Image.new('RGB', display_img.size, (255, 255, 255))
            bg.paste(display_img, mask=display_img.split()[3])
            display_img = bg
        
        self.photo = ImageTk.PhotoImage(display_img)
        self.canvas.create_image(canvas_width // 2, canvas_height // 2, image=self.photo, anchor=tk.CENTER)
        
        # Сохраняем масштаб
        self.scale = scale
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
    def on_click(self, event):
        """Начало выделения"""
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
    
    def on_drag(self, event):
        """Перетаскивание мыши"""
        if self.start_x is not None:
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline="red", width=3
            )
    
    def on_release(self, event):
        """Окончание выделения"""
        if self.start_x is not None:
            # Переводим координаты в оригинальный размер
            x1 = int(min(self.start_x, event.x) / self.scale)
            y1 = int(min(self.start_y, event.y) / self.scale)
            x2 = int(max(self.start_x, event.x) / self.scale)
            y2 = int(max(self.start_y, event.y) / self.scale)
            
            # Ограничиваем границами
            img_width, img_height = self.original_image.size
            x1 = max(0, min(x1, img_width))
            y1 = max(0, min(y1, img_height))
            x2 = max(0, min(x2, img_width))
            y2 = max(0, min(y2, img_height))
            
            if x2 > x1 and y2 > y1:
                self.selected_region = (x1, y1, x2, y2)
    
    def done(self):
        """Завершение выбора"""
        if self.selected_region is None:
            messagebox.showwarning("Предупреждение", "Сначала выделите область!")
            return
        self.root.quit()
    
    def cancel(self):
        """Отмена"""
        self.selected_region = None
        self.root.quit()
    
    def get_region(self):
        """Получить выбранную область"""
        self.root.mainloop()
        self.root.destroy()
        return self.selected_region

def extract_print(image_path, region):
    """Извлечение принта"""
    try:
        image = Image.open(image_path)
        x1, y1, x2, y2 = region
        
        # Обрезаем
        cropped = image.crop((x1, y1, x2, y2))
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
        return cropped
    except Exception as e:
        print(f"Ошибка при извлечении: {e}")
        return None

def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("  🎨 ИЗВЛЕЧЕНИЕ ПРИНТОВ И НАДПИСЕЙ")
    print("="*60 + "\n")
    
    # Выбираем файл
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    
    image_path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[
            ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
            ("Все файлы", "*.*")
        ]
    )
    
    if not image_path:
        print("Файл не выбран")
        return
    
    print(f"✓ Изображение: {os.path.basename(image_path)}")
    
    # Выбираем область
    print("Открывается окно для выбора области...")
    print("Зажмите ЛКМ и выделите область, затем нажмите 'Готово'\n")
    
    selector = RegionSelector(image_path)
    region = selector.get_region()
    
    if region is None:
        print("Выбор отменен")
        return
    
    x1, y1, x2, y2 = region
    print(f"✓ Область выбрана: X={x1}-{x2}, Y={y1}-{y2}")
    print(f"  Размер: {x2-x1} x {y2-y1} пикселей\n")
    
    # Извлекаем
    print("Извлечение принта...")
    result = extract_print(image_path, region)
    
    if result is None:
        print("❌ Ошибка при извлечении")
        return
    
    print("✓ Принт извлечен\n")
    
    # Сохраняем
    root = tk.Tk()
    root.withdraw()
    
    default_name = os.path.splitext(os.path.basename(image_path))[0] + "_extracted.png"
    default_dir = os.path.dirname(image_path) or os.path.expanduser("~/Desktop")
    default_path = os.path.join(default_dir, default_name)
    
    output_path = filedialog.asksaveasfilename(
        title="Сохранить PNG",
        defaultextension=".png",
        initialfile=default_name,
        initialdir=default_dir,
        filetypes=[("PNG файлы", "*.png"), ("Все файлы", "*.*")]
    )
    
    if output_path:
        try:
            result.save(output_path, "PNG", optimize=True)
            print(f"✅ ИЗОБРАЖЕНИЕ СОХРАНЕНО!")
            print(f"   {output_path}\n")
            
            # Открываем файл
            os.system(f'open "{output_path}"')
            
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
    else:
        print("Сохранение отменено")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
