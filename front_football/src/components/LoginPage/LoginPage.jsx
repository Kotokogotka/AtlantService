import React, { useState } from 'react';
import { login } from '../../utils/auth';
import styles from './LoginPage.module.css';

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      console.log('DEBUG: Начинаем процесс входа');
      const userInfo = await login(username, password);
      console.log('DEBUG: Получили информацию о пользователе:', userInfo);
      onLogin(userInfo);
      console.log('DEBUG: Вызвали onLogin');
    } catch (err) {
      console.error('DEBUG: Ошибка входа:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.formContainer}>
        <div className={styles.logoWrap}>
          <span className={styles.ball}>⚽</span>
          <span className={styles.title}>Футбольная Академия</span>
        </div>
        <h2 className={styles.subtitle}>Вход в систему</h2>
        
        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Логин</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              className={styles.input}
              placeholder="Введите логин"
              disabled={isLoading}
            />
          </div>
          <div className={styles.inputGroup}>
            <label className={styles.label}>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className={styles.input}
              placeholder="Введите пароль"
              disabled={isLoading}
            />
          </div>
          {error && <div className={styles.error}>{error}</div>}
          <button 
            type="submit" 
            className={`${styles.button} ${isLoading ? styles.loading : ''}`}
            disabled={isLoading}
          >
            {isLoading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage; 