/**
 * TeamInvite — Public page for accepting or declining a team newsletter invitation.
 * Route: /team-invite/:token
 *
 * Can be visited without being logged in.
 * If the user accepts and is not logged in, they are redirected to sign in first,
 * then the accept flow continues with the token preserved in the URL.
 */

import { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import {
  BookOpen, CheckCircle2, XCircle, Loader2, Users, Calendar,
  Tag, AlertTriangle, Mail,
} from 'lucide-react';
import { getInvitePreview, acceptInvitation, declineInvitation } from '../services/api';
import { useAuth } from '../context/AuthContext';
import clsx from 'clsx';

const FREQ_LABEL = {
  daily: 'Daily', weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly',
};

export default function TeamInvite() {
  const { token } = useParams();
  const [searchParams] = useSearchParams();
  const autoDecline = searchParams.get('action') === 'decline';
  const { user, loading: authLoading } = useAuth();

  const [preview, setPreview] = useState(null);
  const [loadingPreview, setLoadingPreview] = useState(true);
  const [previewError, setPreviewError] = useState(null);

  const [acting, setActing] = useState(false);
  const [result, setResult] = useState(null); // 'accepted' | 'declined' | 'error'
  const [resultMessage, setResultMessage] = useState('');

  // Load preview on mount
  useEffect(() => {
    getInvitePreview(token)
      .then((r) => setPreview(r.data))
      .catch((err) => {
        const detail = err.response?.data?.detail;
        setPreviewError(
          typeof detail === 'string' ? detail : 'This invitation is invalid or has expired.',
        );
      })
      .finally(() => setLoadingPreview(false));
  }, [token]);

  // Auto-handle decline from email link
  useEffect(() => {
    if (autoDecline && preview && !acting && !result) {
      handleDecline();
    }
  }, [autoDecline, preview]);

  const handleAccept = async () => {
    if (!user) {
      // Not logged in — redirect to login, then come back
      window.location.href = `/?next=/team-invite/${token}`;
      return;
    }
    setActing(true);
    try {
      await acceptInvitation(token);
      setResult('accepted');
      setResultMessage(`You've joined ${preview?.team_name || 'the team'}! You'll start receiving their newsletter.`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setResult('error');
      setResultMessage(
        typeof detail === 'string' ? detail : 'Something went wrong. Please try again.',
      );
    } finally {
      setActing(false);
    }
  };

  const handleDecline = async () => {
    setActing(true);
    try {
      await declineInvitation(token);
      setResult('declined');
      setResultMessage("You've declined the invitation. You won't receive any emails from this team.");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setResult('error');
      setResultMessage(
        typeof detail === 'string' ? detail : 'Could not process your response.',
      );
    } finally {
      setActing(false);
    }
  };

  // ── Loading state ────────────────────────────────────────────────────────

  if (authLoading || loadingPreview) {
    return (
      <div className="min-h-screen bg-ms-light flex items-center justify-center">
        <Loader2 className="h-10 w-10 text-ms-blue animate-spin" />
      </div>
    );
  }

  // ── Error state ──────────────────────────────────────────────────────────

  if (previewError) {
    return (
      <div className="min-h-screen bg-ms-light flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg max-w-md w-full p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-ms-dark mb-2">Invalid Invitation</h2>
          <p className="text-gray-500 text-sm">{previewError}</p>
          <Link to="/" className="btn-primary inline-flex mt-6">
            Go to MS Learn Digest
          </Link>
        </div>
      </div>
    );
  }

  // ── Result state ─────────────────────────────────────────────────────────

  if (result) {
    const isAccepted = result === 'accepted';
    const isDeclined = result === 'declined';
    const isError = result === 'error';

    return (
      <div className="min-h-screen bg-ms-light flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-lg max-w-md w-full p-8 text-center">
          {isAccepted && <CheckCircle2 className="h-14 w-14 text-green-500 mx-auto mb-4" />}
          {isDeclined && <XCircle className="h-14 w-14 text-gray-400 mx-auto mb-4" />}
          {isError   && <AlertTriangle className="h-14 w-14 text-red-400 mx-auto mb-4" />}

          <h2 className="text-xl font-bold text-ms-dark mb-2">
            {isAccepted ? 'Welcome aboard!' : isDeclined ? 'Invitation Declined' : 'Something went wrong'}
          </h2>
          <p className="text-gray-500 text-sm">{resultMessage}</p>

          {isAccepted && (
            <Link to="/dashboard" className="btn-primary inline-flex mt-6">
              Go to Dashboard
            </Link>
          )}
          {!isAccepted && (
            <Link to="/" className="mt-6 inline-flex text-sm text-ms-blue hover:underline">
              Back to MS Learn Digest
            </Link>
          )}
        </div>
      </div>
    );
  }

  // ── Main invitation view ─────────────────────────────────────────────────

  const expiresAt = preview?.expires_at
    ? new Date(preview.expires_at).toLocaleDateString('en-US', {
        month: 'long', day: 'numeric', year: 'numeric',
      })
    : null;

  return (
    <div className="min-h-screen bg-ms-light flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-lg max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div className="bg-ms-blue px-8 py-6 flex items-center gap-3">
          <BookOpen className="h-8 w-8 text-white shrink-0" />
          <div>
            <h1 className="text-white font-bold text-xl">You're invited!</h1>
            <p className="text-blue-100 text-sm mt-0.5">MS Learn Digest Team Newsletter</p>
          </div>
        </div>

        {/* Body */}
        <div className="px-8 py-6 space-y-5">
          {preview?.invited_by_email && (
            <p className="text-gray-600 text-sm">
              <Mail className="h-4 w-4 inline mr-1.5 text-ms-blue" />
              <strong>{preview.invited_by_email}</strong> invited you to join a team newsletter.
            </p>
          )}

          {/* Team info */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Users className="h-5 w-5 text-ms-blue shrink-0" />
              <div>
                <p className="text-xs text-gray-400">Team</p>
                <p className="font-semibold text-ms-dark">{preview?.team_name}</p>
                {preview?.team_description && (
                  <p className="text-xs text-gray-500 mt-0.5">{preview.team_description}</p>
                )}
              </div>
            </div>

            {preview?.frequency && (
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-ms-blue shrink-0" />
                <div>
                  <p className="text-xs text-gray-400">Delivery frequency</p>
                  <p className="font-semibold text-ms-dark">
                    {FREQ_LABEL[preview.frequency] || preview.frequency}
                  </p>
                </div>
              </div>
            )}

            {preview?.topics?.length > 0 && (
              <div className="flex items-start gap-2">
                <Tag className="h-5 w-5 text-ms-blue shrink-0 mt-0.5" />
                <div>
                  <p className="text-xs text-gray-400 mb-1.5">Topics covered</p>
                  <div className="flex flex-wrap gap-1.5">
                    {preview.topics.map((t) => (
                      <span
                        key={t}
                        className="text-xs bg-blue-100 text-ms-blue px-2 py-0.5 rounded-full font-medium"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {!user && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800">
              <strong>Sign in required</strong> — You'll be redirected to sign in before accepting.
            </div>
          )}

          {expiresAt && (
            <p className="text-xs text-gray-400">
              This invitation expires on {expiresAt}.
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="px-8 pb-8 flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleAccept}
            disabled={acting}
            className={clsx(
              'flex-1 btn-primary flex items-center justify-center',
              acting && 'opacity-60 cursor-not-allowed',
            )}
          >
            {acting
              ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              : <CheckCircle2 className="h-4 w-4 mr-2" />}
            {user ? 'Accept Newsletter' : 'Sign in & Accept'}
          </button>

          <button
            onClick={handleDecline}
            disabled={acting}
            className="flex-1 btn-secondary flex items-center justify-center"
          >
            <XCircle className="h-4 w-4 mr-2 text-gray-400" />
            Decline
          </button>
        </div>
      </div>
    </div>
  );
}
