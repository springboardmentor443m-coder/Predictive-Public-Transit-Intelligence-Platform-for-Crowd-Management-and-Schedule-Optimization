import React, { useState, useEffect } from 'react';
import { LoginPage } from './components/LoginPage';
import { Dashboard } from './components/Dashboard';

export const App: React.FC = () => {
  // Session ఉందో లేదో చెక్ చేసుకుని డైరెక్ట్‌గా స్టేట్ సెట్ చేస్తుంది
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(localStorage.getItem('metroflow_session'));
  });

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('metroflow_session');
    setIsAuthenticated(false);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {isAuthenticated ? (
        <Dashboard onLogout={handleLogout} />
      ) : (
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
};

export default App;