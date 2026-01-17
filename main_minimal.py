#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Минимальная версия программы без ранних импортов
"""

def main():
    """Главная функция с отложенной загрузкой всех модулей"""
    try:
        print("Импорт tkinter...")
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
        print("✓ tkinter загружен")
        
        print("Импорт PIL...")
        from PIL import Image, ImageTk, ImageEnhance, ImageFilter
        print("✓ PIL загружен")
        
        print("Создание главного окна...")
        root = tk.Tk()
        root.title("Извлечение принтов для печати")
        root.geometry("1000x700")
        print("✓ Главное окно создано")
        
        # Создаем простой интерфейс
        tk.Label(root, text="Извлечение и обработка принтов", 
                font=("Arial", 16, "bold"), pady=10).pack()
        
        # Функция для загрузки изображения (упрощенная версия)
        def load_image():
            file_path = filedialog.askopenfilename(
                title="Выберите изображение",
                filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                messagebox.showinfo("Успех", f"Изображение загружено: {file_path}")
        
        tk.Button(root, text="Загрузить изображение", 
                 command=load_image, font=("Arial", 12),
                 bg="#4CAF50", fg="white", padx=20, pady=5).pack(pady=10)
        
        tk.Label(root, text="Это минимальная версия программы.\n"
                          "Если это окно появилось, значит базовый GUI работает!",
                font=("Arial", 10)).pack(pady=20)
        
        print("✓ Интерфейс создан")
        print("Запуск главного цикла...")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
