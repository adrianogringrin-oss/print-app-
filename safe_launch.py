#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безопасный запуск программы с полной обработкой ошибок
"""

import sys
import traceback

def safe_launch():
    """Безопасный запуск программы с перехватом всех ошибок"""
    print("=" * 60)
    print("Безопасный запуск программы извлечения принтов")
    print("=" * 60)
    print()
    
    try:
        print("Шаг 1: Импорт tkinter...")
        import tkinter as tk
        print("✓ tkinter загружен")
        
        print("Шаг 2: Импорт PIL...")
        from PIL import Image, ImageTk
        print("✓ PIL загружен")
        
        print("Шаг 3: Импорт main.py...")
        import main
        print("✓ main.py импортирован")
        
        print("Шаг 4: Создание главного окна...")
        root = tk.Tk()
        print("✓ Главное окно создано")
        
        print("Шаг 5: Создание приложения...")
        app = main.PrintExtractor(root)
        print("✓ Приложение создано")
        
        print()
        print("=" * 60)
        print("Программа запущена успешно!")
        print("=" * 60)
        print()
        
        # Запускаем главный цикл
        root.mainloop()
        
    except SystemError as e:
        print()
        print("=" * 60)
        print("❌ СИСТЕМНАЯ ОШИБКА")
        print("=" * 60)
        print(f"Ошибка: {e}")
        print()
        print("Возможна проблема совместимости с macOS")
        print("Или проблема с нативными библиотеками")
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ОШИБКА")
        print("=" * 60)
        print(f"Ошибка: {e}")
        print()
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    safe_launch()
