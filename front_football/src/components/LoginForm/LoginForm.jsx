import React, { useState } from 'react';
import axios from 'axios';
import styles from './LoginForm.module.css';

function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await axios.post('http://localhost:8000/api/login/', {
        username,
        password,
      });
      localStorage.setItem('token', response.data.token);
      if (onLogin) onLogin(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка входа');
    }
  };

  return (
    <div className={styles.bg}>
      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.logoWrap}>
          <span className={styles.ball} role="img" aria-label="soccer-ball">⚽</span>
          <span className={styles.title}>Футбольная Академия</span>
        </div>
        <div className={styles.inputGroup}>
          <label className={styles.label}>Логин</label>
          <input
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            required
            className={styles.input}
            placeholder="Введите логин"
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
          />
        </div>
        {error && <div className={styles.error}>{error}</div>}
        <button type="submit" className={styles.button}>Войти</button>
      </form>
    </div>
  );
}

export default LoginForm;
