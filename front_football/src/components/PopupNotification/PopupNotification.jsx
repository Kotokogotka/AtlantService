import React, { useState, useEffect } from 'react';
import { scheduleAPI } from '../../utils/api';
import styles from './PopupNotification.module.css';

const PopupNotification = ({ notifications, onMarkAsRead, onClose }) => {
  const [currentNotificationIndex, setCurrentNotificationIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  // Фильтруем только непрочитанные уведомления
  const unreadNotifications = notifications.filter(n => !n.is_read);

  useEffect(() => {
    if (unreadNotifications.length > 0) {
      setIsVisible(true);
      setCurrentNotificationIndex(0);
    } else {
      setIsVisible(false);
    }
  }, [unreadNotifications.length]);

  // Автоматическое переключение между уведомлениями каждые 5 секунд
  useEffect(() => {
    if (unreadNotifications.length > 1) {
      const interval = setInterval(() => {
        setCurrentNotificationIndex((prevIndex) => 
          (prevIndex + 1) % unreadNotifications.length
        );
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [unreadNotifications.length]);

  const handleMarkAsRead = async () => {
    if (unreadNotifications.length === 0) return;

    const currentNotification = unreadNotifications[currentNotificationIndex];
    try {
      await scheduleAPI.markNotificationAsRead(currentNotification.id);
      onMarkAsRead(currentNotification.id);
    } catch (error) {
      console.error('Ошибка при отметке уведомления как прочитанного:', error);
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    onClose();
  };

  if (!isVisible || unreadNotifications.length === 0) {
    return null;
  }

  const currentNotification = unreadNotifications[currentNotificationIndex];

  return (
    <div className={styles.overlay}>
      <div className={styles.popup}>
        <div className={styles.header}>
          <div className={styles.icon}>
            {currentNotification.type_code === 'date_changed' ? '📅' :
             currentNotification.type_code === 'time_changed' ? '🕐' :
             currentNotification.type_code === 'both_changed' ? '📅🕐' : '❌'}
          </div>
          <h3 className={styles.title}>Изменение в расписании</h3>
          <button className={styles.closeButton} onClick={handleClose}>
            ✕
          </button>
        </div>

        <div className={styles.content}>
          <div className={styles.trainingInfo}>
            <strong>{currentNotification.training.group_name}</strong>
          </div>
          <div className={styles.message}>
            {currentNotification.message}
          </div>
          <div className={styles.timestamp}>
            {currentNotification.created_at}
          </div>
        </div>

        <div className={styles.actions}>
          {unreadNotifications.length > 1 && (
            <div className={styles.indicator}>
              {currentNotificationIndex + 1} из {unreadNotifications.length}
            </div>
          )}
          <button 
            className={styles.readButton} 
            onClick={handleMarkAsRead}
          >
            ✓ Прочитано
          </button>
        </div>
      </div>
    </div>
  );
};

export default PopupNotification;
