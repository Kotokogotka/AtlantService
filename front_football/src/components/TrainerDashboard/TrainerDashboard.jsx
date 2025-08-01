import React, { useState, useEffect } from 'react';
import { logout } from '../../utils/auth';
import styles from './TrainerDashboard.module.css';

function TrainerDashboard({ userInfo, onLogout }) {
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Загружаем группы тренера
    loadTrainerGroups();
  }, []);

  const loadTrainerGroups = async () => {
    try {
      // Здесь будет API запрос для получения групп тренера
      // const response = await axios.get('/api/trainer/groups/');
      // setGroups(response.data);
    } catch (err) {
      console.error('Ошибка загрузки групп:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.dashboard}>
      {/* Шапка с информацией о пользователе */}
      <header className={styles.header}>
        <div className={styles.userInfo}>
          <span>👤 {userInfo.username}</span>
          <span>Роль: {userInfo.role_display || userInfo.role}</span>
          <span>Вход: {userInfo.loginTime}</span>
        </div>
        <button onClick={async () => {
          await logout();
          onLogout();
        }} className={styles.logoutButton}>
          Выйти
        </button>
      </header>

      {/* Основной контент */}
      <main className={styles.main}>
        <h1>Кабинет тренера</h1>
        
        {isLoading ? (
          <div>Загрузка групп...</div>
        ) : (
          <div className={styles.groups}>
            <h2>Мои группы</h2>
            {groups.length > 0 ? (
              groups.map(group => (
                <div key={group.id} className={styles.group}>
                  {group.name}
                </div>
              ))
            ) : (
              <p>У вас пока нет групп</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default TrainerDashboard; 