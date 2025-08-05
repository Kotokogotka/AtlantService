import React, { useState, useEffect } from 'react';
import LoginPage from './components/LoginPage/LoginPage';
import AdminDashboard from './components/AdminDashboard/AdminDashboard';
import TrainerDashboard from './components/TrainerDashboard/TrainerDashboard';
import AttendancePage from './components/AttendancePage/AttendancePage';
import ParentDashboard from './components/ParentDashboard/ParentDashboard';
import { checkAuthStatus } from './utils/auth';

function App() {
  const [userInfo, setUserInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [trainerView, setTrainerView] = useState('dashboard'); // 'dashboard' или 'attendance'

  useEffect(() => {
    checkAuthStatus()
      .then(user => setUserInfo(user))
      .catch(err => {
        console.error('Ошибка проверки авторизации:', err);
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #111 60%, #FFD600 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#FFD600',
        fontSize: '24px',
        fontWeight: 'bold'
      }}>
        Загрузка...
      </div>
    );
  }

  // Если пользователь не авторизован - показываем страницу входа
  if (!userInfo) {
    console.log('DEBUG: Пользователь не авторизован, показываем страницу входа');
    return <LoginPage onLogin={(user) => {
      console.log('DEBUG: onLogin вызван с данными:', user);
      setUserInfo(user);
    }} />;
  }

  // Показываем соответствующий кабинет в зависимости от роли
  switch (userInfo.role) {
    case 'admin':
      return <AdminDashboard userInfo={userInfo} onLogout={() => setUserInfo(null)} />;
    case 'trainer':
      // Для тренера показываем навигацию между функциями
      return (
        <div>
                    {/* Навигация для тренера */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(10px)',
            padding: '15px 30px',
            borderBottom: '2px solid #667eea',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', gap: '20px' }}>
              <button
                onClick={() => setTrainerView('dashboard')}
                style={{
                  background: trainerView === 'dashboard' ? '#667eea' : 'transparent',
                  color: trainerView === 'dashboard' ? 'white' : '#667eea',
                  border: '2px solid #667eea',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'all 0.3s ease'
                }}
              >
                📊 Просмотр групп
              </button>
              <button
                onClick={() => setTrainerView('attendance')}
                style={{
                  background: trainerView === 'attendance' ? '#667eea' : 'transparent',
                  color: trainerView === 'attendance' ? 'white' : '#667eea',
                  border: '2px solid #667eea',
                  padding: '10px 20px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  transition: 'all 0.3s ease'
                }}
              >
                ✅ Отметка посещаемости
              </button>
            </div>
            <button
              onClick={() => setUserInfo(null)}
              style={{
                background: 'linear-gradient(135deg, #ff6b6b, #ee5a24)',
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              Выйти
            </button>
          </div>
          
          {/* Контент в зависимости от выбранной функции */}
          {trainerView === 'dashboard' ? (
            <TrainerDashboard userInfo={userInfo} onLogout={() => setUserInfo(null)} />
          ) : (
            <AttendancePage userInfo={userInfo} onLogout={() => setUserInfo(null)} />
          )}
        </div>
      );
    case 'parent':
      return <ParentDashboard userInfo={userInfo} onLogout={() => setUserInfo(null)} />;
    default:
      return <div>Неизвестная роль пользователя</div>;
  }
}

export default App;
