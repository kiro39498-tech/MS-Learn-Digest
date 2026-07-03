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

// ── Axios base URL ────────────────────────────────────────────────────────────
// Configured once in services/api.js — that module throws at load time if
// VITE_API_URL is missing, so we do NOT duplicate the fallback logic here.
// This import triggers the validation immediately on app start.
import './services/api';

// ── Google OAuth validation ───────────────────────────────────────────────────
// Log clearly whether the Google Client ID was provided, without crashing
// (the error state is handled in LandingPage before the button is rendered).
if (import.meta.env.VITE_GOOGLE_CLIENT_ID) {
  console.log('✅ Google OAuth configuration loaded successfully.');
} else {
  console.error(
    '❌ VITE_GOOGLE_CLIENT_ID is not set. ' +
    'Google Sign-In will not work. ' +
    'Add VITE_GOOGLE_CLIENT_ID to your .env file (local) or Vercel environment (production).'
  );
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
