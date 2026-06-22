import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { BookOpen, Zap, Mail, Users, ArrowRight, Check, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { requestEmailLogin } from '../services/api';
import clsx from 'clsx';

const FEATURES = [
  {
    icon: Zap,
    title: 'AI-Enriched Digests',
    desc: 'Groq-powered summaries highlighting business value and key takeaways of new Microsoft Learn modules.',
  },
  {
    icon: BookOpen,
    title: 'Structured Learning Tracks',
    desc: 'Progressive beginner-to-expert learning paths with phases, milestones, and AI-generated lessons delivered to your inbox.',
  },
  {
    icon: Mail,
    title: 'Automated Delivery',
    desc: 'Beautifully formatted HTML emails on your schedule — daily, weekly, or bi-weekly.',
  },
  {
    icon: Users,
    title: 'Team Newsletters',
    desc: 'Create shared digests for your entire organisation and keep teams aligned on Microsoft technology.',
  },
];

export default function LandingPage() {
  const { user, loading } = useAuth();
  const [email, setEmail]       = useState('');
  const [emailSent, setEmailSent] = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError, setEmailError]   = useState('');
  const [showEmailForm, setShowEmailForm] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;

  const handleGoogleLogin = () => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) {
      console.error('VITE_GOOGLE_CLIENT_ID not set');
      return;
    }
    const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
    const scope = encodeURIComponent('openid email profile');
    const url = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}`;
    window.location.href = url;
  };

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setEmailLoading(true);
    setEmailError('');
    try {
      await requestEmailLogin(email.trim().toLowerCase());
      setEmailSent(true);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (err.response?.status === 429) {
        setEmailError('Too many requests. Please wait a few minutes before trying again.');
      } else {
        setEmailError(detail || 'Failed to send login email. Please try again.');
      }
    } finally {
      setEmailLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ms-light">
      {/* Nav */}
      <nav className="border-b border-gray-200 bg-white/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <BookOpen className="h-7 w-7 text-ms-blue" />
              <span className="ml-2 text-lg font-bold text-ms-dark">MS Learn Digest</span>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => setShowEmailForm(true)}
                className="text-sm text-gray-600 hover:text-ms-dark font-medium transition-colors">
                Sign in
              </button>
              <button onClick={handleGoogleLogin}
                className="btn-primary text-sm">
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24">
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-blue-50 text-ms-blue text-xs font-semibold px-3 py-1.5 rounded-full border border-blue-100 mb-6">
            <Zap className="h-3.5 w-3.5" /> AI-Powered Microsoft Learning Platform
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-ms-dark leading-tight mb-6">
            Transform Microsoft Learn<br/>
            <span className="text-ms-blue">into your personal coach</span>
          </h1>
          <p className="text-lg text-gray-500 mb-10 max-w-2xl mx-auto">
            AI-curated digests, structured learning tracks from beginner to expert,
            and personalised email delivery — all in one platform.
          </p>

          {/* Auth box */}
          <div className="max-w-sm mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
            {!showEmailForm && !emailSent && (
              <>
                <button
                  onClick={handleGoogleLogin}
                  className="w-full flex items-center justify-center gap-3 border border-gray-300 rounded-xl px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all mb-4"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </button>

                <div className="relative mb-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="px-3 bg-white text-xs text-gray-400 font-medium">or</span>
                  </div>
                </div>

                <button
                  onClick={() => setShowEmailForm(true)}
                  className="w-full flex items-center justify-center gap-2 bg-ms-blue hover:bg-blue-700 text-white rounded-xl px-4 py-3 text-sm font-semibold transition-colors"
                >
                  <Mail className="h-4 w-4" />
                  Continue with Email
                </button>

                <p className="text-xs text-gray-400 text-center mt-4">
                  No password needed. We'll email you a secure sign-in link.
                </p>
              </>
            )}

            {showEmailForm && !emailSent && (
              <form onSubmit={handleEmailSubmit}>
                <h3 className="text-base font-bold text-ms-dark mb-1 text-center">Sign in with Email</h3>
                <p className="text-xs text-gray-400 text-center mb-4">
                  We'll send a secure link to your inbox.
                </p>
                <input
                  type="email"
                  required
                  placeholder="you@company.com"
                  value={email}
                  onChange={e => { setEmail(e.target.value); setEmailError(''); }}
                  className="input w-full mb-3"
                  autoFocus
                />
                {emailError && (
                  <p className="text-xs text-red-500 mb-3 text-center">{emailError}</p>
                )}
                <button
                  type="submit"
                  disabled={emailLoading || !email.trim()}
                  className="w-full btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {emailLoading
                    ? <><Loader2 className="h-4 w-4 animate-spin" />Sending…</>
                    : <><ArrowRight className="h-4 w-4" />Send Login Link</>}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowEmailForm(false); setEmailError(''); }}
                  className="w-full text-xs text-gray-400 hover:text-gray-600 mt-3 transition-colors"
                >
                  ← Back to sign-in options
                </button>
              </form>
            )}

            {emailSent && (
              <div className="text-center">
                <div className="flex justify-center mb-3">
                  <div className="bg-green-100 rounded-full p-3">
                    <Check className="h-8 w-8 text-green-600" />
                  </div>
                </div>
                <h3 className="font-bold text-ms-dark mb-2">Check your inbox</h3>
                <p className="text-sm text-gray-500 mb-4">
                  We sent a sign-in link to <strong>{email}</strong>.
                  It expires in 15 minutes.
                </p>
                <button
                  onClick={() => { setEmailSent(false); setShowEmailForm(false); setEmail(''); }}
                  className="text-xs text-ms-blue hover:underline"
                >
                  Use a different email
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="bg-white border-t border-gray-100 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-center text-ms-dark mb-10">
            Everything you need to stay ahead
          </h2>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title}
                className="p-6 rounded-2xl border border-gray-100 hover:border-ms-blue hover:shadow-sm transition-all">
                <div className="bg-blue-50 rounded-xl p-2.5 w-fit mb-4">
                  <Icon className="h-5 w-5 text-ms-blue" />
                </div>
                <h3 className="font-semibold text-ms-dark mb-2">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
