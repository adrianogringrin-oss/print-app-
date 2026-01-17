#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовая версия GUI - максимально простая
Проверяем, что именно вызывает краш
"""

import sys
import os

# Очищаем PYTHONPATH
os.environ.pop('PYTHONPATH', None)

print("Импорт tkinter...")
try:
    import tkinter as tk
    print("✓ tkinter импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта tkinter: {e}")
    sys.exit(1)

print("Импорт PIL...")
try:
    from PIL import Image
    print("✓ PIL импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта PIL: {e}")
    sys.exit(1)

print("Создание главного окна...")
try:
    root = tk.Tk()
    print("✓ Окно создано")
except Exception as e:
    print(f"❌ Ошибка создания окна: {e}")
    sys.exit(1)

print("Настройка окна...")
try:
    root.title("Тест")
    root.geometry("400x300")
    print("✓ Окно настроено")
except Exception as e:
    print(f"❌ Ошибка настройки: {e}")
    root.destroy()
    sys.exit(1)

print("Создание виджета...")
try:
    label = tk.Label(root, text="Если вы видите это - GUI работает!")
    label.pack(pady=50)
    print("✓ Виджет создан")
except Exception as e:
    print(f"❌ Ошибка создания виджета: {e}")
    root.destroy()
    sys.exit(1)

print("Обновление окна...")
try:
    root.update_idletasks()
    print("✓ Окно обновлено")
except Exception as e:
    print(f"❌ Ошибка обновления: {e}")
    root.destroy()
    sys.exit(1)

print("Запуск главного цикла...")
print("Окно должно открыться. Закройте его для завершения.")

try:
    root.mainloop()
    print("✓ Программа завершена нормально")
except Exception as e:
    print(f"❌ Ошибка в главном цикле: {e}")
    sys.exit(1)
