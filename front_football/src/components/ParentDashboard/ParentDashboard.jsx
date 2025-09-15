import React, { useState, useEffect, useCallback } from 'react';
import { parentAPI, scheduleAPI } from '../../utils/api';
import PopupNotification from '../PopupNotification/PopupNotification';
import styles from './ParentDashboard.module.css';

function ParentDashboard({ userInfo, onLogout }) {
  const [childInfo, setChildInfo] = useState(null);
  const [comments, setComments] = useState([]);
  const [medicalCertificates, setMedicalCertificates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [showRefundForm, setShowRefundForm] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    date_from: '',
    date_to: '',
    note: '',
    certificate_file: null
  });
  const [refundForm, setRefundForm] = useState({
    date_from: '',
    date_to: '',
    absence_reason: '',
    certificate_file: null
  });
  const [paymentData, setPaymentData] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [scheduleNotifications, setScheduleNotifications] = useState([]);
  const [showPopupNotifications, setShowPopupNotifications] = useState(true);

  const months = [
    'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
  ];

  const loadParentData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Загружаем данные параллельно
      const [childResponse, commentsResponse, certificatesResponse, paymentResponse] = await Promise.all([
        parentAPI.getChildInfo(),
        parentAPI.getComments(),
        parentAPI.getMedicalCertificates(),
        parentAPI.getPaymentCalculation()
      ]);

      if (childResponse && childResponse.success) {
        setChildInfo(childResponse.child);
      }

      if (commentsResponse && commentsResponse.success) {
        setComments(commentsResponse.comments);
      }

      if (certificatesResponse) {
        setMedicalCertificates(certificatesResponse);
      }

      if (paymentResponse) {
        setPaymentData(paymentResponse);
      }

    } catch (err) {
      console.error('Ошибка загрузки данных родителя:', err);
      setError('Ошибка загрузки данных. Попробуйте обновить страницу.');
    } finally {
      setLoading(false);
    }
  };


  const loadSchedule = useCallback(async () => {
    try {
      const response = await scheduleAPI.getSchedule();
      if (response && Array.isArray(response)) {
        // Фильтруем расписание для группы ребенка
        if (childInfo && childInfo.group) {
          const groupName = typeof childInfo.group === 'object' ? childInfo.group.name : childInfo.group;
          const childSchedule = response.filter(training => 
            training.group && training.group.name === groupName
          );
          setSchedule(childSchedule);
        } else {
          setSchedule(response);
        }
      }
    } catch (err) {
      console.error('Ошибка загрузки расписания:', err);
    }
  }, [childInfo]);

  // Загрузка уведомлений об изменениях расписания
  const loadScheduleNotifications = useCallback(async () => {
    try {
      const response = await scheduleAPI.getNotifications();
      setScheduleNotifications(response.notifications || []);
    } catch (err) {
      console.error('Ошибка загрузки уведомлений о расписании:', err);
    }
  }, []);

  const handleNotificationMarkAsRead = (notificationId) => {
    setScheduleNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
    );
  };

  const handleClosePopupNotifications = () => {
    setShowPopupNotifications(false);
  };

  useEffect(() => {
    loadParentData();
    loadScheduleNotifications();
  }, [loadScheduleNotifications]);

  useEffect(() => {
    if (childInfo) {
      loadSchedule();
    }
  }, [childInfo, loadSchedule]);


  // Остальные функции (handleUploadSubmit, handleRefundSubmit, etc.) остаются без изменений
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    
    // Валидация дат
    if (new Date(uploadForm.date_to) < new Date(uploadForm.date_from)) {
      setError('Дата окончания не может быть раньше даты начала');
      return;
    }
    
    const daysDiff = Math.ceil((new Date(uploadForm.date_to) - new Date(uploadForm.date_from)) / (1000 * 60 * 60 * 24));
    if (daysDiff > 365) {
      setError('Период отсутствия не может превышать 365 дней');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('date_from', uploadForm.date_from);
      formData.append('date_to', uploadForm.date_to);
      formData.append('note', uploadForm.note);
      if (uploadForm.certificate_file) {
        formData.append('certificate_file', uploadForm.certificate_file);
      }
      
      const response = await parentAPI.uploadMedicalCertificate(formData);
      
      if (response.success) {
        setUploadForm({
          date_from: '',
          date_to: '',
          note: '',
          certificate_file: null
        });
        setShowUploadForm(false);
        
        // Обновляем данные
        const [certificatesResponse, paymentResponse] = await Promise.all([
          parentAPI.getMedicalCertificates(),
          parentAPI.getPaymentCalculation()
        ]);
        
        if (certificatesResponse) {
          setMedicalCertificates(certificatesResponse);
        }
        
        if (paymentResponse) {
          setPaymentData(paymentResponse);
        }
      } else {
        setError(response.error || 'Ошибка загрузки справки');
      }
    } catch (err) {
      console.error('Ошибка при загрузке справки:', err);
      setError('Ошибка при загрузке справки');
    } finally {
      setLoading(false);
    }
  };

  const handleRefundSubmit = async (e) => {
    e.preventDefault();
    
    // Валидация дат
    if (new Date(refundForm.date_to) < new Date(refundForm.date_from)) {
      setError('Дата окончания не может быть раньше даты начала');
      return;
    }
    
    const daysDiff = Math.ceil((new Date(refundForm.date_to) - new Date(refundForm.date_from)) / (1000 * 60 * 60 * 24));
    if (daysDiff > 365) {
      setError('Период отсутствия не может превышать 365 дней');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('date_from', refundForm.date_from);
      formData.append('date_to', refundForm.date_to);
      formData.append('absence_reason', refundForm.absence_reason);
      if (refundForm.certificate_file) {
        formData.append('certificate_file', refundForm.certificate_file);
      }
      
      const response = await parentAPI.uploadMedicalCertificate(formData);
      
      if (response.success) {
        setRefundForm({
          date_from: '',
          date_to: '',
          absence_reason: '',
          certificate_file: null
        });
        setShowRefundForm(false);
        
        // Обновляем данные
        const [certificatesResponse, paymentResponse] = await Promise.all([
          parentAPI.getMedicalCertificates(),
          parentAPI.getPaymentCalculation()
        ]);
        
        if (certificatesResponse) {
          setMedicalCertificates(certificatesResponse);
        }
        
        if (paymentResponse) {
          setPaymentData(paymentResponse);
        }
      } else {
        setError(response.error || 'Ошибка отправки запроса на перерасчет');
      }
    } catch (err) {
      console.error('Ошибка при отправке запроса:', err);
      setError('Ошибка при отправке запроса на перерасчет');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
  };

  // Определяем статус тренировки для календаря
  const getTrainingStatus = (training) => {
    const today = new Date();
    const trainingDate = new Date(training.date.split('.').reverse().join('-'));
    
    if (trainingDate > today) {
      return styles.upcoming; // Предстоящие
    }
    
    // Для прошедших тренировок проверяем посещаемость
    // Пока что используем случайную логику для демонстрации
    const dayOfMonth = trainingDate.getDate();
    if (dayOfMonth % 3 === 0) {
      return styles.missed; // Пропущенные (каждый 3-й день)
    } else {
      return styles.attended; // Посещенные
    }
  };

  const handleRefresh = () => {
    loadParentData();
    if (childInfo) {
      loadSchedule();
    }
  };

  if (loading && !childInfo) {
    return (
      <div className={styles.parentDashboard}>
        <div className={styles.main}>
          <div className={styles.loading}>
            Загрузка данных...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.parentDashboard}>
      {/* Всплывающие уведомления */}
      {showPopupNotifications && (
        <PopupNotification
          notifications={scheduleNotifications}
          onMarkAsRead={handleNotificationMarkAsRead}
          onClose={handleClosePopupNotifications}
        />
      )}
      <div className={styles.header}>
        <div className={styles.userInfo}>
          <span>Добро пожаловать, {userInfo.username}!</span>
          <span>Роль: {userInfo.role_display || userInfo.role}</span>
        </div>
        <button className={styles.logoutButton} onClick={onLogout}>
          Выйти
        </button>
      </div>

      <div className={styles.main}>
      <h1>Кабинет родителя</h1>

        {/* Убираем табы - оставляем только главную страницу */}

        {error && (
          <div className={styles.error}>
            {error}
            <button className={styles.refreshButton} onClick={handleRefresh}>
              Обновить
            </button>
          </div>
        )}

        {/* Основной контент */}
        <div className={styles.dashboardGrid}>
            {/* Информация о ребенке */}
            <div className={styles.card}>
              <h3>Информация о ребенке</h3>
              {childInfo ? (
                <div className={styles.childInfo}>
                  <div className={styles.infoItem}>
                    <span className={styles.infoLabel}>Имя:</span>
                    <span className={styles.infoValue}>{childInfo.full_name}</span>
                  </div>
                  <div className={styles.infoItem}>
                    <span className={styles.infoLabel}>Дата рождения:</span>
                    <span className={styles.infoValue}>
                      {formatDate(childInfo.birth_date)}
                    </span>
                  </div>
                  <div className={styles.infoItem}>
                    <span className={styles.infoLabel}>Группа:</span>
                    <span className={styles.infoValue}>
                      {childInfo.group ? (typeof childInfo.group === 'object' ? childInfo.group.name : childInfo.group) : 'Не указана'}
                    </span>
                  </div>
                  <div className={styles.infoItem}>
                    <span className={styles.infoLabel}>Детский сад:</span>
                    <span className={styles.infoValue}>
                      {childInfo.group && typeof childInfo.group === 'object' ? `№${childInfo.group.kindergarten_number}` : 'Не указан'}
                    </span>
                  </div>
                </div>
              ) : (
                <div className={styles.noData}>
                  Информация о ребенке недоступна
                </div>
              )}
            </div>


            {/* Календарь тренировок */}
            <div className={styles.card}>
              <h3>Календарь тренировок</h3>
              <div className={styles.calendarLegend}>
                <div className={styles.legendItem}>
                  <div className={`${styles.legendColor} ${styles.upcoming}`}></div>
                  <span>Предстоящие</span>
                </div>
                <div className={styles.legendItem}>
                  <div className={`${styles.legendColor} ${styles.attended}`}></div>
                  <span>Посещенные</span>
                </div>
                <div className={styles.legendItem}>
                  <div className={`${styles.legendColor} ${styles.missed}`}></div>
                  <span>Пропущенные</span>
                </div>
              </div>
              <div className={styles.trainingCalendar}>
                {schedule.length > 0 ? (
                  <div className={styles.calendarGrid}>
                    {schedule.slice(0, 10).map((training, index) => (
                      <div key={index} className={`${styles.calendarDay} ${getTrainingStatus(training)}`}>
                        <div className={styles.calendarDate}>
                          {new Date(training.date.split('.').reverse().join('-')).getDate()}
                        </div>
                        <div className={styles.calendarTime}>
                          {training.time}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={styles.noData}>
                    Тренировки не запланированы
                  </div>
                )}
              </div>
            </div>

            {/* Предварительная сумма к оплате */}
            {paymentData && (
              <div className={styles.card}>
                <div className={styles.paymentCalculation}>
                  <h3>Сумма к оплате за {months[paymentData.month - 1]} {paymentData.year}</h3>
                  <div className={styles.paymentInfo}>
                    <div>Всего тренировок: {paymentData.total_trainings}</div>
                    <div>Посещено: {paymentData.attended_trainings}</div>
                    <div>Пропущено: {paymentData.missed_trainings}</div>
                    <div>С уважительной причиной: {paymentData.excused_absences}</div>
                    <div>Без уважительной причины: {paymentData.unexcused_absences}</div>
                    <div>Стоимость занятия: {paymentData.cost_per_lesson} ₽</div>
                    <div className={styles.totalAmount}>К оплате: {paymentData.amount_to_pay} ₽</div>
                  </div>
                </div>
              </div>
            )}

            {/* Справки и перерасчет */}
            <div className={styles.card}>
              <h3>Справки и перерасчет</h3>
              
              <div className={styles.certificateActions}>
                <button 
                  className={styles.uploadButton}
                  onClick={() => setShowUploadForm(!showUploadForm)}
                >
                  {showUploadForm ? 'Отмена' : 'Загрузить справку о болезни'}
                </button>
                
                <button 
                  className={styles.refundButton}
                  onClick={() => setShowRefundForm(!showRefundForm)}
                >
                  {showRefundForm ? 'Отмена' : 'Запрос на перерасчет'}
                </button>
              </div>

              {showUploadForm && (
                <form onSubmit={handleUploadSubmit} className={styles.uploadForm}>
                  <h4>Загрузка справки о болезни</h4>
                  
                  <div className={styles.formGroup}>
                    <label>Дата начала болезни:</label>
                    <input
                      type="date"
                      value={uploadForm.date_from}
                      onChange={(e) => setUploadForm({...uploadForm, date_from: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Дата окончания болезни:</label>
                    <input
                      type="date"
                      value={uploadForm.date_to}
                      onChange={(e) => setUploadForm({...uploadForm, date_to: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Примечание:</label>
                    <textarea
                      value={uploadForm.note}
                      onChange={(e) => setUploadForm({...uploadForm, note: e.target.value})}
                      placeholder="Дополнительная информация"
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Файл справки:</label>
                    <input
                      type="file"
                      onChange={(e) => setUploadForm({...uploadForm, certificate_file: e.target.files[0]})}
                      accept=".pdf,.jpg,.jpeg,.png"
                    />
                  </div>
                  
                  <button type="submit" className={styles.submitButton} disabled={loading}>
                    {loading ? 'Загрузка...' : 'Загрузить справку'}
                  </button>
                </form>
              )}

              {showRefundForm && (
                <form onSubmit={handleRefundSubmit} className={styles.uploadForm}>
                  <h4>Запрос на перерасчет</h4>
                  
                  <div className={styles.formGroup}>
                    <label>Дата начала отсутствия:</label>
                    <input
                      type="date"
                      value={refundForm.date_from}
                      onChange={(e) => setRefundForm({...refundForm, date_from: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Дата окончания отсутствия:</label>
                    <input
                      type="date"
                      value={refundForm.date_to}
                      onChange={(e) => setRefundForm({...refundForm, date_to: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Причина отсутствия для перерасчета:</label>
                    <textarea
                      value={refundForm.absence_reason}
                      onChange={(e) => setRefundForm({...refundForm, absence_reason: e.target.value})}
                      placeholder="Опишите причину отсутствия"
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Файл справки (необязательно):</label>
                    <input
                      type="file"
                      onChange={(e) => setRefundForm({...refundForm, certificate_file: e.target.files[0]})}
                      accept=".pdf,.jpg,.jpeg,.png"
                    />
                  </div>
                  
                  <button type="submit" className={styles.submitButton} disabled={loading}>
                    {loading ? 'Отправка...' : 'Отправить запрос'}
                  </button>
                </form>
              )}

              {medicalCertificates && medicalCertificates.length > 0 ? (
                <div className={styles.certificatesList}>
                  <h4>Загруженные справки:</h4>
                  {medicalCertificates.map((cert, index) => (
                    <div key={index} className={styles.certificateItem}>
                      <div className={styles.certificateHeader}>
                        <div className={styles.certificateDate}>
                          {formatDate(cert.date_from)} - {formatDate(cert.date_to)}
                        </div>
                        <div className={`${styles.certificateStatus} ${styles[cert.status]}`}>
                          {cert.status_display}
                        </div>
                      </div>
                      <div className={styles.certificateDetails}>
                        {cert.note && (
                          <div className={styles.certificateNote}>
                            <strong>Примечание:</strong> {cert.note}
                          </div>
                        )}
                        {cert.absence_reason && (
                          <div className={styles.certificateReason}>
                            <strong>Причина отсутствия:</strong> {cert.absence_reason}
                          </div>
                        )}
                        <div className={styles.certificateUploadDate}>
                          Загружено: {cert.uploaded_at}
                        </div>
                        {cert.file_name && (
                          <div className={styles.certificateFile}>
                            <a href={cert.file_url} target="_blank" rel="noopener noreferrer">
                              📄 {cert.file_name}
                            </a>
                          </div>
                        )}
                        {cert.admin_comment && (
                          <div className={styles.certificateComment}>
                            <strong>Комментарий администратора:</strong> {cert.admin_comment}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.noData}>
                  Справки о болезни не загружены
                </div>
              )}
            </div>

            {/* Комментарии от тренера - на всю ширину внизу */}
            <div className={`${styles.card} ${styles.fullWidth}`}>
              <h3>Комментарии от тренера</h3>
              {comments && comments.length > 0 ? (
                <div className={styles.commentsList}>
                  {comments.map((comment, index) => (
                    <div key={index} className={styles.commentItem}>
                      <div className={styles.commentDate}>
                        {formatDate(comment.date)}
                      </div>
                      <div className={styles.commentText}>
                        {comment.text}
                      </div>
                      <div className={styles.commentAuthor}>
                        От: {comment.trainer_name}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.noData}>
                  Комментариев от тренера пока нет
                </div>
              )}
            </div>
          </div>
      </div>
    </div>
  );
}

export default ParentDashboard; 
