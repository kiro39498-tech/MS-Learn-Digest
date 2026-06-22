/**
 * EmailAuthCallback — Handles the magic-link token from the email URL.
 * Route: /auth/email/callback?token=<raw_token>
 *
 * Extracts the token, calls /api/auth/email/verify, then uses the
 * existing login() flow (identical to Google OAuth callback).
 */
import { useEffect, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { verifyEmailToken } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Loader2, XCircle } from 'lucide-react';
import { useState } from 'react';

export default function EmailAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const called = useRef(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const token = searchParams.get('token');
    if (!token) {
      navigate('/', { replace: true });
      return;
    }

    verifyEmailToken(token)
      .then((res) => {
        login(res.data.access_token);
      })
      .catch((err) => {
        const detail = err.response?.data?.detail || 'Invalid or expired login link.';
        setError(detail);
      });
  }, [searchParams, navigate, login]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ms-light px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="bg-red-100 rounded-full p-3">
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
          </div>
          <h2 className="text-xl font-bold text-ms-dark mb-2">Login Link Expired</h2>
          <p className="text-gray-500 text-sm mb-6">{error}</p>
          <Link to="/" replace
            className="btn-primary inline-flex items-center justify-center w-full">
            Back to Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ms-light">
      <div className="text-center">
        <Loader2 className="h-10 w-10 text-ms-blue animate-spin mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-ms-dark">Signing you in…</h2>
        <p className="text-gray-500 mt-2 text-sm">Verifying your login link.</p>
      </div>
    </div>
  );
}
