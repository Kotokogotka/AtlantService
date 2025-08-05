import React, { useState, useEffect } from 'react';
import { trainerAPI, apiUtils } from '../../utils/api';
import styles from './AttendancePage.module.css';

function AttendancePage({ userInfo, onLogout }) {
  const [kindergartens, setKindergartens] = useState([]);
  const [selectedKindergarten, setSelectedKindergarten] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [children, setChildren] = useState([]);
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [attendanceData, setAttendanceData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    loadAttendanceData();
  }, []);

  const loadAttendanceData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await trainerAPI.getAttendanceData();
      
      if (response.success) {
        setKindergartens(response.kindergartens);
      } else {
        setError('Не удалось загрузить данные');
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка загрузки данных:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKindergartenSelect = (kindergarten) => {
    setSelectedKindergarten(kindergarten);
    setSelectedGroup(null);
    setChildren([]);
    setAttendanceData({});
  };

  const handleGroupSelect = async (group) => {
    try {
      setSelectedGroup(group);
      setError(null);
      
      const response = await trainerAPI.getGroupChildren(group.id);
      
      if (response.success) {
        setChildren(response.children);
        
        // Инициализируем данные посещаемости (по умолчанию все присутствуют)
        const initialData = {};
        response.children.forEach(child => {
          initialData[child.id] = {
            child_id: child.id,
            status: true,
            reason: ''
          };
        });
        setAttendanceData(initialData);
      } else {
        setError('Не удалось загрузить список детей');
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка загрузки детей:', err);
    }
  };

  const handleAttendanceChange = (childId, status) => {
    setAttendanceData(prev => ({
      ...prev,
      [childId]: {
        ...prev[childId],
        status: status,
        reason: status ? '' : prev[childId]?.reason || ''
      }
    }));
  };

  const handleReasonChange = (childId, reason) => {
    setAttendanceData(prev => ({
      ...prev,
      [childId]: {
        ...prev[childId],
        reason: reason
      }
    }));
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      setSuccessMessage(null);
      
      const attendanceArray = Object.values(attendanceData);
      
      const response = await trainerAPI.createAttendance({
        group_id: selectedGroup.id,
        date: attendanceDate,
        attendance_data: attendanceArray
      });
      
      if (response.success) {
        setSuccessMessage(`Успешно отмечена посещаемость для ${response.created_count} детей`);
        // Очищаем форму
        setTimeout(() => {
          setSuccessMessage(null);
        }, 3000);
      } else {
        setError('Не удалось сохранить посещаемость');
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка сохранения посещаемости:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Не указана';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };



  return (
    <div className={styles.attendancePage}>
      {/* Шапка */}
      <header className={styles.header}>
        <div className={styles.userInfo}>
          <span>👤 {userInfo.username}</span>
          <span>Роль: {userInfo.role_display || userInfo.role}</span>
        </div>
      </header>

      {/* Основной контент */}
      <main className={styles.main}>
        <h1>Отметка посещаемости</h1>
        
        {error && (
          <div className={styles.error}>
            <p>Ошибка: {error}</p>
            <button onClick={loadAttendanceData}>Повторить</button>
          </div>
        )}

        {successMessage && (
          <div className={styles.success}>
            <p>{successMessage}</p>
          </div>
        )}
        
        {isLoading ? (
          <div className={styles.loading}>Загрузка данных...</div>
        ) : (
          <div className={styles.content}>
            {/* Выбор даты */}
            <div className={styles.dateSection}>
              <label htmlFor="attendanceDate">Дата тренировки:</label>
              <input
                type="date"
                id="attendanceDate"
                value={attendanceDate}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className={styles.dateInput}
              />
            </div>

            <div className={styles.selectionArea}>
              {/* Левая панель - выбор сада и группы */}
              <div className={styles.leftPanel}>
                <h2>Выберите детский сад и группу</h2>
                
                {kindergartens.map(kindergarten => (
                  <div key={kindergarten.number} className={styles.kindergartenCard}>
                    <h3 
                      className={`${styles.kindergartenTitle} ${selectedKindergarten?.number === kindergarten.number ? styles.selected : ''}`}
                      onClick={() => handleKindergartenSelect(kindergarten)}
                    >
                      Детский сад №{kindergarten.number}
                    </h3>
                    
                    {selectedKindergarten?.number === kindergarten.number && (
                      <div className={styles.groupsList}>
                        {kindergarten.groups.map(group => (
                          <div 
                            key={group.id} 
                            className={`${styles.groupItem} ${selectedGroup?.id === group.id ? styles.selected : ''}`}
                            onClick={() => handleGroupSelect(group)}
                          >
                            <span className={styles.groupName}>{group.name}</span>
                            <span className={styles.groupInfo}>
                              {group.age_level} • {group.children_count} детей
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Правая панель - список детей */}
              <div className={styles.rightPanel}>
                {selectedGroup ? (
                  <>
                    <h2>Группа: {selectedGroup.name}</h2>
                    <p className={styles.groupDetails}>
                      Детский сад №{selectedGroup.kindergarten_number} • {selectedGroup.age_level}
                    </p>
                    
                    {children.length > 0 ? (
                      <div className={styles.childrenList}>
                        {children.map(child => (
                          <div key={child.id} className={styles.childCard}>
                                                                                     <div className={styles.childInfo}>
                              <h4>{child.full_name}</h4>
                              <p>Дата рождения: {formatDate(child.birth_date)}</p>
                              <p>Родитель: {child.parent_name}</p>
                              {child.parent_phone && (
                                <p>Телефон: {child.parent_phone}</p>
                              )}
                              <p className={styles.attendanceCount}>
                                Посещено занятий в этом месяце: <strong>{child.attendance_count}</strong>
                              </p>
                            </div>
                            
                            <div className={styles.attendanceControls}>
                              <label className={styles.checkboxLabel}>
                                <input
                                  type="checkbox"
                                  checked={attendanceData[child.id]?.status || false}
                                  onChange={(e) => handleAttendanceChange(child.id, e.target.checked)}
                                  className={styles.checkbox}
                                />
                                <span>Присутствует</span>
                              </label>
                              
                              {!attendanceData[child.id]?.status && (
                                <input
                                  type="text"
                                  placeholder="Причина отсутствия"
                                  value={attendanceData[child.id]?.reason || ''}
                                  onChange={(e) => handleReasonChange(child.id, e.target.value)}
                                  className={styles.reasonInput}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className={styles.noChildren}>В группе нет активных детей</p>
                    )}
                    
                    {children.length > 0 && (
                      <div className={styles.submitSection}>
                        <button 
                          onClick={handleSubmit}
                          disabled={isSubmitting}
                          className={styles.submitButton}
                        >
                          {isSubmitting ? 'Сохранение...' : 'Отправить данные'}
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className={styles.noSelection}>
                    <p>Выберите группу для отметки посещаемости</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default AttendancePage; 