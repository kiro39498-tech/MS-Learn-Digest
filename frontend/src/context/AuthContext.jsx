import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getMe } from '../services/api';
import axios from 'axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Restore session from stored token on mount
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        // Attach header for the centralized api client and axios defaults
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        try {
          const response = await getMe();
          setUser(response.data);
        } catch {
          localStorage.removeItem('token');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };
    loadUser();
  }, []);

  const login = useCallback(async (token) => {
    localStorage.setItem('token', token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    try {
      const response = await getMe();
      setUser(response.data);
      // getMe() self-heals is_onboarded on the backend, so the value we receive
      // here is always accurate after that heal has run.
      // Send to onboarding only if the user is genuinely new (no subscriptions yet).
      const userData = response.data;
      const hasSubscriptions = userData.is_onboarded; // healed by server before returning
      const destination = hasSubscriptions ? '/dashboard' : '/onboarding';
      navigate(destination, { replace: true });
    } catch {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      navigate('/', { replace: true });
    }
  }, [navigate]);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    navigate('/', { replace: true });
  }, [navigate]);

  const refreshUser = useCallback(async () => {
    try {
      const response = await getMe();
      setUser(response.data);
      return response.data;
    } catch {
      return null;
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, login, logout, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
