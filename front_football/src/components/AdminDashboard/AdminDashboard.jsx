import React from 'react';

function AdminDashboard({ userInfo, onLogout }) {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Кабинет администратора</h1>
      <p>Пользователь: {userInfo.username}</p>
      <p>Роль: {userInfo.role_display || userInfo.role}</p>
      <button onClick={onLogout}>Выйти</button>
    </div>
  );
}

export default AdminDashboard; 