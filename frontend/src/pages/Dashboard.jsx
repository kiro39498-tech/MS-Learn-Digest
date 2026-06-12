import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Mail, Clock, ExternalLink, BookOpen, Target, Zap,
  Calendar, Send, Loader2, CheckCircle2, XCircle,
} from 'lucide-react';
import { getDigests, getMyTopics, adminSendMyDigest } from '../services/api';
import clsx from 'clsx';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const FREQ_LABEL = { daily: 'Daily', weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly' };
const STATUS_STYLES = {
  sent:       'bg-green-100 text-green-700',
  generated:  'bg-blue-100 text-blue-700',
  failed:     'bg-red-100 text-red-700',
  no_content: 'bg-gray-100 text-gray-500',
};
const STATUS_LABEL = {
  sent:       'Sent',
  generated:  'Generated',
  failed:     'Failed',
  no_content: 'No Updates',
};

function parseDeliveryTime(dt) {
  if (!dt) return { hour: 8, minute: 0 };
  const parts = String(dt).split(':');
  return { hour: parseInt(parts[0] ?? '8', 10), minute: parseInt(parts[1] ?? '0', 10) };
}

function nextDeliveryLabel(pref) {
  if (!pref) return 'Not configured';
  const { frequency, delivery_day, delivery_time } = pref;
  const { hour, minute } = parseDeliveryTime(delivery_time);
  const m = String(minute).padStart(2, '0');
  const label = `${hour % 12 || 12}:${m} ${hour < 12 ? 'AM' : 'PM'}`;
  if (frequency === 'daily')   return `Daily at ${label}`;
  if (frequency === 'monthly') return `1st of month at ${label}`;
  return `${DAYS[delivery_day] ?? 'Mon'} at ${label}`;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [digests, setDigests] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sendingNow, setSendingNow] = useState(false);
  const [sendResult, setSendResult] = useState(null);

  useEffect(() => {
    if (!user) return;
    Promise.all([getDigests(), getMyTopics()])
      .then(([dRes, tRes]) => {
        setDigests(dRes.data);
        setTopics(tRes.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [user]);

  const handleSendNow = async () => {
    setSendingNow(true);
    setSendResult(null);
    try {
      const res = await adminSendMyDigest();
      const { status, recipient, message } = res.data;

      if (status === 'sent') {
        setSendResult({ success: true, message: `Digest sent to ${recipient}` });
        const dRes = await getDigests();
        setDigests(dRes.data);
      } else if (status === 'no_content') {
        setSendResult({
          success: false,
          message: message || 'No catalog items matched your topics. Run a catalog sync first.',
          link: { to: '/admin/testing', label: '→ Go to Admin Testing' },
        });
      } else {
        setSendResult({ success: false, message: message || 'Digest generation failed.' });
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object'
        ? (detail.message || JSON.stringify(detail))
        : (detail || err.message || 'Failed to send digest');
      setSendResult({ success: false, message: msg });
    } finally {
      setSendingNow(false);
    }
  };

  const pref = user?.preferences;
  const firstName = user?.name?.split(' ')[0] ?? 'Learner';
  const lastSentDigest = digests.find((d) => d.status === 'sent');
  const totalSent = digests.filter((d) => d.status === 'sent').length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ms-dark">Welcome back, {firstName} 👋</h1>
        <p className="text-gray-500 mt-1">Your Microsoft Learn intelligence dashboard.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">

        <div className="card bg-ms-blue text-white col-span-2 sm:col-span-1">
          <p className="text-sm font-medium opacity-80">Next Digest</p>
          <p className="text-lg font-bold mt-1 leading-tight">{nextDeliveryLabel(pref)}</p>
          <p className="text-xs opacity-70 mt-1">{FREQ_LABEL[pref?.frequency] ?? '—'}</p>
          <Calendar className="h-7 w-7 opacity-30 mt-3" />
        </div>

        <div className="card">
          <p className="text-sm font-medium text-gray-500">Last Digest Sent</p>
          <p className="text-sm font-bold text-ms-dark mt-1">
            {lastSentDigest
              ? new Date(lastSentDigest.sent_at || lastSentDigest.created_at)
                  .toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
              : 'None yet'}
          </p>
          <Clock className="h-7 w-7 text-ms-blue opacity-20 mt-3" />
        </div>

        <div className="card">
          <p className="text-sm font-medium text-gray-500">Total Digests Sent</p>
          <p className="text-3xl font-bold text-ms-dark mt-1">{totalSent}</p>
          <Mail className="h-7 w-7 text-ms-blue opacity-20 mt-1" />
        </div>

        <div className="card">
          <p className="text-sm font-medium text-gray-500">Subscribed Topics</p>
          <p className="text-3xl font-bold text-ms-dark mt-1">{topics.length}</p>
          <div className="mt-2 flex flex-wrap gap-1">
            {topics.slice(0, 2).map((t) => (
              <span key={t.id} className="text-xs bg-blue-50 text-ms-blue px-1.5 py-0.5 rounded-full">
                {t.name}
              </span>
            ))}
            {topics.length > 2 && (
              <span className="text-xs text-gray-400">+{topics.length - 2}</span>
            )}
          </div>
        </div>

      </div>

      {/* Send Digest Now */}
      <div className="card border border-dashed border-ms-blue bg-blue-50/40">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h3 className="font-semibold text-ms-dark">Send Digest Now</h3>
            <p className="text-sm text-gray-500 mt-0.5">
              Generate and send your digest immediately — no need to wait for the scheduled time.
            </p>
          </div>
          <button
            onClick={handleSendNow}
            disabled={sendingNow || topics.length === 0}
            className="btn-primary flex items-center shrink-0 disabled:opacity-50"
          >
            {sendingNow
              ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Sending…</>
              : <><Send className="h-4 w-4 mr-2" />Send My Digest</>}
          </button>
        </div>

        {sendResult && (
          <div className={clsx(
            'mt-3 flex items-start gap-2 text-sm rounded-lg px-3 py-2',
            sendResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          )}>
            {sendResult.success
              ? <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
              : <XCircle className="h-4 w-4 shrink-0 mt-0.5" />}
            <div>
              {sendResult.message}
              {sendResult.link && (
                <Link
                  to={sendResult.link.to}
                  className="block mt-1 text-xs underline text-red-700 hover:text-red-900"
                >
                  {sendResult.link.label}
                </Link>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Onboarding nudge */}
      {topics.length === 0 && !loading && (
        <div className="card border-2 border-dashed border-ms-blue bg-blue-50">
          <div className="flex items-start gap-4">
            <div className="bg-ms-blue rounded-lg p-2">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-ms-dark">Complete your setup</h3>
              <p className="text-sm text-gray-600 mt-1">
                Subscribe to Microsoft Learn topics to start receiving personalized digests.
              </p>
              <Link to="/preferences" className="btn-primary inline-flex mt-3 text-sm">
                Set Up Topics →
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Digest history */}
      <div className="card">
        <div className="flex items-center justify-between border-b pb-3 mb-4">
          <h2 className="font-semibold text-lg text-ms-dark">Digest History</h2>
          {digests.length > 5 && (
            <Link to="/history" className="text-sm text-ms-blue hover:underline">View all</Link>
          )}
        </div>

        {loading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3].map((n) => <div key={n} className="h-14 bg-gray-100 rounded-lg" />)}
          </div>
        ) : digests.length === 0 ? (
          <div className="text-center py-10 text-gray-400">
            <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
            <p className="font-medium text-sm">No digests yet</p>
            <p className="text-xs mt-1">Your first digest will arrive at your scheduled time.</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {digests.slice(0, 6).map((digest) => {
              const isNoContent = digest.status === 'no_content';
              return (
                <div
                  key={digest.id}
                  className={clsx(
                    'flex items-center justify-between p-3.5 border rounded-xl transition-colors',
                    isNoContent ? 'bg-gray-50 border-gray-100' : 'hover:border-ms-blue group'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div className={clsx('p-1.5 rounded-lg', isNoContent ? 'bg-gray-100' : 'bg-blue-50')}>
                      <Mail className={clsx('h-4 w-4', isNoContent ? 'text-gray-400' : 'text-ms-blue')} />
                    </div>
                    <div>
                      <p className={clsx('font-medium text-sm line-clamp-1',
                        isNoContent ? 'text-gray-400' : 'text-ms-dark')}>
                        {digest.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(digest.created_at).toLocaleDateString('en-US', {
                          weekday: 'short', month: 'short', day: 'numeric',
                        })}
                        {!isNoContent && <>{' · '}{digest.items?.length ?? 0} items</>}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'text-xs px-2 py-0.5 rounded-full font-medium',
                      STATUS_STYLES[digest.status] ?? 'bg-gray-100 text-gray-500'
                    )}>
                      {STATUS_LABEL[digest.status] ?? digest.status}
                    </span>
                    {!isNoContent && (
                      <Link
                        to={`/digest/${digest.id}`}
                        className="text-gray-300 hover:text-ms-blue opacity-0 group-hover:opacity-100 transition-opacity"
                        title="View digest"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
