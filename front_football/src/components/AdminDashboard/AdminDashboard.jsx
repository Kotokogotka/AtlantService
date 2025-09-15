import React, { useState, useEffect, useCallback } from 'react';
import { adminAPI, scheduleAPI } from '../../utils/api';
import styles from './AdminDashboard.module.css';

function AdminDashboard({ userInfo, onLogout }) {
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications' или 'schedule'
  const [kindergartens, setKindergartens] = useState([]);
  const [selectedKindergarten, setSelectedKindergarten] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [groupSchedule, setGroupSchedule] = useState([]);
  const [editingTraining, setEditingTraining] = useState(null);
  const [scheduleMode, setScheduleMode] = useState('bulk'); // 'bulk' или 'single'
  const [scheduleForm, setScheduleForm] = useState({
    date: '',
    time: '',
    duration_minutes: 40,
    location: '',
    notes: ''
  });
  const [bulkScheduleForm, setBulkScheduleForm] = useState({
    start_date: '',
    end_date: '',
    weekdays: [],
    time: '',
    duration_minutes: 40,
    location: '',
    notes: ''
  });

  // Загрузка уведомлений
  const loadNotifications = useCallback(async () => {
    try {
      const response = await adminAPI.getMedicalCertificates();
      const pendingCertificates = response.filter(cert => cert.status_code === 'pending');
      setNotifications(pendingCertificates);
    } catch (error) {
      console.error('Ошибка загрузки уведомлений:', error);
    }
  }, []);

  // Загрузка групп для расписания
  const loadGroups = useCallback(async () => {
    try {
      const response = await adminAPI.getGroupsForSchedule();
      setKindergartens(response.kindergartens || []);
    } catch (error) {
      console.error('Ошибка загрузки групп:', error);
    }
  }, []);

  // Загрузка расписания для выбранной группы
  const loadGroupSchedule = useCallback(async (groupId) => {
    try {
      const response = await scheduleAPI.getSchedule();
      const groupTrainings = response.filter(training => training.group.id === groupId);
      setGroupSchedule(groupTrainings);
    } catch (error) {
      console.error('Ошибка загрузки расписания группы:', error);
    }
  }, []);

  // Загрузка уведомлений при монтировании компонента
  useEffect(() => {
    loadNotifications();
    loadGroups();
  }, [loadNotifications, loadGroups]);

  // Обработка клика на уведомление
  const handleNotificationClick = (notification) => {
    setSelectedNotification(notification);
    setShowModal(true);
  };

  // Подтверждение справки
  const handleApprove = async () => {
    if (!selectedNotification) return;
    
    setLoading(true);
    try {
      await adminAPI.approveMedicalCertificate(selectedNotification.id);
      await loadNotifications(); // Обновляем список уведомлений
      setShowModal(false);
      setSelectedNotification(null);
    } catch (error) {
      console.error('Ошибка подтверждения справки:', error);
    } finally {
      setLoading(false);
    }
  };

  // Отклонение справки
  const handleReject = async () => {
    if (!selectedNotification) return;
    
    setLoading(true);
    try {
      await adminAPI.rejectMedicalCertificate(selectedNotification.id);
      await loadNotifications(); // Обновляем список уведомлений
      setShowModal(false);
      setSelectedNotification(null);
    } catch (error) {
      console.error('Ошибка отклонения справки:', error);
    } finally {
      setLoading(false);
    }
  };

  // Форматирование даты
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  // Определение типа уведомления
  const getNotificationType = (certificate) => {
    if (certificate.absence_reason && certificate.absence_reason.trim()) {
      return 'refund';
    }
    return 'certificate';
  };

  // Обработка формы расписания
  const handleScheduleFormChange = (e) => {
    const { name, value } = e.target;
    setScheduleForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Обработка формы массового создания
  const handleBulkScheduleFormChange = (e) => {
    const { name, value, checked } = e.target;
    
    if (name === 'weekdays') {
      const weekday = parseInt(value);
      setBulkScheduleForm(prev => ({
        ...prev,
        weekdays: checked 
          ? [...prev.weekdays, weekday]
          : prev.weekdays.filter(day => day !== weekday)
      }));
    } else {
      setBulkScheduleForm(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Создание тренировки
  const handleCreateTraining = async (e) => {
    e.preventDefault();
    if (!selectedGroup) {
      alert('Выберите группу');
      return;
    }

    setLoading(true);
    try {
      let response;
      
      if (scheduleMode === 'bulk') {
        // Массовое создание
        if (bulkScheduleForm.weekdays.length === 0) {
          alert('Выберите хотя бы один день недели');
          return;
        }
        
        response = await adminAPI.createTraining({
          group_id: selectedGroup.id,
          bulk_create: true,
          ...bulkScheduleForm
        });
        
        // Сбрасываем форму
        setBulkScheduleForm({
          start_date: '',
          end_date: '',
          weekdays: [],
          time: '',
          duration_minutes: 40,
          location: '',
          notes: ''
        });
      } else {
        // Одиночное создание или редактирование
        if (editingTraining) {
          // Редактирование существующей тренировки
          response = await adminAPI.updateTraining(editingTraining.id, scheduleForm);
        } else {
          // Создание новой тренировки
          response = await adminAPI.createTraining({
            group_id: selectedGroup.id,
            ...scheduleForm
          });
        }
        
        // Сбрасываем форму
        setScheduleForm({
          date: '',
          time: '',
          duration_minutes: 40,
          location: '',
          notes: ''
        });
        setEditingTraining(null);
      }
      
      setShowScheduleForm(false);
      
      // Обновляем расписание группы
      if (selectedGroup) {
        await loadGroupSchedule(selectedGroup.id);
      }
      
      alert(response.message || 'Тренировка успешно создана!');
    } catch (error) {
      console.error('Ошибка создания тренировки:', error);
      alert('Ошибка создания тренировки: ' + (error.error || 'Неизвестная ошибка'));
    } finally {
      setLoading(false);
    }
  };

  // Загружаем данные при монтировании компонента
  useEffect(() => {
    loadNotifications();
    loadGroups();
  }, [loadNotifications, loadGroups]);

  return (
    <div className={styles.dashboard}>
      {/* Заголовок с уведомлениями */}
      <header className={styles.header}>
        <h1 className={styles.title}>Кабинет администратора</h1>
        
        {/* Вкладки навигации */}
        <div className={styles.tabs}>
          <button 
            className={`${styles.tab} ${activeTab === 'notifications' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('notifications')}
          >
            📋 Уведомления
            {notifications.length > 0 && (
              <span className={styles.tabBadge}>{notifications.length}</span>
            )}
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'schedule' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            📅 Расписание
          </button>
        </div>
        
        <div className={styles.headerActions}>
          <div className={styles.notificationContainer}>
            <button 
              className={styles.notificationButton}
              onClick={() => setShowNotifications(!showNotifications)}
            >
              📋
              {notifications.length > 0 && (
                <span className={styles.notificationBadge}>{notifications.length}</span>
              )}
            </button>
            
            {/* Выпадающий список уведомлений */}
            {showNotifications && (
              <div className={styles.notificationsDropdown}>
                <div className={styles.notificationsHeader}>
                  <h3>Уведомления о справках</h3>
                  <button 
                    className={styles.closeButton}
                    onClick={() => setShowNotifications(false)}
                  >
                    ✕
                  </button>
                </div>
                
                {notifications.length === 0 ? (
                  <div className={styles.noNotifications}>
                    Нет новых уведомлений
                  </div>
                ) : (
                  <div className={styles.notificationsList}>
                    {notifications.map((notification) => (
                      <div 
                        key={notification.id}
                        className={styles.notificationItem}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className={styles.notificationType}>
                          {getNotificationType(notification) === 'refund' ? '💰' : '📄'}
                        </div>
                        <div className={styles.notificationContent}>
                          <div className={styles.notificationTitle}>
                            {getNotificationType(notification) === 'refund' 
                              ? 'Запрос на перерасчет' 
                              : 'Медицинская справка'
                            }
                          </div>
                          <div className={styles.notificationDetails}>
                            <strong>{notification.child_name}</strong> • {formatDate(notification.date_from)} - {formatDate(notification.date_to)}
                          </div>
                          <div className={styles.notificationDate}>
                            {formatDate(notification.uploaded_at)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
          
          <button className={styles.logoutButton} onClick={onLogout}>
            Выйти
          </button>
        </div>
      </header>

      {/* Основной контент */}
      <main className={styles.main}>
        {/* Вкладка уведомлений */}
        {activeTab === 'notifications' && (
          <div className={styles.tabContent}>
            {notifications.length > 0 ? (
              <div className={styles.alert}>
                У вас есть {notifications.length} {notifications.length === 1 ? 'новое уведомление' : 'новых уведомления'} о справках
              </div>
            ) : (
              <div className={styles.noNotificationsMain}>
                <h3>Нет новых уведомлений</h3>
                <p>Все справки и запросы на перерасчет обработаны</p>
              </div>
            )}
          </div>
        )}

        {/* Вкладка расписания */}
        {activeTab === 'schedule' && (
          <div className={styles.tabContent}>
            <div className={styles.scheduleContainer}>
              <div className={styles.scheduleHeader}>
                <h2>Составление расписания тренировок</h2>
                {selectedGroup && (
                  <div className={styles.scheduleActions}>
                    <button 
                      className={styles.addTrainingButton}
                      onClick={() => {
                        setScheduleMode('bulk');
                        setShowScheduleForm(true);
                      }}
                    >
                      📅 Быстрое составление
                    </button>
                    <button 
                      className={styles.editTrainingButton}
                      onClick={() => {
                        setScheduleMode('single');
                        setShowScheduleForm(true);
                      }}
                    >
                      ➕ Добавить тренировку
                    </button>
                  </div>
                )}
              </div>

              <div className={styles.scheduleContent}>
                {/* Выбор детского сада */}
                <div className={styles.kindergartenSelector}>
                  <h3>Выберите детский сад:</h3>
                  <div className={styles.kindergartenList}>
                    {kindergartens.map((kindergarten) => (
                      <button
                        key={kindergarten.number}
                        className={`${styles.kindergartenCard} ${selectedKindergarten?.number === kindergarten.number ? styles.selected : ''}`}
                        onClick={() => {
                          setSelectedKindergarten(kindergarten);
                          setSelectedGroup(null);
                        }}
                      >
                        <h4>Детский сад №{kindergarten.number}</h4>
                        <p>{kindergarten.groups.length} {kindergarten.groups.length === 1 ? 'группа' : 'групп'}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Выбор группы */}
                {selectedKindergarten && (
                  <div className={styles.groupSelector}>
                    <h3>Выберите группу:</h3>
                    <div className={styles.groupList}>
                      {selectedKindergarten.groups.map((group) => (
                        <button
                          key={group.id}
                          className={`${styles.groupCard} ${selectedGroup?.id === group.id ? styles.selected : ''}`}
                          onClick={() => {
                            setSelectedGroup(group);
                            loadGroupSchedule(group.id);
                          }}
                        >
                          <h4>{group.name}</h4>
                          <p>Возраст: {group.age_level}</p>
                          <p>Тренер: {group.trainer.name}</p>
                          <p>Детей: {group.children_count}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Существующие тренировки группы */}
                {selectedGroup && groupSchedule.length > 0 && (
                  <div className={styles.existingTrainings}>
                    <h3>Существующие тренировки группы "{selectedGroup.name}"</h3>
                    <div className={styles.trainingsList}>
                      {groupSchedule.map((training) => (
                        <div key={training.id} className={styles.trainingCard}>
                          <div className={styles.trainingInfo}>
                            <div className={styles.trainingDate}>{training.date}</div>
                            <div className={styles.trainingTime}>{training.time}</div>
                            <div className={styles.trainingStatus}>{training.status}</div>
                          </div>
                          <div className={styles.trainingActions}>
                            <button 
                              className={styles.editButton}
                              onClick={() => {
                                setEditingTraining(training);
                                setScheduleMode('single');
                                setScheduleForm({
                                  date: training.date.split('.').reverse().join('-'), // DD.MM.YYYY -> YYYY-MM-DD
                                  time: training.time,
                                  duration_minutes: training.duration_minutes,
                                  location: training.location,
                                  notes: training.notes
                                });
                                setShowScheduleForm(true);
                              }}
                            >
                              ✏️ Редактировать
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Форма создания тренировки */}
                {showScheduleForm && selectedGroup && (
                  <div className={styles.scheduleFormContainer}>
                    <div className={styles.scheduleFormHeader}>
                      <h3>
                        {scheduleMode === 'bulk' 
                          ? 'Быстрое составление расписания' 
                          : editingTraining 
                            ? 'Редактировать тренировку'
                            : 'Добавить тренировку'
                        } для группы "{selectedGroup.name}"
                      </h3>
                      <button 
                        className={styles.closeButton}
                        onClick={() => setShowScheduleForm(false)}
                      >
                        ✕
                      </button>
                    </div>
                    
                    <form onSubmit={handleCreateTraining} className={styles.scheduleForm}>
                      {scheduleMode === 'bulk' ? (
                        // Форма массового создания
                        <>
                          <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                              <label>Дата начала периода:</label>
                              <input
                                type="date"
                                name="start_date"
                                value={bulkScheduleForm.start_date}
                                onChange={handleBulkScheduleFormChange}
                                required
                              />
                            </div>
                            <div className={styles.formGroup}>
                              <label>Дата окончания периода:</label>
                              <input
                                type="date"
                                name="end_date"
                                value={bulkScheduleForm.end_date}
                                onChange={handleBulkScheduleFormChange}
                                required
                              />
                            </div>
                          </div>
                          
                          <div className={styles.formGroup}>
                            <label>Дни недели для тренировок:</label>
                            <div className={styles.weekdaysSelector}>
                              {[
                                { value: 0, label: 'Понедельник' },
                                { value: 1, label: 'Вторник' },
                                { value: 2, label: 'Среда' },
                                { value: 3, label: 'Четверг' },
                                { value: 4, label: 'Пятница' },
                                { value: 5, label: 'Суббота' },
                                { value: 6, label: 'Воскресенье' }
                              ].map((day) => (
                                <label key={day.value} className={styles.checkboxLabel}>
                                  <input
                                    type="checkbox"
                                    name="weekdays"
                                    value={day.value}
                                    checked={bulkScheduleForm.weekdays.includes(day.value)}
                                    onChange={handleBulkScheduleFormChange}
                                  />
                                  {day.label}
                                </label>
                              ))}
                            </div>
                          </div>
                          
                          <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                              <label>Время тренировки:</label>
                              <input
                                type="time"
                                name="time"
                                value={bulkScheduleForm.time}
                                onChange={handleBulkScheduleFormChange}
                                required
                              />
                            </div>
                            <div className={styles.formGroup}>
                              <label>Продолжительность (минуты):</label>
                              <input
                                type="number"
                                name="duration_minutes"
                                value={bulkScheduleForm.duration_minutes}
                                onChange={handleBulkScheduleFormChange}
                                min="15"
                                max="120"
                                required
                              />
                            </div>
                          </div>
                          
                          <div className={styles.formGroup}>
                            <label>Место проведения:</label>
                            <input
                              type="text"
                              name="location"
                              value={bulkScheduleForm.location}
                              onChange={handleBulkScheduleFormChange}
                              placeholder="Спортивный зал, площадка и т.д."
                            />
                          </div>
                          
                          <div className={styles.formGroup}>
                            <label>Заметки:</label>
                            <textarea
                              name="notes"
                              value={bulkScheduleForm.notes}
                              onChange={handleBulkScheduleFormChange}
                              placeholder="Дополнительная информация о тренировках"
                            />
                          </div>
                          
                          <div className={styles.formActions}>
                            <button 
                              type="button" 
                              className={styles.cancelButton}
                              onClick={() => setShowScheduleForm(false)}
                            >
                              Отмена
                            </button>
                            <button 
                              type="submit" 
                              className={styles.createButton}
                              disabled={loading}
                            >
                              {loading ? 'Создание...' : 'Создать расписание'}
                            </button>
                          </div>
                        </>
                      ) : (
                        // Форма одиночного создания
                        <>
                      <div className={styles.formRow}>
                        <div className={styles.formGroup}>
                          <label>Дата тренировки:</label>
                          <input
                            type="date"
                            name="date"
                            value={scheduleForm.date}
                            onChange={handleScheduleFormChange}
                            required
                          />
                        </div>
                        <div className={styles.formGroup}>
                          <label>Время тренировки:</label>
                          <input
                            type="time"
                            name="time"
                            value={scheduleForm.time}
                            onChange={handleScheduleFormChange}
                            required
                          />
                        </div>
                      </div>
                      
                      <div className={styles.formRow}>
                        <div className={styles.formGroup}>
                          <label>Продолжительность (минуты):</label>
                          <input
                            type="number"
                            name="duration_minutes"
                            value={scheduleForm.duration_minutes}
                            onChange={handleScheduleFormChange}
                            min="15"
                            max="120"
                            required
                          />
                        </div>
                        <div className={styles.formGroup}>
                          <label>Место проведения:</label>
                          <input
                            type="text"
                            name="location"
                            value={scheduleForm.location}
                            onChange={handleScheduleFormChange}
                            placeholder="Спортивный зал, площадка и т.д."
                          />
                        </div>
                      </div>
                      
                      <div className={styles.formGroup}>
                        <label>Заметки:</label>
                        <textarea
                          name="notes"
                          value={scheduleForm.notes}
                          onChange={handleScheduleFormChange}
                          placeholder="Дополнительная информация о тренировке"
                        />
                      </div>
                      
                      <div className={styles.formActions}>
                        <button 
                          type="button" 
                          className={styles.cancelButton}
                          onClick={() => setShowScheduleForm(false)}
                        >
                          Отмена
                        </button>
                        <button 
                          type="submit" 
                          className={styles.createButton}
                          disabled={loading}
                        >
                          {loading ? 'Создание...' : 'Создать тренировку'}
                        </button>
                      </div>
                        </>
                      )}
                    </form>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Модальное окно для просмотра справки */}
      {showModal && selectedNotification && (
        <div className={styles.modalOverlay}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3>
                {getNotificationType(selectedNotification) === 'refund' 
                  ? 'Запрос на перерасчет' 
                  : 'Медицинская справка'
                }
              </h3>
              <button 
                className={styles.closeButton}
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>
            
            <div className={styles.modalContent}>
              <div className={styles.certificateInfo}>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Ребенок:</span>
                  <span className={styles.infoValue}>{selectedNotification.child_name}</span>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Период отсутствия:</span>
                  <span className={styles.infoValue}>
                    {formatDate(selectedNotification.date_from)} - {formatDate(selectedNotification.date_to)}
                  </span>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>Дата подачи:</span>
                  <span className={styles.infoValue}>{formatDate(selectedNotification.uploaded_at)}</span>
                </div>
                
                {selectedNotification.note && (
                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Примечание:</span>
                    <span className={styles.infoValue}>{selectedNotification.note}</span>
                  </div>
                )}
                
                {selectedNotification.absence_reason && (
                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Причина отсутствия:</span>
                    <span className={styles.infoValue}>{selectedNotification.absence_reason}</span>
                  </div>
                )}
                
                {selectedNotification.file_url && (
                  <div className={styles.infoRow}>
                    <span className={styles.infoLabel}>Прикрепленный файл:</span>
                    <a 
                      href={selectedNotification.file_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className={styles.fileLink}
                    >
                      📎 {selectedNotification.file_name || 'Открыть файл'}
                    </a>
                  </div>
                )}
              </div>
            </div>
            
            <div className={styles.modalActions}>
              <button 
                className={styles.rejectButton}
                onClick={handleReject}
                disabled={loading}
              >
                Отклонить
              </button>
              <button 
                className={styles.approveButton}
                onClick={handleApprove}
                disabled={loading}
              >
                {loading ? 'Обработка...' : 'Подтвердить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard; 