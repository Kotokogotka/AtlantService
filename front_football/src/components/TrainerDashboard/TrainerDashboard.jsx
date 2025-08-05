import React, { useState, useEffect } from 'react';
import { trainerAPI, apiUtils } from '../../utils/api';
import styles from './TrainerDashboard.module.css';

function TrainerDashboard({ userInfo, onLogout }) {
  const [groups, setGroups] = useState([]);
  const [trainerInfo, setTrainerInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [groupDetail, setGroupDetail] = useState(null);

  useEffect(() => {
    // Загружаем группы тренера при монтировании компонента
    loadTrainerGroups();
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



  const formatDate = (dateString) => {
    if (!dateString) return 'Не указана';
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  return (
    <div className={styles.dashboard}>
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
        
        {error && (
          <div className={styles.error}>
            <p>Ошибка: {error}</p>
            <button onClick={loadTrainerGroups}>Повторить</button>
          </div>
        )}
        
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
      </main>
    </div>
  );
}

export default TrainerDashboard; 