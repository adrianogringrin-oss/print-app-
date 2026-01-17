#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для безопасной установки OpenAI API ключа
"""

import os
import sys

def install_key(api_key=None):
    """Установка API ключа"""
    key_file = os.path.expanduser('~/.openai_api_key')
    
    if api_key is None:
        print("\n🔐 Установка OpenAI API ключа")
        print("="*60)
        print("\nВведите ваш OpenAI API ключ:")
        print("(Ключ можно получить на: https://platform.openai.com/api-keys)")
        print("(Ключ начинается с 'sk-' и не будет показан на экране)")
        print()
        
        # Скрытый ввод
        import getpass
        api_key = getpass.getpass("API ключ: ").strip()
    
    if not api_key:
        print("❌ Ключ не введен")
        return False
    
    # Проверка формата
    if not api_key.startswith('sk-'):
        print(f"⚠ Предупреждение: ключ обычно начинается с 'sk-', ваш начинается с '{api_key[:3]}'")
        response = input("Продолжить? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # Сохраняем ключ
    try:
        with open(key_file, 'w') as f:
            f.write(api_key)
        
        # Устанавливаем права доступа (только для владельца)
        os.chmod(key_file, 0o600)
        
        print(f"\n✅ Ключ успешно сохранен в: {key_file}")
        print(f"   Начало ключа: {api_key[:10]}...")
        print(f"   Права доступа: 600 (только для вас)")
        
        # Проверяем что ключ сохранился
        with open(key_file, 'r') as f:
            saved_key = f.read().strip()
            if saved_key == api_key:
                print("   ✓ Проверка: ключ сохранен правильно")
                return True
            else:
                print("   ❌ Ошибка: ключ не совпадает!")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка при сохранении ключа: {e}")
        return False

def verify_setup():
    """Проверка настройки"""
    print("\n" + "="*60)
    print("Проверка настройки...")
    print("="*60)
    
    # Проверка Pillow
    try:
        from PIL import Image
        print("✅ Pillow установлен")
    except ImportError:
        print("❌ Pillow не установлен")
        print("   Установите: pip3 install --user --break-system-packages Pillow")
    
    # Проверка OpenAI
    try:
        import openai
        print(f"✅ OpenAI установлен (версия: {openai.__version__})")
    except ImportError:
        print("❌ OpenAI не установлен")
        print("   Установите: pip3 install --user --break-system-packages openai")
    
    # Проверка ключа
    key_file = os.path.expanduser('~/.openai_api_key')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                key = f.read().strip()
                if key:
                    print(f"✅ API ключ найден: {key[:10]}...")
                    
                    # Проверка формата
                    if key.startswith('sk-'):
                        print("   ✓ Формат ключа правильный")
                    else:
                        print("   ⚠ Необычный формат ключа")
                    
                    return True
                else:
                    print("⚠ API ключ пустой")
        except Exception as e:
            print(f"⚠ Ошибка чтения ключа: {e}")
    else:
        print("⚠ API ключ не найден")
        print(f"   Создайте файл: {key_file}")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ключ передан как аргумент
        api_key = sys.argv[1]
        success = install_key(api_key)
    else:
        # Интерактивный режим
        success = install_key()
    
    if success:
        verify_setup()
        print("\n" + "="*60)
        print("✅ НАСТРОЙКА ЗАВЕРШЕНА!")
        print("="*60)
        print("\nТеперь можно запускать:")
        print("  ./ЗАПУСТИТЬ_С_ИИ.command")
        print("\nИли напрямую:")
        print("  python3 ВЕБ_ВЕРСИЯ_С_ИИ.py")
        print()
    else:
        print("\n❌ Настройка не завершена. Исправьте ошибки и попробуйте снова.")
        sys.exit(1)
