#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI версия БЕЗ отображения изображений - только функционал
Избегаем проблемы с ImageTk которая может вызывать краш
"""

import sys
import os

# Очищаем PYTHONPATH
os.environ.pop('PYTHONPATH', None)

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from tkinter import ttk
except ImportError as e:
    print(f"❌ tkinter недоступен: {e}")
    sys.exit(1)

try:
    from PIL import Image
except ImportError as e:
    print(f"❌ Pillow недоступен: {e}")
    try:
        messagebox.showerror("Ошибка", f"Pillow не установлен:\n{e}")
    except:
        pass
    sys.exit(1)

class PrintExtractorNoDisplay:
    """GUI без отображения изображений - только функции"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Извлечение принтов и надписей")
        self.root.geometry("600x500")
        
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.selected_region = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg="#2196F3", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🎨 Извлечение принтов и надписей",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2196F3"
        ).pack(pady=12)
        
        # Основной контент
        main_frame = tk.Frame(self.root, padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Информация о файле
        self.file_label = tk.Label(
            main_frame,
            text="Файл не загружен",
            font=("Arial", 12),
            fg="gray",
            anchor="w"
        )
        self.file_label.pack(fill=tk.X, pady=10)
        
        # Кнопки
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        btn_style = {
            "font": ("Arial", 11),
            "padx": 20,
            "pady": 12,
            "width": 30
        }
        
        tk.Button(
            button_frame,
            text="📁 Загрузить изображение",
            command=self.load_image,
            bg="#4CAF50",
            fg="white",
            **btn_style
        ).pack(pady=8)
        
        tk.Button(
            button_frame,
            text="✂️ Ввести координаты области (вручную)",
            command=self.enter_coordinates,
            bg="#FF9800",
            fg="white",
            state=tk.DISABLED,
            **btn_style
        ).pack(pady=8)
        self.coords_btn = button_frame.winfo_children()[-1]
        
        tk.Button(
            button_frame,
            text="🔍 Извлечь принт",
            command=self.extract_print,
            bg="#2196F3",
            fg="white",
            state=tk.DISABLED,
            **btn_style
        ).pack(pady=8)
        self.extract_btn = button_frame.winfo_children()[-1]
        
        tk.Button(
            button_frame,
            text="💾 Сохранить PNG",
            command=self.save_png,
            bg="#F44336",
            fg="white",
            state=tk.DISABLED,
            **btn_style
        ).pack(pady=8)
        self.save_btn = button_frame.winfo_children()[-1]
        
        # Информация
        info_frame = tk.LabelFrame(main_frame, text="Информация", padx=15, pady=15)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.info_text = tk.Text(
            info_frame,
            height=8,
            font=("Arial", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(info_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)
        
        self.update_info("Загрузите изображение для начала работы")
    
    def update_info(self, text):
        """Обновление информации"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, text)
        self.info_text.config(state=tk.DISABLED)
    
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
                
                # Обновляем информацию
                file_name = os.path.basename(file_path)
                width, height = self.original_image.size
                
                self.file_label.config(text=f"📄 {file_name} ({width}x{height})", fg="black")
                self.update_info(
                    f"Изображение загружено:\n"
                    f"Файл: {file_name}\n"
                    f"Размер: {width} x {height} пикселей\n\n"
                    f"Следующий шаг: Введите координаты области для извлечения\n"
                    f"Формат: x1 y1 x2 y2 (например: 100 100 500 300)"
                )
                
                self.coords_btn.config(state=tk.NORMAL)
                self.extract_btn.config(state=tk.DISABLED)
                self.save_btn.config(state=tk.DISABLED)
                
                messagebox.showinfo("Успех", "Изображение загружено!\nВведите координаты области для извлечения.")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение:\n{e}")
    
    def enter_coordinates(self):
        """Ввод координат области"""
        if self.original_image is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите изображение!")
            return
        
        width, height = self.original_image.size
        
        # Диалог ввода координат
        dialog = tk.Toplevel(self.root)
        dialog.title("Введите координаты области")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text=f"Размер изображения: {width} x {height}",
            font=("Arial", 10),
            pady=10
        ).pack()
        
        tk.Label(
            dialog,
            text="Введите координаты области (x1 y1 x2 y2):",
            font=("Arial", 10)
        ).pack(pady=5)
        
        coords_entry = tk.Entry(dialog, font=("Arial", 12), width=30)
        coords_entry.pack(pady=10)
        coords_entry.focus()
        
        hint_label = tk.Label(
            dialog,
            text=f"Пример: 100 100 {width//2} {height//2}",
            font=("Arial", 9),
            fg="gray"
        )
        hint_label.pack()
        
        def ok_clicked():
            try:
                coords = coords_entry.get().strip().split()
                if len(coords) != 4:
                    raise ValueError("Нужно 4 числа")
                
                x1, y1, x2, y2 = map(int, coords)
                
                # Проверяем границы
                x1 = max(0, min(x1, width))
                y1 = max(0, min(y1, height))
                x2 = max(0, min(x2, width))
                y2 = max(0, min(y2, height))
                
                if x2 <= x1 or y2 <= y1:
                    raise ValueError("x2 должно быть > x1, y2 должно быть > y1")
                
                self.selected_region = (x1, y1, x2, y2)
                self.update_info(
                    f"Область выбрана:\n"
                    f"Координаты: X={x1}-{x2}, Y={y1}-{y2}\n"
                    f"Размер области: {x2-x1} x {y2-y1} пикселей\n\n"
                    f"Нажмите 'Извлечь принт' для обработки"
                )
                self.extract_btn.config(state=tk.NORMAL)
                dialog.destroy()
                messagebox.showinfo("Готово", "Координаты введены!\nНажмите 'Извлечь принт'")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные координаты:\n{e}")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="OK", command=ok_clicked, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy, width=15).pack(side=tk.LEFT, padx=5)
    
    def extract_print(self):
        """Извлечение принта"""
        if self.original_image is None or self.selected_region is None:
            messagebox.showwarning("Предупреждение", "Загрузите изображение и выберите область!")
            return
        
        try:
            x1, y1, x2, y2 = self.selected_region
            cropped = self.original_image.crop((x1, y1, x2, y2))
            cropped = cropped.convert('RGBA')
            
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
            self.processed_image = cropped
            
            width, height = cropped.size
            self.update_info(
                f"Принт извлечен!\n"
                f"Размер: {width} x {height} пикселей\n"
                f"Прозрачных пикселей: {transparent_count}\n\n"
                f"Нажмите 'Сохранить PNG' для сохранения результата"
            )
            
            self.save_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Успех", "Принт извлечен!\nТеперь можно сохранить результат.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при извлечении:\n{e}")
    
    def save_png(self):
        """Сохранение результата"""
        if self.processed_image is None:
            messagebox.showwarning("Предупреждение", "Нет обработанного изображения!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить PNG",
            defaultextension=".png",
            filetypes=[("PNG файлы", "*.png"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            try:
                self.processed_image.save(file_path, "PNG", optimize=True)
                self.update_info(
                    f"{self.info_text.get(1.0, tk.END).strip()}\n\n"
                    f"✓ Сохранено: {os.path.basename(file_path)}"
                )
                messagebox.showinfo("Успех", f"Изображение сохранено:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{e}")

def main():
    """Главная функция"""
    try:
        root = tk.Tk()
        app = PrintExtractorNoDisplay(root)
        root.mainloop()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Ошибка", f"Ошибка:\n{e}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
