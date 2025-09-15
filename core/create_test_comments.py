#!/usr/bin/env python
"""
Скрипт для создания тестовых комментариев тренера
"""

import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import TrainerComment, Child, Trainer

def create_test_comments():
    """Создает тестовые комментарии тренеров"""
    
    print("Создаем тестовые комментарии...")
    
    # Получаем тестового ребенка и тренера
    child = Child.objects.first()
    if not child:
        print("Ребенок не найден")
        return
        
    trainer = Trainer.objects.first()
    if not trainer:
        print("Тренер не найден")
        return
    
    print(f"Создаем комментарии для ребенка: {child.full_name}")
    print(f"От тренера: {trainer.full_name}")
    
    # Создаем несколько тестовых комментариев
    comments_text = [
        "Ребенок хорошо занимается, показывает отличный прогресс в координации движений. Рекомендую продолжать в том же духе!",
        "Сегодня работали над техникой ударов. Нужно больше внимания уделить постановке ноги.",
        "Отличная работа на тренировке! Ребенок очень старается и слушает инструкции.",
        "Рекомендую дома поработать над растяжкой. Это поможет избежать травм.",
        "Заметил улучшения в скорости реакции. Продолжаем работать над выносливостью."
    ]
    
    created_count = 0
    for i, comment_text in enumerate(comments_text):
        # Проверяем, нет ли уже такого комментария
        existing = TrainerComment.objects.filter(
            trainer=trainer,
            child=child,
            comment_text=comment_text
        ).exists()
        
        if not existing:
            comment = TrainerComment.objects.create(
                trainer=trainer,
                child=child,
                comment_text=comment_text
            )
            created_count += 1
            print(f"Создан комментарий {i+1}: {comment_text[:50]}...")
    
    print(f"\nВсего создано комментариев: {created_count}")

if __name__ == "__main__":
    create_test_comments()
