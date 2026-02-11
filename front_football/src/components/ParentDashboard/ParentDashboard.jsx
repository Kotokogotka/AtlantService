import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { parentAPI, scheduleAPI, paymentAPI, cancellationNotificationsAPI } from '../../utils/api';
import PopupNotification from '../PopupNotification/PopupNotification';
import styles from './ParentDashboard.module.css';

function ParentDashboard({ userInfo, onLogout }) {
  const [childrenList, setChildrenList] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState(null);
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
  const [schedule, setSchedule] = useState([]);
  const [scheduleNotifications, setScheduleNotifications] = useState([]);
  const [showPopupNotifications, setShowPopupNotifications] = useState(true);
  const [invoices, setInvoices] = useState([]);
  const [unpaidMonthsCount, setUnpaidMonthsCount] = useState(0);
  const [totalUnpaidAmount, setTotalUnpaidAmount] = useState(0);
  const [globalQRCodeUrl, setGlobalQRCodeUrl] = useState(null);
  const [activeTab, setActiveTab] = useState('main');
  const [cancellationNotifications, setCancellationNotifications] = useState([]);
  const [uploadDateError, setUploadDateError] = useState(false);
  const [refundDateError, setRefundDateError] = useState(false);
  const [uploadingReceiptForId, setUploadingReceiptForId] = useState(null);
  const [receiptError, setReceiptError] = useState(null);
  const [receiptFileForInvoice, setReceiptFileForInvoice] = useState({});

  const commentsHoverMarkReadDone = useRef(false);
  const paymentHoverMarkReadDone = useRef(false);

  const invoicesByChild = useMemo(() => {
    if (!invoices || invoices.length === 0) return [];
    const byChild = {};
    invoices.forEach((inv) => {
      const key = inv.child_id;
      if (!byChild[key]) byChild[key] = { child_id: key, child_name: inv.child_name, invoices: [] };
      byChild[key].invoices.push(inv);
    });
    return Object.entries(byChild).map(([childId, data]) => ({ childId, ...data }));
  }, [invoices]);

  const loadParentData = async (childId = null) => {
    const idToUse = childId ?? selectedChildId;
    try {
      setLoading(true);
      setError(null);

      const childResponse = await parentAPI.getChildInfo();
      if (childResponse && childResponse.success) {
        const children = childResponse.children || (childResponse.child ? [childResponse.child] : []);
        setChildrenList(children);
        const nextSelected = idToUse && children.some(c => c.id === idToUse)
          ? idToUse
          : (childResponse.primary_child_id ?? children[0]?.id);
        setSelectedChildId(nextSelected);
        const selected = children.find(c => c.id === nextSelected) || childResponse.child || children[0];
        setChildInfo(selected || null);
      }

      const [commentsResponse, certificatesResponse] = await Promise.all([
        parentAPI.getComments(idToUse ?? undefined),
        parentAPI.getMedicalCertificates(idToUse ?? undefined)
      ]);

      if (commentsResponse && commentsResponse.success) {
        setComments(commentsResponse.comments || []);
      }
      if (certificatesResponse) {
        const certs = certificatesResponse.certificates ?? certificatesResponse;
        setMedicalCertificates(Array.isArray(certs) ? certs : []);
      }
    } catch (err) {
      console.error('Ошибка загрузки данных родителя:', err);
      setError('Ошибка загрузки данных. Попробуйте обновить страницу.');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка счетов на оплату (по всем детям)
  const loadInvoices = useCallback(async () => {
    try {
      const response = await paymentAPI.getInvoices();
      setInvoices(response.invoices || []);
      setUnpaidMonthsCount(response.unpaid_months_count ?? 0);
      setTotalUnpaidAmount(response.total_unpaid_amount ?? 0);
      setGlobalQRCodeUrl(response.global_qr_code_url || null);
    } catch (err) {
      console.error('Ошибка загрузки счетов:', err);
    }
  }, []);

  const handleUploadReceipt = async (invoiceId) => {
    const file = receiptFileForInvoice[invoiceId];
    if (!file) {
      setReceiptError('Выберите файл чека');
      return;
    }
    setReceiptError(null);
    setUploadingReceiptForId(invoiceId);
    try {
      await paymentAPI.uploadReceipt(invoiceId, file);
      setReceiptFileForInvoice(prev => ({ ...prev, [invoiceId]: null }));
      await loadInvoices();
    } catch (err) {
      setReceiptError(err.error || err.message || 'Ошибка загрузки чека');
    } finally {
      setUploadingReceiptForId(null);
    }
  };

  const selectChild = async (id) => {
    setSelectedChildId(id);
    // Сначала отмечаем комментарии как прочитанные, потом загружаем данные — тогда в getChildInfo придёт уже 0 и точка пропадёт
    await parentAPI.markCommentsRead(id).catch(() => {});
    await loadParentData(id);
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

  // Загрузка уведомлений об отмене тренировок
  const loadCancellationNotifications = useCallback(async () => {
    try {
      const response = await cancellationNotificationsAPI.getNotifications();
      setCancellationNotifications(response.notifications || []);
    } catch (error) {
      console.error('Ошибка при загрузке уведомлений об отмене:', error);
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
    commentsHoverMarkReadDone.current = false;
  }, [selectedChildId]);

  useEffect(() => {
    paymentHoverMarkReadDone.current = false;
  }, [scheduleNotifications]);

  // Снять красную точку при наведении на блок комментариев
  const handleCommentsAreaHover = useCallback(() => {
    if (!selectedChildId || commentsHoverMarkReadDone.current) return;
    commentsHoverMarkReadDone.current = true;
    parentAPI.markCommentsRead(selectedChildId)
      .then(() => {
        setChildrenList(prev => prev.map(c => (c.id === selectedChildId ? { ...c, unread_comments_count: 0 } : c)));
      })
      .catch(() => { commentsHoverMarkReadDone.current = false; });
  }, [selectedChildId]);

  // Снять красную точку при наведении на блок счетов (отметить уведомления расписания как прочитанные)
  const handlePaymentInvoicesHover = useCallback(() => {
    if (paymentHoverMarkReadDone.current) return;
    const unread = (scheduleNotifications || []).filter(n => !n.is_read);
    if (unread.length === 0) return;
    paymentHoverMarkReadDone.current = true;
    Promise.all(unread.map(n => scheduleAPI.markNotificationAsRead(n.id)))
      .then(() => {
        setScheduleNotifications(prev => (prev || []).map(n => ({ ...n, is_read: true })));
      })
      .catch(() => { paymentHoverMarkReadDone.current = false; });
  }, [scheduleNotifications]);
  const getGroupName = (child) => (child?.group && typeof child.group === 'object' ? child.group.name : null) || child?.group || null;
  const getUnreadCountForChild = (child) => {
    if (!child) return 0;
    const groupName = getGroupName(child);
    const scheduleUnread = groupName
      ? (scheduleNotifications || []).filter(n => !n.is_read && n.training?.group_name === groupName).length
      : (scheduleNotifications || []).filter(n => !n.is_read).length;
    const commentsUnread = child.unread_comments_count ?? 0;
    return scheduleUnread + commentsUnread;
  };

  // Общее кол-во непрочитанного (для одного ребёнка — одна точка у «Главная»)
  const totalUnreadCount = childrenList.length === 1 && childrenList[0]
    ? getUnreadCountForChild(childrenList[0])
    : 0;

  const handleOpenMainTab = () => {
    setActiveTab('main');
    if (selectedChildId) {
      parentAPI.markCommentsRead(selectedChildId)
        .then(() => parentAPI.getChildInfo())
        .then((response) => {
          if (response?.success && response?.children?.length) {
            setChildrenList(response.children);
          } else {
            setChildrenList(prev => prev.map(c => (c.id === selectedChildId ? { ...c, unread_comments_count: 0 } : c)));
          }
        })
        .catch(() => {});
    }
  };

  useEffect(() => {
    loadParentData();
    loadScheduleNotifications();
    loadCancellationNotifications();
    loadInvoices();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- initial load only on mount
  }, [loadScheduleNotifications, loadCancellationNotifications, loadInvoices]);

  useEffect(() => {
    if (childInfo) {
      loadSchedule();
    }
  }, [childInfo, loadSchedule]);


  // Остальные функции (handleUploadSubmit, handleRefundSubmit, etc.) остаются без изменений
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploadDateError(false);

    // Валидация дат: дата начала не должна быть больше даты окончания
    if (uploadForm.date_from && uploadForm.date_to && new Date(uploadForm.date_to) < new Date(uploadForm.date_from)) {
      setUploadDateError(true);
      setError('Дата окончания болезни не может быть раньше даты начала. Проверьте поля дат.');
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
      
      const response = await parentAPI.uploadMedicalCertificate(formData, selectedChildId ?? undefined);
      
      if (response.success || response.message) {
        setUploadForm({
          date_from: '',
          date_to: '',
          note: '',
          certificate_file: null
        });
        setShowUploadForm(false);
        
        const certificatesResponse = await parentAPI.getMedicalCertificates(selectedChildId ?? undefined);
        if (certificatesResponse) {
          const certs = certificatesResponse.certificates ?? certificatesResponse;
          setMedicalCertificates(Array.isArray(certs) ? certs : []);
        }
        loadInvoices();
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
    setRefundDateError(false);

    // Валидация дат: дата начала не должна быть больше даты окончания
    if (refundForm.date_from && refundForm.date_to && new Date(refundForm.date_to) < new Date(refundForm.date_from)) {
      setRefundDateError(true);
      setError('Дата окончания отсутствия не может быть раньше даты начала. Проверьте поля дат.');
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
      
      const response = await parentAPI.uploadMedicalCertificate(formData, selectedChildId ?? undefined);
      
      if (response.success || response.message) {
        setRefundForm({
          date_from: '',
          date_to: '',
          absence_reason: '',
          certificate_file: null
        });
        setShowRefundForm(false);
        
        const certificatesResponse = await parentAPI.getMedicalCertificates(selectedChildId ?? undefined);
        if (certificatesResponse) {
          const certs = certificatesResponse.certificates ?? certificatesResponse;
          setMedicalCertificates(Array.isArray(certs) ? certs : []);
        }
        loadInvoices();
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
    if (!dateString) return '';
    const str = String(dateString).trim();
    if (str.includes('.') && /^\d{1,2}\.\d{1,2}\.\d{4}$/.test(str)) {
      const [d, m, y] = str.split('.');
      const date = new Date(parseInt(y, 10), parseInt(m, 10) - 1, parseInt(d, 10));
      return Number.isNaN(date.getTime()) ? str : date.toLocaleDateString('ru-RU');
    }
    const date = new Date(dateString);
    return Number.isNaN(date.getTime()) ? str : date.toLocaleDateString('ru-RU');
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
    loadParentData(selectedChildId ?? undefined);
    if (childInfo) {
      loadSchedule();
    }
  };

  if (loading && !childInfo && childrenList.length === 0) {
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
          notifications={[...scheduleNotifications, ...cancellationNotifications]}
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

        {/* Выбор ребёнка (если несколько) */}
        {childrenList.length > 1 && (
          <div className={styles.childSwitcher}>
            <span className={styles.childSwitcherLabel}>Ребёнок:</span>
            {childrenList.map((c) => {
              const unread = getUnreadCountForChild(c);
              return (
                <button
                  key={c.id}
                  type="button"
                  className={`${styles.childSwitcherButton} ${selectedChildId === c.id ? styles.childSwitcherButtonActive : ''}`}
                  onClick={() => selectChild(c.id)}
                >
                  {c.full_name}
                  {unread > 0 && <span className={styles.childUnreadBadge} aria-label={`Непрочитанных: ${unread}`} />}
                </button>
              );
            })}
          </div>
        )}

        {/* Навигационные табы */}
        <div className={styles.tabs}>
          <button 
            className={`${styles.tab} ${activeTab === 'main' ? styles.activeTab : ''}`}
            onClick={handleOpenMainTab}
          >
            Главная
            {childrenList.length <= 1 && totalUnreadCount > 0 && (
              <span className={styles.tabUnreadBadge} aria-label={`Непрочитанных: ${totalUnreadCount}`} />
            )}
          </button>
          <button 
            className={`${styles.tab} ${activeTab === 'payment' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('payment')}
          >
            Оплата
          </button>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
            <button className={styles.refreshButton} onClick={handleRefresh}>
              Обновить
            </button>
          </div>
        )}

        {/* Основной контент */}
        {activeTab === 'main' && (
        <div className={styles.dashboardGrid}>
            {/* Уведомления: неоплата и решения по справкам */}
            {(() => {
              const hasUnpaid = unpaidMonthsCount > 0;
              const certsForChild = childrenList.length > 1 && selectedChildId
                ? (medicalCertificates || []).filter(c => c.child_id === selectedChildId)
                : (medicalCertificates || []);
              const certsWithDecision = (certsForChild || []).filter(
                c => c.status_code === 'approved' || c.status_code === 'rejected'
              );
              if (!hasUnpaid && certsWithDecision.length === 0) return null;
              return (
                <div className={styles.mainAlerts}>
                  {hasUnpaid && (
                    <div className={styles.alertUnpaid}>
                      <strong>Неоплаченные счета:</strong>{' '}
                      {unpaidMonthsCount} {unpaidMonthsCount === 1 ? 'месяц' : unpaidMonthsCount < 5 ? 'месяца' : 'месяцев'} на сумму {totalUnpaidAmount} ₽.{' '}
                      <button type="button" className={styles.alertLink} onClick={() => setActiveTab('payment')}>
                        Перейти к оплате →
                      </button>
                    </div>
                  )}
                  {certsWithDecision.length > 0 && (
                    <div className={styles.alertCertificates}>
                      <strong>Решение по справкам:</strong>
                      <ul className={styles.alertCertList}>
                        {certsWithDecision.map((cert) => (
                          <li key={cert.id}>
                            <span className={cert.status_code === 'approved' ? styles.certApproved : styles.certRejected}>
                              {cert.status_display ?? cert.status}
                            </span>
                            {' — '}
                            {formatDate(cert.date_from)}–{formatDate(cert.date_to)}
                            {cert.admin_comment && (
                              <span className={styles.alertCertComment}> Комментарий: {cert.admin_comment}</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })()}

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

                  {uploadDateError && (
                    <div className={styles.dateErrorText}>
                      Дата окончания не может быть раньше даты начала. Укажите корректный период.
                    </div>
                  )}
                  
                  <div className={styles.formGroup}>
                    <label>Дата начала болезни:</label>
                    <input
                      type="date"
                      className={uploadDateError ? styles.dateInputError : ''}
                      value={uploadForm.date_from}
                      onChange={(e) => {
                        setUploadForm({...uploadForm, date_from: e.target.value});
                        setUploadDateError(false);
                        setError(null);
                      }}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Дата окончания болезни:</label>
                    <input
                      type="date"
                      className={uploadDateError ? styles.dateInputError : ''}
                      value={uploadForm.date_to}
                      onChange={(e) => {
                        setUploadForm({...uploadForm, date_to: e.target.value});
                        setUploadDateError(false);
                        setError(null);
                      }}
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

                  {refundDateError && (
                    <div className={styles.dateErrorText}>
                      Дата окончания не может быть раньше даты начала. Укажите корректный период.
                    </div>
                  )}
                  
                  <div className={styles.formGroup}>
                    <label>Дата начала отсутствия:</label>
                    <input
                      type="date"
                      className={refundDateError ? styles.dateInputError : ''}
                      value={refundForm.date_from}
                      onChange={(e) => {
                        setRefundForm({...refundForm, date_from: e.target.value});
                        setRefundDateError(false);
                        setError(null);
                      }}
                      required
                    />
                  </div>
                  
                  <div className={styles.formGroup}>
                    <label>Дата окончания отсутствия:</label>
                    <input
                      type="date"
                      className={refundDateError ? styles.dateInputError : ''}
                      value={refundForm.date_to}
                      onChange={(e) => {
                        setRefundForm({...refundForm, date_to: e.target.value});
                        setRefundDateError(false);
                        setError(null);
                      }}
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

              {(() => {
                const filteredCerts = childrenList.length > 1 && selectedChildId
                  ? (medicalCertificates || []).filter(c => c.child_id === selectedChildId)
                  : (medicalCertificates || []);
                return filteredCerts.length > 0 ? (
                <div className={styles.certificatesList}>
                  <h4>Загруженные справки:</h4>
                  {filteredCerts.map((cert, index) => (
                    <div key={cert.id ?? index} className={styles.certificateItem}>
                      <div className={styles.certificateHeader}>
                        {cert.child_name && childrenList.length > 1 && (
                          <div className={styles.certificateChildName}>{cert.child_name}</div>
                        )}
                        <div className={styles.certificateDate}>
                          {formatDate(cert.date_from)} - {formatDate(cert.date_to)}
                        </div>
                        <div className={`${styles.certificateStatus} ${styles[cert.status_code] || styles[cert.status] || ''}`}>
                          {cert.status_display ?? cert.status}
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
              );
              })()}
            </div>

            {/* Комментарии от тренера — при наведении снимаем красную точку по комментариям */}
            <div className={styles.card} onMouseEnter={handleCommentsAreaHover}>
              <h3>Комментарии от тренера</h3>
              {(() => {
                const filteredComments = childrenList.length > 1 && selectedChildId
                  ? (comments || []).filter(c => c.child_id === selectedChildId)
                  : (comments || []);
                return filteredComments.length > 0 ? (
                <div className={styles.commentsList}>
                  {filteredComments.map((comment, index) => (
                    <div key={comment.id ?? index} className={styles.commentItem}>
                      {comment.child_name && childrenList.length > 1 && (
                        <div className={styles.commentChildName}>{comment.child_name}</div>
                      )}
                      <div className={styles.commentDate}>
                        {formatDate(comment.created_at || comment.date)}
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
              );
              })()}
            </div>
          </div>
        )}

        {/* Вкладка оплаты */}
        {activeTab === 'payment' && (
          <div className={styles.paymentContent}>
            {unpaidMonthsCount >= 2 && (
              <div className={styles.overdueWarning}>
                <strong>Внимание:</strong> У вас не оплачены счета за {unpaidMonthsCount} {unpaidMonthsCount === 2 ? 'месяца' : 'месяцев'} на сумму {totalUnpaidAmount} ₽. Пожалуйста, погасите задолженность.
              </div>
            )}
            <div className={styles.card} onMouseEnter={handlePaymentInvoicesHover}>
              <h3>Счета на оплату</h3>
              {receiptError && (
                <div className={styles.receiptError}>{receiptError}</div>
              )}
              {invoicesByChild.length > 0 ? (
                <div className={styles.invoicesByChild}>
                  {invoicesByChild.map(({ childId, child_name, invoices: childInvoices }) => (
                    <div key={childId} className={styles.invoiceChildBlock}>
                      {childrenList.length > 1 && (
                        <div className={styles.invoiceChildBlockTitle}>{child_name}</div>
                      )}
                      {globalQRCodeUrl && (
                        <div className={styles.invoiceQR}>
                          <div className={styles.invoiceQRTitle}>Оплата по QR-коду</div>
                          <img src={globalQRCodeUrl} alt="QR для оплаты" className={styles.invoiceQRImage} />
                          <div className={styles.invoiceQRAmount}>После оплаты загрузите чек по нужному счёту ниже.</div>
                        </div>
                      )}
                      <div className={styles.invoicesList}>
                        {childInvoices.map((invoice) => (
                              <div key={invoice.id} className={styles.invoiceItem}>
                                <div className={styles.invoiceHeader}>
                                  <div className={styles.invoiceMonth}>
                                    {invoice.invoice_month_display}
                                  </div>
                                  <div className={`${styles.invoiceStatus} ${styles[invoice.status]}`}>
                                    {invoice.status_display}
                                  </div>
                                </div>
                                <div className={styles.invoiceDetails}>
                        <div className={styles.invoiceRow}>
                          <span>Всего тренировок:</span>
                          <span>{invoice.total_trainings}</span>
                        </div>
                        
                        <div className={styles.invoiceRow}>
                          <span>Подтвержденные пропуски:</span>
                          <span>{invoice.confirmed_absences}</span>
                        </div>
                        
                        <div className={styles.invoiceRow}>
                          <span>К оплате тренировок:</span>
                          <span>{invoice.billable_trainings}</span>
                        </div>
                        
                        <div className={styles.invoiceRow}>
                          <span>Стоимость за тренировку:</span>
                          <span>{invoice.price_per_training} ₽</span>
                        </div>
                        
                        <div className={`${styles.invoiceRow} ${styles.totalRow}`}>
                          <span>Итого к оплате:</span>
                          <span className={styles.totalAmount}>{invoice.total_amount} ₽</span>
                        </div>
                        
                        <div className={styles.invoiceRow}>
                          <span>Срок оплаты:</span>
                          <span>{new Date(invoice.due_date).toLocaleDateString('ru-RU')}</span>
                        </div>
                        
                        {invoice.paid_at && (
                          <div className={styles.invoiceRow}>
                            <span>Дата оплаты:</span>
                            <span>{new Date(invoice.paid_at).toLocaleDateString('ru-RU')}</span>
                          </div>
                        )}
                        
                        {invoice.notes && (
                          <div className={styles.invoiceNotes}>
                            <strong>Примечания:</strong> {invoice.notes}
                          </div>
                        )}
                        {(invoice.status === 'pending' || invoice.status === 'overdue') && (
                          <div className={styles.invoiceReceipt}>
                            {invoice.receipt_parsed_amount != null && (
                              <div className={invoice.receipt_amount_match ? styles.receiptParsedMatch : styles.receiptParsedMismatch}>
                                По чеку: <strong>{invoice.receipt_parsed_amount} ₽</strong>
                                {invoice.receipt_parsed_bank && ` (${invoice.receipt_parsed_bank})`}
                                {invoice.receipt_amount_match === true
                                  ? ' — сумма совпадает со счётом.'
                                  : invoice.receipt_amount_match === false
                                    ? ' — сумма не совпадает со счётом. Проверьте чек.'
                                    : ''}
                              </div>
                            )}
                            {invoice.receipt_status === 'pending' && (
                              <div className={styles.receiptStatus}>Чек загружен, на проверке</div>
                            )}
                            {invoice.receipt_status === 'rejected' && (
                              <div className={styles.receiptStatusRejected}>Чек отклонён. Загрузите новый.</div>
                            )}
                            {invoice.receipt_status !== 'approved' && (
                              <div className={styles.receiptUpload}>
                                <input
                                  type="file"
                                  accept=".pdf,.jpg,.jpeg,.png"
                                  onChange={(e) => {
                                    const f = e.target.files?.[0];
                                    setReceiptFileForInvoice(prev => ({ ...prev, [invoice.id]: f || null }));
                                    setReceiptError(null);
                                  }}
                                />
                                <button
                                  type="button"
                                  className={styles.uploadReceiptButton}
                                  disabled={uploadingReceiptForId === invoice.id || !receiptFileForInvoice[invoice.id]}
                                  onClick={() => handleUploadReceipt(invoice.id)}
                                >
                                  {uploadingReceiptForId === invoice.id ? 'Загрузка...' : 'Загрузить чек'}
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                                </div>
                              </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.noData}>
                  Счетов на оплату пока нет
                </div>
              )}
            </div>

            <div className={styles.card}>
              <h3>Информация об оплате</h3>
              <div className={styles.paymentInfo}>
                <div className={styles.infoBlock}>
                  <h4>Система оплаты</h4>
                  <p>Мы перешли на систему предоплаты. Счета выставляются с 25 числа каждого месяца на следующий месяц.</p>
                </div>
                
                <div className={styles.infoBlock}>
                  <h4>Расчет стоимости</h4>
                  <ul>
                    <li>Если расписание составлено — оплата по количеству запланированных тренировок</li>
                    <li>Если расписания нет — оплата за 8 тренировок (среднее количество)</li>
                    <li>Подтвержденные пропуски по болезни вычитаются из суммы</li>
                  </ul>
                </div>
                
                <div className={styles.infoBlock}>
                  <h4>Справки о болезни</h4>
                  <p>Для получения перерасчета загрузите справку о болезни в разделе "Главная" → "Справки и перерасчеты".</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ParentDashboard; 
