import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import AuthCallback from './pages/AuthCallback';
import EmailAuthCallback from './pages/EmailAuthCallback';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import Preferences from './pages/Preferences';
import Teams from './pages/Teams';
import DigestDetail from './pages/DigestDetail';
import AdminTesting from './pages/AdminTesting';
import TeamInvite from './pages/TeamInvite';
import LearningCenter from './pages/LearningCenter';
import Layout from './components/Layout';
import { AuthProvider } from './context/AuthContext';

// Configure axios base URL
import axios from 'axios';
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

if (import.meta.env.VITE_GOOGLE_CLIENT_ID) {
  console.log('✅ Google OAuth configuration loaded successfully.');
} else {
  console.error('❌ Google OAuth configuration is MISSING (VITE_GOOGLE_CLIENT_ID).');
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/auth/email/callback" element={<EmailAuthCallback />} />

          {/* Team invitation — public, no auth wall */}
          <Route path="/team-invite/:token" element={<TeamInvite />} />

          {/* Onboarding */}
          <Route path="/onboarding" element={<Onboarding />} />

          {/* Protected routes */}
          <Route element={<Layout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/preferences" element={<Preferences />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/digest/:digestId" element={<DigestDetail />} />
            <Route path="/history" element={<Dashboard />} />
            <Route path="/learning" element={<LearningCenter />} />
            <Route path="/admin/testing" element={<AdminTesting />} />
          </Route>
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
