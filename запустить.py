#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запуска программы извлечения принтов
Проверяет зависимости и запускает основную программу
"""

import sys
import subprocess
import importlib.util

def check_package(package_name, import_name=None):
    """Проверка наличия пакета"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def install_package(package_name):
    """Установка пакета"""
    try:
        print(f"Установка {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Ошибка при установке {package_name}")
        return False

def main():
    print("=" * 50)
    print("Программа для извлечения принтов с одежды")
    print("=" * 50)
    print()
    
    # Проверка обязательных зависимостей
    required_packages = {
        "Pillow": "PIL",
        "numpy": "numpy",
        "opencv-python": "cv2"
    }
    
    # Опциональные зависимости
    optional_packages = {
        "rembg": "rembg"
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        if not check_package(package_name, import_name):
            missing_packages.append(package_name)
            print(f"⚠️  {package_name} не установлен (обязательно)")
        else:
            print(f"✓ {package_name} установлен")
    
    # Проверка опциональных пакетов
    # ВАЖНО: НЕ пытаемся импортировать rembg здесь, так как это может вызвать системный краш на macOS
    # rembg будет проверяться только при реальном использовании в основной программе
    print()
    for package_name, import_name in optional_packages.items():
        if check_package(package_name, import_name):
            # Только проверяем наличие модуля, НЕ импортируем (избегаем системного краша)
            print(f"○ {package_name} установлен (будет проверен при использовании)")
        else:
            print(f"○ {package_name} не установлен (опционально)")
    
    if missing_packages:
        print()
        response = input(f"Установить недостающие обязательные пакеты? ({', '.join(missing_packages)}) [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes', 'да', 'д']:
            print()
            for package in missing_packages:
                if not install_package(package):
                    print(f"\n❌ Не удалось установить {package}")
                    print("Попробуйте установить вручную: pip install -r requirements.txt")
                    input("Нажмите Enter для выхода...")
                    return False
            print("\n✓ Все обязательные пакеты успешно установлены!")
        else:
            print("\n❌ Программа не может работать без обязательных зависимостей")
            input("Нажмите Enter для выхода...")
            return False
    
    print()
    print("=" * 50)
    print("Запуск программы...")
    print("=" * 50)
    print()
    
    # Запуск основной программы
    try:
        import main
        main.main()
    except KeyboardInterrupt:
        print("\n\nПрограмма завершена пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске программы: {e}")
        input("Нажмите Enter для выхода...")
        return False
    
    return True

if __name__ == "__main__":
    main()
