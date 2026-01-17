#!/usr/bin/env python3
"""Тестовый скрипт для проверки импортов"""

print("Проверка базовых модулей...")
try:
    import tkinter as tk
    print("✓ tkinter OK")
except Exception as e:
    print(f"✗ tkinter ERROR: {e}")
    exit(1)

try:
    from PIL import Image
    print("✓ PIL OK")
except Exception as e:
    print(f"✗ PIL ERROR: {e}")
    exit(1)

print("\nПроверка numpy...")
try:
    import numpy as np
    print("✓ numpy OK")
except Exception as e:
    print(f"✗ numpy ERROR: {e}")
    exit(1)

print("\nПроверка cv2...")
try:
    import cv2
    print("✓ cv2 OK")
    print(f"  OpenCV version: {cv2.__version__}")
except Exception as e:
    print(f"✗ cv2 ERROR: {e}")
    exit(1)

print("\nПроверка импорта main.py...")
try:
    import main
    print("✓ main.py импортирован успешно!")
except SystemError as e:
    print(f"✗ SystemError при импорте main.py: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Ошибка при импорте main.py: {e}")
    exit(1)

print("\n✓ Все проверки пройдены!")
