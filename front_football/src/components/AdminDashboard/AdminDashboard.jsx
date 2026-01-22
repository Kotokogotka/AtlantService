import React, { useState, useEffect, useCallback } from 'react';
import { adminAPI, scheduleAPI } from '../../utils/api';
import styles from './AdminDashboard.module.css';

function AdminDashboard({ userInfo, onLogout }) {
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('notifications'); // 'notifications', 'schedule', 'attendance', 'attendance_table'
  
  // Состояние для таблицы посещений
  const [attendanceTableData, setAttendanceTableData] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState('');
  const [trainingDates, setTrainingDates] = useState([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [kindergartens, setKindergartens] = useState([]);
  const [selectedKindergarten, setSelectedKindergarten] = useState(null);
  const [selectedAgeGroup, setSelectedAgeGroup] = useState(null);
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
  
  // Состояния для вкладки посещений
  const [attendanceData, setAttendanceData] = useState([]);
  const [attendanceFilters, setAttendanceFilters] = useState({
    groupId: '',
    childId: '',
    dateFrom: '',
    dateTo: ''
  });
  const [children, setChildren] = useState([]);
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

  // Удаление тренировки
  const handleDeleteTraining = async (trainingId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту тренировку?')) {
      return;
    }

    setLoading(true);
    try {
      await adminAPI.deleteTraining(trainingId);
      // Обновляем расписание группы
      if (selectedGroup) {
        await loadGroupSchedule(selectedGroup.id);
      }
      alert('Тренировка успешно удалена');
    } catch (error) {
      console.error('Ошибка удаления тренировки:', error);
      alert('Ошибка при удалении тренировки: ' + (error.error || 'Неизвестная ошибка'));
    } finally {
      setLoading(false);
    }
  };

  // Функции для работы с посещениями
  const loadAttendanceData = async () => {
    setLoading(true);
    try {
      const response = await adminAPI.getAttendanceData(attendanceFilters);
      setAttendanceData(response.children || []);
    } catch (error) {
      console.error('Ошибка загрузки данных о посещениях:', error);
      alert('Ошибка при загрузке данных о посещениях: ' + (error.error || 'Неизвестная ошибка'));
    } finally {
      setLoading(false);
    }
  };

  // Функции для таблицы посещений
  const handleMonthSelect = (month) => {
    setSelectedMonth(month);
    setSelectedKindergarten(null);
    setSelectedAgeGroup(null);
    setAttendanceTableData([]);
    setTrainingDates([]);
    loadMonthData(month);
  };

  const handleKindergartenSelect = (kindergarten) => {
    setSelectedKindergarten(kindergarten);
    setSelectedAgeGroup(null);
  };

  const handleAgeGroupSelect = (ageGroup) => {
    setSelectedAgeGroup(ageGroup);
    if (selectedMonth && selectedKindergarten) {
      loadAttendanceTableDataFiltered(selectedMonth, selectedKindergarten.kindergarten_number, ageGroup);
    }
  };

  // Функция для загрузки данных при выборе месяца
  const loadMonthData = async (month) => {
    setTableLoading(true);
    try {
      console.log(`Загрузка данных для месяца: ${month}`);
      const response = await adminAPI.getAttendanceTableData(month);
      
      console.log('Полный ответ от API:', response);
      
      if (response && response.children) {
        // Группируем детей по садам
        const kindergartenMap = {};
        response.children.forEach(child => {
          const kgNum = child.group_number;
          if (!kindergartenMap[kgNum]) {
            kindergartenMap[kgNum] = [];
          }
          kindergartenMap[kgNum].push(child);
        });
        
        // Создаем массив садов
        const kgList = Object.keys(kindergartenMap).map(kgNum => ({
          kindergarten_number: parseInt(kgNum),
          children: kindergartenMap[kgNum]
        }));
        
        console.log('Обработанные сады:', kgList);
        setKindergartens(kgList);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных месяца:', error);
    } finally {
      setTableLoading(false);
    }
  };

  // Функция для подсчета детей по возрастным группам
  const getAgeGroupCounts = (kindergartenNum) => {
    if (!selectedMonth) return { младшая: 0, средняя: 0, старшая: 0 };
    
    const kindergarten = kindergartens.find(kg => kg.kindergarten_number === kindergartenNum);
    if (!kindergarten) return { младшая: 0, средняя: 0, старшая: 0 };
    
    const counts = { младшая: 0, средняя: 0, старшая: 0 };
    
    kindergarten.children.forEach(child => {
      const groupName = (child.group_name || '').toLowerCase();
      if (groupName.includes('младш')) {
        counts.младшая++;
      } else if (groupName.includes('средн')) {
        counts.средняя++;
      } else if (groupName.includes('старш')) {
        counts.старшая++;
      }
    });
    
    console.log(`Подсчет для сада ${kindergartenNum}:`, counts);
    return counts;
  };

  const loadAttendanceTableDataFiltered = async (month, kindergartenNum, ageGroup) => {
    setTableLoading(true);
    setAttendanceTableData([]);
    setTrainingDates([]);
    
    try {
      console.log(`Загрузка данных: месяц=${month}, сад=${kindergartenNum}, группа=${ageGroup}`);
      const response = await adminAPI.getAttendanceTableData(month);
      
      console.log('Ответ от API:', response);
      
      if (response && response.children) {
        // Фильтруем детей по детскому саду и возрастной группе
        console.log(`Фильтр: ищем сад ${kindergartenNum} (тип: ${typeof kindergartenNum})`);
        
        let filteredChildren = response.children.filter(child => {
          const childKgNum = parseInt(child.group_number);
          const searchKgNum = parseInt(kindergartenNum);
          console.log(`Ребенок: ${child.child_name}, Сад: ${child.group_number} (${childKgNum}), Ищем: ${searchKgNum}, Совпадение: ${childKgNum === searchKgNum}`);
          return childKgNum === searchKgNum;
        });

        console.log(`После фильтра по саду ${kindergartenNum}: ${filteredChildren.length} детей`);

        // Фильтруем по возрастной группе
        filteredChildren = filteredChildren.filter(child => {
          const groupName = (child.group_name || '').toLowerCase();
          if (ageGroup === 'младшая') {
            return groupName.includes('младш');
          } else if (ageGroup === 'средняя') {
            return groupName.includes('средн');
          } else if (ageGroup === 'старшая') {
            return groupName.includes('старш');
          }
          return false;
        });

        console.log(`После фильтра по возрасту: ${filteredChildren.length} детей`);
        setAttendanceTableData(filteredChildren);
      } else {
        setAttendanceTableData([]);
      }
      
      if (response && response.training_dates) {
        setTrainingDates(response.training_dates);
      } else {
        setTrainingDates([]);
      }
      
    } catch (error) {
      console.error('Ошибка загрузки таблицы посещений:', error);
      setAttendanceTableData([]);
      setTrainingDates([]);
      
      const errorMessage = error.error || error.message || 'Неизвестная ошибка';
      alert(`Ошибка при загрузке таблицы посещений: ${errorMessage}`);
    } finally {
      setTableLoading(false);
    }
  };

  const getAvailableMonths = () => {
    const months = [];
    
    // Добавляем сентябрь и октябрь 2025
    const september = new Date(2025, 8, 1); // месяц 8 = сентябрь
    const october = new Date(2025, 9, 1);   // месяц 9 = октябрь
    
    months.push({
      value: '2025-09',
      label: september.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })
    });
    
    months.push({
      value: '2025-10',
      label: october.toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })
    });
    
    return months;
  };

  const getAttendanceSymbol = (childId, date) => {
    const child = attendanceTableData.find(c => c.child_id === childId);
    if (!child || !child.attendances) return '';
    
    // Ищем посещение по дате (формат YYYY-MM-DD)
    const attendance = child.attendances.find(a => a.date === date);
    if (!attendance) return '';
    
    if (attendance.attended) return '+';
    if (attendance.absence_reason && attendance.absence_reason.toLowerCase().includes('справка')) return 'С';
    return ''; // Пустая клетка для отсутствия без причины
  };

  // Подсчёт посещений ребёнка за месяц
  const getChildAttendanceCount = (childId) => {
    const child = attendanceTableData.find(c => c.child_id === childId);
    if (!child || !child.attendances) return 0;
    
    return child.attendances.filter(a => a.attended).length;
  };

  // Подсчёт посещений по конкретной дате
  const getDateAttendanceCount = (date) => {
    let count = 0;
    attendanceTableData.forEach(child => {
      if (child.attendances) {
        const attendance = child.attendances.find(a => a.date === date && a.attended);
        if (attendance) count++;
      }
    });
    return count;
  };

  const loadChildren = async (groupId) => {
    if (!groupId) {
      setChildren([]);
      return;
    }
    try {
      const response = await adminAPI.getGroupChildren(groupId);
      setChildren(response.children || []);
    } catch (error) {
      console.error('Ошибка загрузки детей:', error);
      setChildren([]);
    }
  };

  const handleAttendanceFilterChange = (field, value) => {
    setAttendanceFilters(prev => ({
      ...prev,
      [field]: value
    }));
    
    if (field === 'groupId') {
      setAttendanceFilters(prev => ({
        ...prev,
        childId: '' // Сбрасываем выбор ребенка при смене группы
      }));
      loadChildren(value);
    }
  };

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
          <button 
            className={`${styles.tab} ${activeTab === 'attendance' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('attendance')}
          >
            👥 Посещения
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'attendance_table' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('attendance_table')}
          >
            📊 Таблица посещений
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
                    {kindergartens && kindergartens.map((kindergarten) => (
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
                              title="Редактировать тренировку"
                            >
                              ✏️
                            </button>
                            <button 
                              className={styles.deleteButton}
                              onClick={() => handleDeleteTraining(training.id)}
                              disabled={loading}
                              title="Удалить тренировку"
                            >
                              🗑️
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

        {/* Вкладка посещений */}
        {activeTab === 'attendance' && (
          <div className={styles.tabContent}>
            <div className={styles.attendanceContainer}>
              <div className={styles.attendanceHeader}>
                <h2>Посещения детей</h2>
                <p>Просмотр посещений и расчет оплаты</p>
              </div>

              {/* Фильтры */}
              <div className={styles.attendanceFilters}>
                <div className={styles.filterRow}>
                  <div className={styles.filterGroup}>
                    <label>Детский сад:</label>
                    <select 
                      value={selectedKindergarten?.number || ''} 
                      onChange={(e) => {
                        const kindergarten = kindergartens.find(k => k.number === e.target.value);
                        setSelectedKindergarten(kindergarten);
                        setSelectedGroup(null);
                        setAttendanceFilters(prev => ({ ...prev, groupId: '', childId: '' }));
                      }}
                    >
                      <option value="">Выберите сад</option>
                      {kindergartens && kindergartens.map(k => (
                        <option key={k.number} value={k.number}>
                          Детский сад №{k.number} - {k.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className={styles.filterGroup}>
                    <label>Группа:</label>
                    <select 
                      value={attendanceFilters.groupId} 
                      onChange={(e) => {
                        const groupId = e.target.value;
                        handleAttendanceFilterChange('groupId', groupId);
                        // Устанавливаем selectedGroup для совместимости
                        if (selectedKindergarten) {
                          const group = selectedKindergarten.groups.find(g => g.id === parseInt(groupId));
                          setSelectedGroup(group);
                        }
                      }}
                      disabled={!selectedKindergarten}
                    >
                      <option value="">Выберите группу</option>
                      {selectedKindergarten?.groups.map(group => (
                        <option key={group.id} value={group.id}>
                          {group.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className={styles.filterGroup}>
                    <label>Ребенок:</label>
                    <select 
                      value={attendanceFilters.childId} 
                      onChange={(e) => handleAttendanceFilterChange('childId', e.target.value)}
                      disabled={!attendanceFilters.groupId}
                    >
                      <option value="">Все дети ({children.length})</option>
                      {children.map(child => (
                        <option key={child.id} value={child.id}>
                          {child.full_name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className={styles.filterRow}>
                  <div className={styles.filterGroup}>
                    <label>Период с:</label>
                    <input 
                      type="date" 
                      value={attendanceFilters.dateFrom} 
                      onChange={(e) => handleAttendanceFilterChange('dateFrom', e.target.value)}
                    />
                  </div>

                  <div className={styles.filterGroup}>
                    <label>Период по:</label>
                    <input 
                      type="date" 
                      value={attendanceFilters.dateTo} 
                      onChange={(e) => handleAttendanceFilterChange('dateTo', e.target.value)}
                    />
                  </div>

                  <div className={styles.filterGroup}>
                    <button 
                      className={styles.searchButton}
                      onClick={loadAttendanceData}
                      disabled={loading}
                    >
                      {loading ? 'Загрузка...' : '🔍 Найти'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Результаты */}
              {attendanceData.length > 0 && (
                <div className={styles.attendanceResults}>
                  <div className={styles.resultsHeader}>
                    <div>
                      <h3>Результаты поиска</h3>
                      {attendanceFilters.dateFrom && attendanceFilters.dateTo && (
                        <p className={styles.periodInfo}>
                          Период: {new Date(attendanceFilters.dateFrom).toLocaleDateString('ru-RU')} - {new Date(attendanceFilters.dateTo).toLocaleDateString('ru-RU')}
                        </p>
                      )}
                    </div>
                    <span className={styles.resultsCount}>{attendanceData.length} {attendanceData.length === 1 ? 'ребенок' : attendanceData.length < 5 ? 'ребенка' : 'детей'}</span>
                  </div>
                  
                  {attendanceData.map(child => (
                    <div key={child.child_id} className={styles.childCard}>
                      <div className={styles.childHeader}>
                        <div className={styles.childMainInfo}>
                          <h4>{child.child_name}</h4>
                          <div className={styles.childBadges}>
                            <span className={styles.badge}>{child.kindergarten_name}</span>
                            <span className={styles.badge}>{child.group_name}</span>
                          </div>
                        </div>
                        <div className={styles.childPayment}>
                          <span className={styles.paymentLabel}>К оплате:</span>
                          <span className={styles.paymentAmount}>{child.payment_amount}₽</span>
                          <span className={styles.paymentDetails}>
                            {child.billable_trainings} × {child.price_per_training}₽
                          </span>
                        </div>
                      </div>

                      <div className={styles.childStats}>
                        <div className={styles.statBox}>
                          <span className={styles.statNumber}>{child.total_trainings}</span>
                          <span className={styles.statTitle}>Всего</span>
                        </div>
                        <div className={`${styles.statBox} ${styles.successBox}`}>
                          <span className={styles.statNumber}>{child.attended_trainings}</span>
                          <span className={styles.statTitle}>Посетил</span>
                        </div>
                        <div className={`${styles.statBox} ${styles.warningBox}`}>
                          <span className={styles.statNumber}>{child.missed_trainings}</span>
                          <span className={styles.statTitle}>Пропустил</span>
                        </div>
                        <div className={`${styles.statBox} ${styles.infoBox}`}>
                          <span className={styles.statNumber}>{child.confirmed_absences}</span>
                          <span className={styles.statTitle}>Подтверждено</span>
                        </div>
                      </div>

                      {child.attendances && child.attendances.length > 0 && (
                        <details className={styles.attendanceDetails}>
                          <summary className={styles.attendanceSummary}>
                            📋 Детали посещений ({child.attendances.length})
                          </summary>
                          <div className={styles.attendanceGrid}>
                            {child.attendances.map(attendance => (
                              <div 
                                key={attendance.id} 
                                className={`${styles.attendanceCard} ${attendance.attended ? styles.attendedCard : styles.missedCard}`}
                                title={attendance.absence_reason || ''}
                              >
                                <span className={styles.attendanceIcon}>
                                  {attendance.attended ? '✅' : '❌'}
                                </span>
                                <div className={styles.attendanceInfo}>
                                  <span className={styles.attendanceDateTime}>{attendance.date}</span>
                                  {attendance.absence_reason && (
                                    <span className={styles.attendanceReason}>{attendance.absence_reason}</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {attendanceData.length === 0 && !loading && (
                <div className={styles.noData}>
                  <p>Выберите фильтры и нажмите "Найти" для просмотра посещений</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Вкладка таблицы посещений */}
        {activeTab === 'attendance_table' && (
          <div className={styles.tabContent}>
            <div className={styles.attendanceTableContainer}>
              <div className={styles.attendanceTableHeader}>
                <h2>Таблица посещений</h2>
                <p>Просмотр посещений в формате таблицы Excel</p>
              </div>

              {/* Шаг 1: Выбор месяца */}
              <div className={styles.filterSection}>
                <h3>Шаг 1: Выберите месяц</h3>
                <div className={styles.filterButtons}>
                  {getAvailableMonths().map(month => (
                    <button
                      key={month.value}
                      className={`${styles.filterButton} ${selectedMonth === month.value ? styles.activeFilter : ''}`}
                      onClick={() => handleMonthSelect(month.value)}
                      disabled={tableLoading}
                    >
                      {month.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Шаг 2: Выбор детского сада */}
              {selectedMonth && kindergartens && kindergartens.length > 0 && (
                <div className={styles.filterSection}>
                  <h3>Шаг 2: Выберите детский сад</h3>
                  <div className={styles.filterButtons}>
                    {kindergartens.map(kg => (
                      <button
                        key={kg.kindergarten_number}
                        className={`${styles.filterButton} ${selectedKindergarten?.kindergarten_number === kg.kindergarten_number ? styles.activeFilter : ''}`}
                        onClick={() => handleKindergartenSelect(kg)}
                        disabled={tableLoading}
                      >
                        Сад №{kg.kindergarten_number} ({kg.children?.length || 0} детей)
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Шаг 3: Выбор возрастной группы */}
              {selectedMonth && selectedKindergarten && (
                <div className={styles.filterSection}>
                  <h3>Шаг 3: Выберите возрастную группу</h3>
                  <div className={styles.filterButtons}>
                    {['младшая', 'средняя', 'старшая'].map(ageGroup => {
                      const counts = getAgeGroupCounts(selectedKindergarten.kindergarten_number);
                      const count = counts[ageGroup] || 0;
                      return (
                        <button
                          key={ageGroup}
                          className={`${styles.filterButton} ${selectedAgeGroup === ageGroup ? styles.activeFilter : ''}`}
                          onClick={() => handleAgeGroupSelect(ageGroup)}
                          disabled={tableLoading || count === 0}
                        >
                          {ageGroup.charAt(0).toUpperCase() + ageGroup.slice(1)} группа ({count} детей)
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Таблица посещений */}
              {attendanceTableData.length > 0 && trainingDates.length > 0 && selectedAgeGroup && (
                <div className={styles.excelTable}>
                  <div className={styles.tableInfo}>
                    <p>
                      <strong>Сад №{selectedKindergarten.kindergarten_number}</strong> • 
                      <strong> {selectedAgeGroup.charAt(0).toUpperCase() + selectedAgeGroup.slice(1)} группа</strong> • 
                      <strong> {new Date(selectedMonth + '-01').toLocaleDateString('ru-RU', { year: 'numeric', month: 'long' })}</strong>
                    </p>
                  </div>
                  <div className={styles.compactTableWrapper}>
                    <table className={styles.compactTable}>
                      <thead>
                        <tr>
                          <th className={styles.compactFioColumn}>ФИО ребенка</th>
                          <th className={styles.compactBirthdateColumn}>Дата рождения</th>
                          <th className={styles.compactGroupColumn}>Группа</th>
                          {trainingDates.map(date => (
                            <th key={date} className={styles.compactDateColumn}>
                              {new Date(date).getDate()}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {attendanceTableData.map(child => {
                          const attendanceCount = getChildAttendanceCount(child.child_id);
                          const birthdate = child.birth_date ? new Date(child.birth_date).toLocaleDateString('ru-RU') : '-';
                          return (
                            <tr key={child.child_id}>
                              <td className={styles.compactFioCell}>
                                {child.child_name} <span className={styles.attendanceCount}>({attendanceCount})</span>
                              </td>
                              <td className={styles.compactBirthdateCell}>{birthdate}</td>
                              <td className={styles.compactGroupCell}>{child.group_name}</td>
                              {trainingDates.map(date => {
                                const symbol = getAttendanceSymbol(child.child_id, date);
                                const cellClass = symbol === '+' 
                                  ? `${styles.compactAttendanceCell} ${styles.plusSymbol}`
                                  : symbol === 'С'
                                  ? `${styles.compactAttendanceCell} ${styles.certificateSymbol}`
                                  : styles.compactAttendanceCell;
                                return (
                                  <td key={date} className={cellClass}>
                                    {symbol}
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        })}
                        {/* Строка с общим количеством посещений по датам */}
                        <tr className={styles.totalRow}>
                          <td className={styles.compactFioCell}><strong>Итого присутствовало:</strong></td>
                          <td className={styles.compactBirthdateCell}></td>
                          <td className={styles.compactGroupCell}></td>
                          {trainingDates.map(date => (
                            <td key={date} className={styles.compactAttendanceCell}>
                              <strong>{getDateAttendanceCount(date)}</strong>
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Информация о данных */}
              {attendanceTableData.length > 0 && trainingDates.length === 0 && (
                <div className={styles.noData}>
                  <p>Нет данных о тренировках для выбранного месяца</p>
                </div>
              )}

              {attendanceTableData.length === 0 && trainingDates.length > 0 && (
                <div className={styles.noData}>
                  <p>Нет данных о детях для выбранного месяца</p>
                </div>
              )}

              {tableLoading && (
                <div className={styles.loading}>
                  <p>Загрузка данных...</p>
                </div>
              )}

              {!tableLoading && !selectedMonth && (
                <div className={styles.noData}>
                  <p>👆 Начните с выбора месяца</p>
                </div>
              )}

              {!tableLoading && selectedMonth && !selectedKindergarten && (
                <div className={styles.noData}>
                  <p>👆 Теперь выберите детский сад</p>
                </div>
              )}

              {!tableLoading && selectedMonth && selectedKindergarten && !selectedAgeGroup && (
                <div className={styles.noData}>
                  <p>👆 Выберите возрастную группу для просмотра</p>
                </div>
              )}

              {!tableLoading && selectedAgeGroup && attendanceTableData.length === 0 && (
                <div className={styles.noData}>
                  <p>Нет данных для выбранных параметров</p>
                </div>
              )}
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