import React, { useState, useEffect } from 'react';
import { trainerAPI, apiUtils, scheduleAPI } from '../../utils/api';
import PopupNotification from '../PopupNotification/PopupNotification';
import styles from './TrainerDashboard.module.css';

function TrainerDashboard({ userInfo, onLogout }) {
  const [groups, setGroups] = useState([]);
  const [trainerInfo, setTrainerInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [groupDetail, setGroupDetail] = useState(null);
  const [activeTab, setActiveTab] = useState('groups'); // 'groups', 'schedule', 'comments'
  const [comments, setComments] = useState([]);
  const [children, setChildren] = useState([]);
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [commentForm, setCommentForm] = useState({
    child_id: '',
    comment_text: ''
  });
  const [scheduleNotifications, setScheduleNotifications] = useState([]);
  const [showPopupNotifications, setShowPopupNotifications] = useState(true);
  const [schedule, setSchedule] = useState([]);

  // Загрузка уведомлений об изменениях расписания
  const loadScheduleNotifications = async () => {
    try {
      const response = await scheduleAPI.getNotifications();
      setScheduleNotifications(response.notifications || []);
    } catch (err) {
      console.error('Ошибка загрузки уведомлений о расписании:', err);
    }
  };

  const handleNotificationMarkAsRead = (notificationId) => {
    setScheduleNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
    );
  };

  const handleClosePopupNotifications = () => {
    setShowPopupNotifications(false);
  };

  // Загрузка расписания тренера
  const loadSchedule = async () => {
    try {
      const response = await scheduleAPI.getSchedule();
      // API возвращает массив напрямую, а не объект с полем schedule
      const scheduleData = Array.isArray(response) ? response : [];
      setSchedule(scheduleData);
    } catch (err) {
      console.error('Ошибка загрузки расписания:', err);
    }
  };

  useEffect(() => {
    // Загружаем группы тренера при монтировании компонента
    loadTrainerGroups();
    loadScheduleNotifications();
    loadSchedule();
  }, []);

  const loadTrainerGroups = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await trainerAPI.getGroups();
      
      if (response.success) {
        setGroups(response.groups);
        setTrainerInfo(response.trainer_info);
      } else {
        setError('Не удалось загрузить группы');
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка загрузки групп:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadGroupDetail = async (groupId) => {
    try {
      setError(null);
      
      const response = await trainerAPI.getGroupDetail(groupId);
      
      if (response.success) {
        setGroupDetail(response);
        setSelectedGroup(groupId);
      } else {
        setError('Не удалось загрузить информацию о группе');
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка загрузки информации о группе:', err);
    }
  };

  // Загрузка комментариев
  const loadComments = async () => {
    try {
      setIsLoading(true);
      const response = await trainerAPI.getComments();
      setComments(response.comments || []);
      setChildren(response.children || []);
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка загрузки комментариев:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Создание комментария
  const handleCreateComment = async (e) => {
    e.preventDefault();
    
    if (!commentForm.child_id || !commentForm.comment_text.trim()) {
      setError('Выберите ребенка и введите комментарий');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await trainerAPI.createComment({
        child_id: commentForm.child_id,
        comment_text: commentForm.comment_text.trim()
      });
      
      // Сбрасываем форму
      setCommentForm({
        child_id: '',
        comment_text: ''
      });
      setShowCommentForm(false);
      
      // Обновляем список комментариев
      await loadComments();
      
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
      console.error('Ошибка создания комментария:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // useEffect для загрузки комментариев при переключении на вкладку
  useEffect(() => {
    if (activeTab === 'comments') {
      loadComments();
    }
  }, [activeTab]);

  const formatDate = (dateString) => {
    if (!dateString) return 'Не указана';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  // Группировка расписания по садам и группам
  const groupScheduleByGardenAndGroup = (schedule) => {
    const grouped = {};
    
    schedule.forEach((training) => {
      const gardenName = training.group?.garden?.name || `Детский сад №${training.group?.kindergarten_number || 'Неизвестно'}`;
      const groupName = training.group?.name || 'Без группы';
      
      if (!grouped[gardenName]) {
        grouped[gardenName] = {};
      }
      
      if (!grouped[gardenName][groupName]) {
        grouped[gardenName][groupName] = [];
      }
      
      grouped[gardenName][groupName].push(training);
    });
    
    return grouped;
  };

  const groupedSchedule = groupScheduleByGardenAndGroup(schedule);

  return (
    <div className={styles.dashboard}>
      {/* Всплывающие уведомления */}
      {showPopupNotifications && (
        <PopupNotification
          notifications={scheduleNotifications}
          onMarkAsRead={handleNotificationMarkAsRead}
          onClose={handleClosePopupNotifications}
        />
      )}
      {/* Шапка с информацией о пользователе */}
      <header className={styles.header}>
        <div className={styles.userInfo}>
          <span>👤 {userInfo.username}</span>
          <span>Роль: {userInfo.role_display || userInfo.role}</span>
          {trainerInfo && (
            <>
              <span>Тренер: {trainerInfo.full_name}</span>
              <span>Телефон: {trainerInfo.phone}</span>
            </>
          )}
        </div>
      </header>

      {/* Основной контент */}
      <main className={styles.main}>
        <h1>Кабинет тренера</h1>
        
        {/* Табы */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'groups' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('groups')}
          >
            Группы
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'schedule' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('schedule')}
          >
            📅 Расписание
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'comments' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('comments')}
          >
            Комментарии
          </button>
        </div>
        
        {error && (
          <div className={styles.error}>
            <p>Ошибка: {error}</p>
            <button onClick={loadTrainerGroups}>Повторить</button>
          </div>
        )}
        
        {/* Контент вкладки "Группы" */}
        {activeTab === 'groups' && (
          <>
            {isLoading ? (
              <div className={styles.loading}>Загрузка групп...</div>
            ) : (
              <div className={styles.content}>
            {/* Список групп */}
            <div className={styles.groupsSection}>
              <h2>Мои группы ({groups.length})</h2>
              
              {groups.length > 0 ? (
                <div className={styles.groupsList}>
                  {groups.map(group => (
                    <div 
                      key={group.id} 
                      className={`${styles.groupCard} ${selectedGroup === group.id ? styles.selected : ''}`}
                      onClick={() => loadGroupDetail(group.id)}
                    >
                      <div className={styles.groupHeader}>
                        <h3>{group.name}</h3>
                        <span className={styles.ageLevel}>{group.age_level}</span>
                      </div>
                      <div className={styles.groupInfo}>
                        <p>Детей в группе: {group.children_count}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className={styles.noGroups}>У вас пока нет групп</p>
              )}
            </div>

            {/* Детальная информация о группе */}
            {groupDetail && (
              <div className={styles.groupDetail}>
                <h2>Информация о группе: {groupDetail.group.name}</h2>
                
                <div className={styles.groupStats}>
                  <div className={styles.stat}>
                    <span>Возрастная группа:</span>
                    <span>{groupDetail.group.age_level}</span>
                  </div>
                  <div className={styles.stat}>
                    <span>Количество детей:</span>
                    <span>{groupDetail.children_count}</span>
                  </div>
                </div>

                {/* Список детей */}
                <div className={styles.childrenSection}>
                  <h3>Дети в группе</h3>
                  
                  {groupDetail.children.length > 0 ? (
                    <div className={styles.childrenList}>
                      {groupDetail.children.map(child => (
                                                 <div key={child.id} className={styles.childCard}>
                           <div className={styles.childInfo}>
                             <h4>{child.full_name}</h4>
                             <p>Дата рождения: {formatDate(child.birth_date)}</p>
                             <p>Родитель: {child.parent_name || 'Не указан'}</p>
                             {child.parent_phone && (
                               <p>Телефон: {child.parent_phone}</p>
                             )}
                             <p className={styles.attendanceCount}>
                               Посещено занятий в этом месяце: <strong>{child.attendance_count}</strong>
                             </p>
                           </div>
                         </div>
                      ))}
                    </div>
                  ) : (
                    <p>В группе пока нет детей</p>
                  )}
                </div>
                </div>
              )}
            </div>
            )}
          </>
        )}

        {/* Контент вкладки "Комментарии" */}
        {activeTab === 'comments' && (
          <div className={styles.commentsSection}>
            <div className={styles.commentsHeader}>
              <h2>Комментарии о детях</h2>
              <button 
                className={styles.addCommentButton}
                onClick={() => setShowCommentForm(!showCommentForm)}
              >
                {showCommentForm ? 'Отмена' : 'Добавить комментарий'}
              </button>
            </div>

            {showCommentForm && (
              <form onSubmit={handleCreateComment} className={styles.commentForm}>
                <h3>Новый комментарий</h3>
                
                <div className={styles.formGroup}>
                  <label>Выберите ребенка:</label>
                  <select
                    value={commentForm.child_id}
                    onChange={(e) => setCommentForm({...commentForm, child_id: e.target.value})}
                    required
                  >
                    <option value="">-- Выберите ребенка --</option>
                    {children.map(child => (
                      <option key={child.id} value={child.id}>
                        {child.name} ({child.group})
                      </option>
                    ))}
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <label>Комментарий:</label>
                  <textarea
                    value={commentForm.comment_text}
                    onChange={(e) => setCommentForm({...commentForm, comment_text: e.target.value})}
                    placeholder="Введите комментарий о ребенке..."
                    rows="4"
                    required
                  />
                </div>

                <div className={styles.formActions}>
                  <button type="button" onClick={() => setShowCommentForm(false)}>
                    Отмена
                  </button>
                  <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Сохранение...' : 'Сохранить комментарий'}
                  </button>
                </div>
              </form>
            )}

            {isLoading ? (
              <div className={styles.loading}>Загрузка комментариев...</div>
            ) : (
              <div className={styles.commentsList}>
                {comments.length > 0 ? (
                  comments.map(comment => (
                    <div key={comment.id} className={styles.commentItem}>
                      <div className={styles.commentHeader}>
                        <div className={styles.commentChild}>
                          <strong>{comment.child.name}</strong>
                          <span className={styles.commentGroup}>({comment.child.group})</span>
                        </div>
                        <div className={styles.commentDate}>
                          {comment.created_at}
                        </div>
                      </div>
                      <div className={styles.commentText}>
                        {comment.comment_text}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className={styles.noComments}>
                    Комментариев пока нет. Добавьте первый комментарий!
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Вкладка "Расписание" */}
        {activeTab === 'schedule' && (
          <div className={styles.scheduleSection}>
            <h2>Расписание тренировок</h2>
            
            {Object.keys(groupedSchedule).length === 0 ? (
              <div className={styles.scheduleInfo}>
                <p>У вас пока нет запланированных тренировок</p>
              </div>
            ) : (
              <div className={styles.scheduleContainer}>
                {Object.entries(groupedSchedule).map(([gardenName, groups]) => (
                  <div key={gardenName} className={styles.gardenSection}>
                    <h3 className={styles.gardenTitle}>🏢 {gardenName}</h3>
                    {Object.entries(groups).map(([groupName, trainings]) => (
                      <div key={groupName} className={styles.groupSection}>
                        <h4 className={styles.groupTitle}>👥 {groupName}</h4>
                        <div className={styles.trainingsGrid}>
                          {trainings.map((training) => (
                            <div key={training.id} className={styles.trainingCard}>
                              <div className={styles.trainingDate}>
                                {training.date}
                              </div>
                              <div className={styles.trainingTime}>
                                {training.time}
                              </div>
                              <div className={styles.trainingStatus}>
                                {training.status_code === 'scheduled' ? '📅' : 
                                 training.status_code === 'completed' ? '✅' : 
                                 training.status_code === 'cancelled' ? '❌' : '⏳'}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default TrainerDashboard; 