import React, { useState, useEffect } from 'react';
import LoginPage from './components/LoginPage/LoginPage';
import AdminDashboard from './components/AdminDashboard/AdminDashboard';
import TrainerDashboard from './components/TrainerDashboard/TrainerDashboard';
import ParentDashboard from './components/ParentDashboard/ParentDashboard';
import { checkAuthStatus } from './utils/auth';

function App() {
  const [userInfo, setUserInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

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
      return <TrainerDashboard userInfo={userInfo} onLogout={() => setUserInfo(null)} />;
    case 'parent':
      return <ParentDashboard userInfo={userInfo} onLogout={() => setUserInfo(null)} />;
    default:
      return <div>Неизвестная роль пользователя</div>;
  }
}

export default App;
