import { useState } from 'react';
import {
  Mail, Send, FileText, Eye, Settings, CheckCircle2, XCircle,
  Loader2, AlertTriangle, ExternalLink, Bug, RefreshCw, Database,
  Users, UserPlus, Copy, Play, ChevronDown, ChevronUp, RotateCcw,
  GraduationCap, BookOpen, Trash2,
} from 'lucide-react';
import {
  adminGetConfig, adminSmtpCheck, adminSendTestEmail,
  adminGenerateTestDigest, adminSendTestDigest, adminPreviewDigest,
  adminDebugOnboarding, adminCatalogSync, adminCatalogCacheStats,
  adminSendMyDigest, adminRepairTopics,
  adminLearningStatus, adminSendLearningLesson, adminClearLessonCache,
  adminTeamCreate, adminTeamInvite, adminTeamAcceptInvite,
  adminTeamRejectInvite, adminTeamSendDigest, adminTeamDeliveryStatus,
} from '../services/api';
import clsx from 'clsx';

const S = { idle: 'idle', loading: 'loading', success: 'success', error: 'error' };

function ResultCard({ status, result }) {
  if (status === S.loading) {
    return (
      <div className="flex items-center gap-2 text-gray-500 text-sm mt-3">
        <Loader2 className="h-4 w-4 animate-spin" /> Processing…
      </div>
    );
  }
  if (status === S.success) {
    return (
      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-start gap-2">
          <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
          <pre className="text-xs text-green-700 whitespace-pre-wrap overflow-x-auto flex-1">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    );
  }
  if (status === S.error) {
    return (
      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-start gap-2">
          <XCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <pre className="text-xs text-red-700 whitespace-pre-wrap overflow-x-auto flex-1">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    );
  }
  return null;
}

function SectionCard({ icon: Icon, title, color = 'blue', children, collapsible = false }) {
  const [open, setOpen] = useState(true);
  const colors = {
    blue:   'border-blue-200 bg-blue-50',
    purple: 'border-purple-200 bg-purple-50',
    green:  'border-green-200 bg-green-50',
    yellow: 'border-yellow-200 bg-yellow-50',
    teal:   'border-teal-200 bg-teal-50',
  };
  const iconColors = {
    blue: 'text-ms-blue', purple: 'text-purple-700',
    green: 'text-green-700', yellow: 'text-yellow-700', teal: 'text-teal-700',
  };
  return (
    <div className={clsx('card border-2', colors[color])}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={clsx('h-5 w-5', iconColors[color])} />
          <h2 className="text-lg font-semibold text-ms-dark">{title}</h2>
        </div>
        {collapsible && (
          <button onClick={() => setOpen(o => !o)} className="text-gray-400">
            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        )}
      </div>
      {open && children}
    </div>
  );
}

// ── Reusable step block ────────────────────────────────────────────────────────
function Step({ label, children }) {
  return (
    <div className="border rounded-xl p-4 bg-white">
      <h3 className="font-semibold text-sm text-ms-dark mb-3">{label}</h3>
      {children}
    </div>
  );
}

function TopicRepairCard() {
  const [st, setSt] = useState(S.idle);
  const [data, setData] = useState(null);

  const handleRepair = async () => {
    setSt(S.loading); setData(null);
    try {
      const res = await adminRepairTopics();
      setData(res.data); setSt(S.success);
    } catch (err) {
      setData(err.response?.data || { message: err.message }); setSt(S.error);
    }
  };

  return (
    <div>
      <button
        onClick={handleRepair}
        disabled={st === S.loading}
        className={clsx(
          'flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors text-white',
          st === S.loading ? 'bg-yellow-400 cursor-not-allowed' :
          st === S.success ? 'bg-green-600 hover:bg-green-700' :
          'bg-yellow-600 hover:bg-yellow-700'
        )}
      >
        {st === S.loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Repairing…</> :
         st === S.success ? <><CheckCircle2 className="h-4 w-4 mr-2" />Repaired</> :
         <><RotateCcw className="h-4 w-4 mr-2" />Repair Topic Hierarchy</>}
      </button>

      {st === S.success && data && (
        <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm font-semibold text-green-800">{data.message}</p>
          <div className="mt-2 grid grid-cols-3 gap-2">
            {Object.entries(data.by_level || {}).map(([k, v]) => (
              <div key={k} className="bg-white border rounded p-2 text-center">
                <p className="text-xs text-gray-500 capitalize">{k.replace('_', ' ')}</p>
                <p className="text-lg font-bold text-ms-dark">{v}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {st === S.error && <ResultCard status={st} result={data} />}
    </div>
  );
}

// ── Learning Engine Section ────────────────────────────────────────────────────

function LearningEngineSection() {
  const [status, setStatus]       = useState(null);
  const [statusSt, setStatusSt]   = useState(S.idle);
  const [sendSt, setSendSt]       = useState(S.idle);
  const [sendData, setSendData]   = useState(null);

  // Cache-clear state
  const [clearSt, setClearSt]       = useState(S.idle);
  const [clearData, setClearData]   = useState(null);
  // Scope inputs
  const [clearSlug, setClearSlug]   = useState('');
  const [clearSeq, setClearSeq]     = useState('');
  // Confirm guard for "clear all"
  const [confirmAll, setConfirmAll] = useState(false);

  const handleStatus = async () => {
    setStatusSt(S.loading);
    try {
      const res = await adminLearningStatus();
      setStatus(res.data);
      setStatusSt(S.success);
    } catch (err) {
      setStatus(err.response?.data || { message: err.message });
      setStatusSt(S.error);
    }
  };

  const handleSendLesson = async () => {
    setSendSt(S.loading);
    setSendData(null);
    try {
      const res = await adminSendLearningLesson();
      setSendData(res.data);
      setSendSt(S.success);
    } catch (err) {
      setSendData(err.response?.data || { message: err.message });
      setSendSt(S.error);
    }
  };

  const handleClearCache = async (scope) => {
    setClearSt(S.loading);
    setClearData(null);
    setConfirmAll(false);
    try {
      const res = await adminClearLessonCache(scope);
      setClearData(res.data);
      setClearSt(S.success);
      // Refresh status counts so "Cached Lessons" tile updates
      if (statusSt === S.success) {
        const s = await adminLearningStatus();
        setStatus(s.data);
      }
    } catch (err) {
      setClearData(err.response?.data || { message: err.message });
      setClearSt(S.error);
    }
  };

  // Derive what scope the clear button will use based on current inputs
  const clearScope = () => {
    if (clearSlug.trim() && clearSeq.trim() && !isNaN(Number(clearSeq))) {
      return { topic_slug: clearSlug.trim(), module_sequence: Number(clearSeq) };
    }
    if (clearSlug.trim()) {
      return { topic_slug: clearSlug.trim() };
    }
    return {};
  };

  const scopeLabel = () => {
    const s = clearScope();
    if (s.module_sequence != null) return `Module ${s.module_sequence} in "${s.topic_slug}"`;
    if (s.topic_slug) return `All modules in "${s.topic_slug}"`;
    return 'ALL cached lessons';
  };

  const isAllScope = Object.keys(clearScope()).length === 0;

  return (
    <SectionCard icon={GraduationCap} title="Learning Engine" color="purple" collapsible>
      <p className="text-sm text-gray-600 mb-4">
        Test the Structured Learning Tracks engine independently from the digest system.
        Check curriculum status, clear the lesson cache after prompt changes, and
        trigger immediate lesson delivery for your active tracks.
      </p>

      {/* ── Engine Status ── */}
      <div className="border rounded-xl p-4 bg-white mb-3">
        <h3 className="font-semibold text-sm text-ms-dark mb-3">Engine Status</h3>
        <button
          onClick={handleStatus}
          disabled={statusSt === S.loading}
          className="btn-secondary flex items-center text-sm"
        >
          {statusSt === S.loading
            ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            : <Database className="h-4 w-4 mr-2" />}
          Check Learning Engine Status
        </button>

        {statusSt === S.success && status && (
          <div className="mt-3 space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Topics',           val: status.topics,                    warn: !status.topics },
                { label: 'Modules',          val: status.modules,                   warn: !status.modules },
                { label: 'Active Subs',      val: status.active_subscriptions,      warn: false },
                { label: 'Cached Lessons',   val: status.generated_lessons_cached,  warn: false },
              ].map(({ label, val, warn }) => (
                <div key={label} className="bg-gray-50 rounded-lg p-3 border">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className={clsx('text-lg font-bold mt-0.5', warn ? 'text-red-600' : 'text-ms-dark')}>
                    {val ?? '—'}
                  </p>
                </div>
              ))}
            </div>

            {status.topic_breakdown && status.topic_breakdown.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-3 border">
                <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wide">
                  Curriculum Topics
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                  {status.topic_breakdown.map((t) => (
                    <div key={t.slug}
                      className="flex items-center justify-between text-sm py-1 border-b border-gray-100 last:border-0"
                    >
                      <span className="text-ms-dark font-medium">{t.name}</span>
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-mono">
                        {t.slug} · {t.modules} modules
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {statusSt === S.error && <ResultCard status={statusSt} result={status} />}
      </div>

      {/* ── Lesson Cache Management ── */}
      <div className="border-2 border-orange-200 rounded-xl p-4 bg-orange-50 mb-3">
        <div className="flex items-center gap-2 mb-1">
          <Trash2 className="h-4 w-4 text-orange-700" />
          <h3 className="font-semibold text-sm text-orange-900">Clear Lesson Cache</h3>
        </div>
        <p className="text-xs text-orange-700 mb-4 leading-relaxed">
          Cached lessons are generated <strong>once per module</strong> and reused for all users.
          After changing the lesson prompt, clear the cache so the next delivery regenerates
          lessons with the new prompt. Clearing does <em>not</em> affect user progress or subscriptions.
        </p>

        {/* Scope inputs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs font-medium text-orange-800 mb-1">
              Topic Slug <span className="text-orange-500 font-normal">(leave blank to clear ALL)</span>
            </label>
            <input
              className="input text-sm font-mono"
              placeholder="e.g. azure-administrator"
              value={clearSlug}
              onChange={e => { setClearSlug(e.target.value); setConfirmAll(false); setClearData(null); }}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-orange-800 mb-1">
              Module Sequence # <span className="text-orange-500 font-normal">(optional — requires slug)</span>
            </label>
            <input
              className="input text-sm font-mono"
              placeholder="e.g. 31"
              value={clearSeq}
              onChange={e => { setClearSeq(e.target.value); setConfirmAll(false); setClearData(null); }}
              disabled={!clearSlug.trim()}
            />
          </div>
        </div>

        {/* Scope preview pill */}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-orange-700">Scope:</span>
          <span className={clsx(
            'text-xs font-semibold px-2.5 py-1 rounded-full border',
            isAllScope
              ? 'bg-red-100 text-red-700 border-red-300'
              : 'bg-orange-100 text-orange-700 border-orange-300',
          )}>
            {scopeLabel()}
          </span>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2 items-center">
          {/* "Clear All" needs an extra confirm click */}
          {isAllScope && !confirmAll ? (
            <button
              onClick={() => setConfirmAll(true)}
              disabled={clearSt === S.loading}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear ALL Lessons
            </button>
          ) : isAllScope && confirmAll ? (
            <>
              <button
                onClick={() => handleClearCache({})}
                disabled={clearSt === S.loading}
                className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-red-700 hover:bg-red-800 text-white transition-colors disabled:opacity-50 animate-pulse"
              >
                {clearSt === S.loading
                  ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  : <Trash2 className="h-4 w-4 mr-2" />}
                Confirm — Clear ALL
              </button>
              <button
                onClick={() => setConfirmAll(false)}
                className="flex items-center px-3 py-2 rounded-lg text-sm font-medium bg-white border border-gray-300 text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
            </>
          ) : (
            <button
              onClick={() => handleClearCache(clearScope())}
              disabled={clearSt === S.loading}
              className="flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-orange-600 hover:bg-orange-700 text-white transition-colors disabled:opacity-50"
            >
              {clearSt === S.loading
                ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                : <Trash2 className="h-4 w-4 mr-2" />}
              {clearSt === S.loading ? 'Clearing…' : 'Clear Cache'}
            </button>
          )}

          {clearSt !== S.idle && (
            <button
              onClick={() => { setClearSt(S.idle); setClearData(null); setConfirmAll(false); }}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              Reset
            </button>
          )}
        </div>

        {/* Result */}
        {clearSt === S.success && clearData && (
          <div className="mt-3 p-3 bg-white border border-orange-200 rounded-lg">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-green-800">{clearData.message}</p>
                <div className="flex gap-3 mt-1.5 text-xs text-gray-500">
                  <span>Scope: <strong className="text-ms-dark">{clearData.scope}</strong></span>
                  <span>Deleted: <strong className="text-ms-dark">{clearData.deleted_count}</strong></span>
                  {clearData.topic_name && (
                    <span>Topic: <strong className="text-ms-dark">{clearData.topic_name}</strong></span>
                  )}
                  {clearData.module_title && (
                    <span>Module: <strong className="text-ms-dark">{clearData.module_title}</strong></span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        {clearSt === S.error && <ResultCard status={clearSt} result={clearData} />}
      </div>

      {/* ── Send lesson now ── */}
      <div className="border rounded-xl p-4 bg-white">
        <h3 className="font-semibold text-sm text-ms-dark mb-2">
          Send My Next Lesson Now
        </h3>
        <p className="text-xs text-gray-500 mb-3">
          Immediately delivers the next lesson email for all your active learning
          tracks. Go to <strong>Learning Center</strong> to subscribe to a track first.
          Each track sends a separate email.{' '}
          <span className="text-orange-600 font-medium">
            Clear the cache above first if you want to test the new prompt.
          </span>
        </p>
        <button
          onClick={handleSendLesson}
          disabled={sendSt === S.loading}
          className={clsx(
            'flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors text-white',
            sendSt === S.loading ? 'bg-purple-400 cursor-not-allowed' :
            sendSt === S.success ? 'bg-green-600 hover:bg-green-700' :
            'bg-purple-700 hover:bg-purple-800',
          )}
        >
          {sendSt === S.loading
            ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating &amp; Sending…</>
            : sendSt === S.success
            ? <><CheckCircle2 className="h-4 w-4 mr-2" />Lessons Sent</>
            : <><Send className="h-4 w-4 mr-2" />Send My Learning Lessons</>}
        </button>

        {sendSt === S.success && sendData && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
            {sendData.status === 'no_subscriptions' ? (
              <p className="text-sm text-yellow-700">{sendData.message}</p>
            ) : (
              <>
                <p className="text-sm font-semibold text-green-800 mb-2">
                  ✅ {sendData.sent}/{sendData.total} lesson{sendData.total !== 1 ? 's' : ''} sent
                </p>
                {sendData.results && (
                  <div className="space-y-1">
                    {sendData.results.map((r, i) => (
                      <div key={i} className="flex items-center justify-between text-xs">
                        <span className="text-gray-700">
                          {r.topic} — Module {r.module}
                        </span>
                        <span className={clsx(
                          'px-2 py-0.5 rounded-full font-medium',
                          r.status === 'sent'   ? 'bg-green-100 text-green-700' :
                          r.status === 'failed' ? 'bg-red-100 text-red-700' :
                          'bg-yellow-100 text-yellow-700',
                        )}>
                          {r.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
        {sendSt === S.error && <ResultCard status={sendSt} result={sendData} />}
      </div>
    </SectionCard>
  );
}

export default function AdminTesting() {
  const [email, setEmail]       = useState('');
  const [userName, setUserName] = useState('Learner');

  // Generic run helper
  const useAction = () => {
    const [st, setSt]     = useState(S.idle);
    const [data, setData] = useState(null);
    const run = async (fn) => {
      setSt(S.loading); setData(null);
      try {
        const res = await fn();
        setData(res.data); setSt(S.success);
        return res.data;
      } catch (err) {
        setData(err.response?.data || { message: err.message }); setSt(S.error);
        return null;
      }
    };
    return { st, data, run, setSt, setData };
  };

  const config    = useAction();
  const smtp      = useAction();
  const testEmail = useAction();
  const genDigest = useAction();
  const sendDig   = useAction();
  const debug     = useAction();
  const myDigest  = useAction();
  const stats     = useAction();

  // Catalog sync with auto-refresh
  const [syncSt, setSyncSt]   = useState(S.idle);
  const [syncData, setSyncData] = useState(null);
  const handleCatalogSync = async () => {
    setSyncSt(S.loading); setSyncData(null);
    try {
      const res = await adminCatalogSync();
      setSyncData(res.data); setSyncSt(S.success);
      const s = await adminCatalogCacheStats();
      stats.data = s.data; // manual update since useAction is separate
    } catch (err) {
      setSyncData(err.response?.data || { message: err.message }); setSyncSt(S.error);
    }
  };

  // Team testing state
  const [teamId,        setTeamId]        = useState('');
  const [teamName,      setTeamName]      = useState('Test Engineering Team');
  const [inviteEmail,   setInviteEmail]   = useState('');
  const [inviteToken,   setInviteToken]   = useState('');
  const [inviteUrl,     setInviteUrl]     = useState('');
  const [rejectToken,   setRejectToken]   = useState('');

  const teamCreate   = useAction();
  const teamInvite   = useAction();
  const teamAccept   = useAction();
  const teamReject   = useAction();
  const teamDigest   = useAction();
  const teamStatus   = useAction();

  const handleTeamCreate = async () => {
    await teamCreate.run(() => adminTeamCreate(teamName));
    if (teamCreate.st === S.success && teamCreate.data?.team_id) {
      setTeamId(teamCreate.data.team_id);
    }
  };

  // After run, pick up team_id from result
  const handleTeamInvite = async () => {
    await teamInvite.run(() => adminTeamInvite(teamId, inviteEmail));
  };

  const handleTeamAccept = async () => {
    await teamAccept.run(() => adminTeamAcceptInvite(inviteToken));
  };

  const handleTeamDigest = async () => {
    await teamDigest.run(() => adminTeamSendDigest(teamId));
  };

  const handleTeamStatus = async () => {
    await teamStatus.run(() => adminTeamDeliveryStatus(teamId));
  };

  // Extract invite token from teamInvite result
  const invTokenFromResult = teamInvite.data?.invitation_token || '';
  const invUrlFromResult   = teamInvite.data?.invite_url || '';

  return (
    <div className="max-w-4xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="bg-yellow-100 rounded-lg p-2">
          <AlertTriangle className="h-6 w-6 text-yellow-700" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ms-dark">Admin Testing Panel</h1>
          <p className="text-gray-500 text-sm mt-0.5">Verify SMTP, catalog cache, digest pipeline, and team newsletters</p>
        </div>
      </div>

      <div className="card border-2 border-yellow-200 bg-yellow-50 text-sm text-yellow-800">
        <strong>Development only.</strong> Set <code className="bg-yellow-200 px-1 rounded">ADMIN_ENABLED=false</code> in production.
      </div>

      {/* Email / name inputs */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-3">Test Configuration</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Recipient Email *</label>
            <input type="email" className="input" placeholder="your@email.com"
              value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">User Name</label>
            <input type="text" className="input" placeholder="Learner"
              value={userName} onChange={(e) => setUserName(e.target.value)} />
          </div>
        </div>
      </div>

      {/* ── Topic Hierarchy Repair ── */}
      <SectionCard icon={RotateCcw} title="Topic Hierarchy Repair" color="yellow">
        <p className="text-sm text-yellow-800 mb-3">
          Run this once after upgrading to the hierarchical topic system. Re-parents any flat
          topics that are showing up twice in the topic tree.
        </p>
        <TopicRepairCard />
      </SectionCard>

      {/* ── 0. Debug Onboarding ── */}
      <SectionCard icon={Bug} title="0. Debug Onboarding State" color="purple">
        <p className="text-sm text-purple-700 mb-3">
          Inspect your onboarding flag, topic subscriptions, and preferences. Auto-heals
          <code className="bg-purple-200 px-1 rounded mx-1">is_onboarded</code> if subscriptions exist.
        </p>
        <button
          onClick={() => debug.run(() => adminDebugOnboarding())}
          disabled={debug.st === S.loading}
          className={clsx('flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors text-white',
            debug.st === S.success ? 'bg-green-600' : 'bg-purple-700 hover:bg-purple-800')}
        >
          {debug.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
           debug.st === S.success ? <CheckCircle2 className="h-4 w-4 mr-2" /> :
           <Bug className="h-4 w-4 mr-2" />}
          Check Onboarding State
        </button>

        {debug.st === S.success && debug.data && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: 'is_onboarded', val: debug.data.is_onboarded ? '✅ true' : '❌ false', ok: debug.data.is_onboarded },
                { label: 'Subscriptions', val: debug.data.subscription_count, ok: debug.data.subscription_count > 0 },
                { label: 'Preferences', val: debug.data.preferences_exist ? '✅ yes' : '⚠️ no', ok: debug.data.preferences_exist },
                { label: 'Can receive digest', val: debug.data.can_receive_digest ? '✅ yes' : '❌ no', ok: debug.data.can_receive_digest },
                debug.data.preferences && { label: 'Frequency', val: debug.data.preferences.frequency },
                debug.data.preferences && { label: 'Delivery', val: `${debug.data.preferences.delivery_time} (${debug.data.preferences.timezone})` },
              ].filter(Boolean).map(({ label, val, ok }) => (
                <div key={label} className="bg-white rounded-lg p-3 border">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className={clsx('text-sm font-bold mt-0.5', ok === false ? 'text-red-600' : ok === true ? 'text-green-600' : 'text-ms-dark')}>
                    {String(val)}
                  </p>
                </div>
              ))}
            </div>
            {debug.data.subscribed_topics?.length > 0 && (
              <div className="bg-white rounded-lg p-3 border flex flex-wrap gap-1.5">
                {debug.data.subscribed_topics.map((t) => (
                  <span key={t.id} className="text-xs bg-blue-50 text-ms-blue px-2 py-0.5 rounded-full border border-blue-100">{t.name}</span>
                ))}
              </div>
            )}
            <div className={clsx('rounded-lg px-4 py-3 text-sm font-medium border',
              debug.data.can_receive_digest ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200')}>
              {debug.data.verdict}
            </div>
          </div>
        )}
        {debug.st === S.error && <ResultCard status={debug.st} result={debug.data} />}
      </SectionCard>

      {/* ── Catalog Cache ── */}
      <SectionCard icon={Database} title="Catalog Cache" color="blue">
        <p className="text-sm text-gray-600 mb-4">
          The catalog cache stores Microsoft Learn metadata locally.
          The nightly sync runs at <strong>{/* shown from stats */} 2:00 AM UTC</strong> daily.
          Digest generation reads from this cache only — it never triggers a sync.
        </p>

        <div className="flex flex-wrap gap-3 mb-3">
          <button
            onClick={() => stats.run(() => adminCatalogCacheStats())}
            disabled={stats.st === S.loading}
            className="btn-secondary flex items-center text-sm"
          >
            {stats.st === S.loading ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Database className="h-4 w-4 mr-1" />}
            Check Cache Stats
          </button>

          <button
            onClick={handleCatalogSync}
            disabled={syncSt === S.loading}
            className={clsx('flex items-center px-4 py-2 rounded-lg text-sm font-semibold transition-colors text-white',
              syncSt === S.loading ? 'bg-blue-300 cursor-not-allowed' :
              syncSt === S.success ? 'bg-green-600 hover:bg-green-700' :
              'bg-ms-blue hover:bg-blue-700')}
          >
            {syncSt === S.loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Syncing… (1–5 min)</> :
             syncSt === S.success ? <><CheckCircle2 className="h-4 w-4 mr-2" />Sync Complete</> :
             <><RefreshCw className="h-4 w-4 mr-2" />Run Catalog Sync</>}
          </button>
        </div>

        {stats.st === S.success && stats.data && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total Cached', val: stats.data.total_cached?.toLocaleString(), warn: !stats.data.total_cached },
                { label: 'Modules', val: stats.data.modules?.toLocaleString() },
                { label: 'Learning Paths', val: stats.data.learning_paths?.toLocaleString() },
                { label: 'Last Synced', val: stats.data.latest_synced_at ? new Date(stats.data.latest_synced_at).toLocaleString() : 'Never', warn: !stats.data.latest_synced_at },
              ].map(({ label, val, warn }) => (
                <div key={label} className="bg-white rounded-lg p-3 border">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className={clsx('text-sm font-bold mt-0.5', warn ? 'text-red-600' : 'text-ms-dark')}>{val ?? '—'}</p>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { label: 'Last Sync Status', val: stats.data.last_sync_status || '—', ok: stats.data.last_sync_status === 'success' },
                { label: 'Next Scheduled Sync', val: stats.data.next_scheduled_sync || '—' },
                stats.data.last_sync_fetched != null && { label: 'Last Fetched', val: stats.data.last_sync_fetched?.toLocaleString() },
                stats.data.last_sync_upserted != null && { label: 'Last Upserted', val: stats.data.last_sync_upserted?.toLocaleString() },
              ].filter(Boolean).map(({ label, val, ok }) => (
                <div key={label} className="bg-white rounded-lg p-3 border">
                  <p className="text-xs text-gray-500">{label}</p>
                  <p className={clsx('text-sm font-bold mt-0.5',
                    ok === true ? 'text-green-600' : ok === false ? 'text-red-600' : 'text-ms-dark')}>
                    {String(val)}
                  </p>
                </div>
              ))}
            </div>
            {stats.data.sync_needed && (
              <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                <XCircle className="h-4 w-4 shrink-0" />
                Cache is empty — click "Run Catalog Sync" before testing real digests.
              </div>
            )}
          </div>
        )}

        {syncSt === S.success && syncData && (
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: 'Fetched', val: syncData.fetched?.toLocaleString() },
              { label: 'Upserted', val: syncData.upserted?.toLocaleString() },
              { label: 'Total Cached', val: syncData.total_cached?.toLocaleString() },
              { label: 'Duration', val: syncData.duration_seconds != null ? `${syncData.duration_seconds}s` : '—' },
            ].map(({ label, val }) => (
              <div key={label} className="bg-white rounded-lg p-3 border border-green-200">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-lg font-bold text-green-700">{val ?? '—'}</p>
              </div>
            ))}
          </div>
        )}
        {(stats.st === S.error || syncSt === S.error) && (
          <ResultCard status={syncSt === S.error ? syncSt : stats.st} result={syncSt === S.error ? syncData : stats.data} />
        )}
      </SectionCard>

      {/* ── 1. SMTP Config ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Settings className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">1. SMTP Configuration</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">View current SMTP settings (password redacted).</p>
        <button onClick={() => config.run(() => adminGetConfig())} disabled={config.st === S.loading}
          className="btn-secondary flex items-center">
          {config.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Settings className="h-4 w-4 mr-2" />}
          Load Config
        </button>
        <ResultCard status={config.st} result={config.data} />
      </div>

      {/* ── 2. SMTP Connection ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Mail className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">2. Test SMTP Connection</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">Connect, authenticate, disconnect — no email sent.</p>
        <button onClick={() => smtp.run(() => adminSmtpCheck())} disabled={smtp.st === S.loading}
          className={clsx('btn-primary flex items-center', smtp.st === S.success && 'bg-green-600 hover:bg-green-700')}>
          {smtp.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
           smtp.st === S.success ? <CheckCircle2 className="h-4 w-4 mr-2" /> :
           <Mail className="h-4 w-4 mr-2" />}
          Test Connection
        </button>
        <ResultCard status={smtp.st} result={smtp.data} />
      </div>

      {/* ── 3. Send Test Email ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Send className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">3. Send Plain Test Email</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">Sends a simple confirmation email — no digest content.</p>
        <button onClick={() => testEmail.run(() => adminSendTestEmail(email.trim()))}
          disabled={!email.trim() || testEmail.st === S.loading}
          className={clsx('btn-primary flex items-center disabled:opacity-50', testEmail.st === S.success && 'bg-green-600 hover:bg-green-700')}>
          {testEmail.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
           testEmail.st === S.success ? <CheckCircle2 className="h-4 w-4 mr-2" /> :
           <Send className="h-4 w-4 mr-2" />}
          Send Test Email
        </button>
        <ResultCard status={testEmail.st} result={testEmail.data} />
      </div>

      {/* ── 4. Generate Test Digest ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">4. Generate Test Digest</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">Creates a sample digest in the database using hardcoded content.</p>
        <button onClick={() => genDigest.run(() => adminGenerateTestDigest())} disabled={genDigest.st === S.loading}
          className={clsx('btn-primary flex items-center', genDigest.st === S.success && 'bg-green-600 hover:bg-green-700')}>
          {genDigest.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
           genDigest.st === S.success ? <CheckCircle2 className="h-4 w-4 mr-2" /> :
           <FileText className="h-4 w-4 mr-2" />}
          Generate Digest
        </button>
        <ResultCard status={genDigest.st} result={genDigest.data} />
        {genDigest.st === S.success && genDigest.data?.preview_url && (
          <a href={genDigest.data.preview_url} target="_blank" rel="noreferrer"
            className="inline-flex items-center text-sm text-ms-blue hover:underline mt-2">
            <ExternalLink className="h-3.5 w-3.5 mr-1" /> View in Dashboard
          </a>
        )}
      </div>

      {/* ── 5. Preview Digest ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Eye className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">5. Preview Digest HTML</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">Renders the newsletter template in a new tab — nothing saved or sent.</p>
        <button onClick={() => window.open(adminPreviewDigest(), '_blank', 'noopener,noreferrer')}
          className="btn-primary flex items-center">
          <Eye className="h-4 w-4 mr-2" /> Preview in Browser
        </button>
      </div>

      {/* ── 6. Send Full Test Digest ── */}
      <div className="card">
        <div className="flex items-center gap-2 mb-2">
          <Mail className="h-5 w-5 text-ms-blue" />
          <h2 className="text-lg font-semibold">6. Send Full Test Digest</h2>
        </div>
        <p className="text-sm text-gray-600 mb-3">Generates, persists, and delivers a complete newsletter email.</p>
        <button onClick={() => sendDig.run(() => adminSendTestDigest(email.trim(), userName.trim() || 'Learner'))}
          disabled={!email.trim() || sendDig.st === S.loading}
          className={clsx('btn-primary flex items-center disabled:opacity-50', sendDig.st === S.success && 'bg-green-600 hover:bg-green-700')}>
          {sendDig.st === S.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> :
           sendDig.st === S.success ? <CheckCircle2 className="h-4 w-4 mr-2" /> :
           <Mail className="h-4 w-4 mr-2" />}
          Send Full Digest
        </button>
        <ResultCard status={sendDig.st} result={sendDig.data} />
      </div>

      {/* ── 7. Send My Real Digest ── */}
      <SectionCard icon={Send} title="7. Send My Real Digest (Live)" color="green">
        <p className="text-sm text-gray-600 mb-3">
          Generates a real digest from the catalog cache using your subscriptions, calls Groq, and emails you.
          The catalog must be populated first.
        </p>
        <button
          onClick={() => myDigest.run(() => adminSendMyDigest())}
          disabled={myDigest.st === S.loading}
          className={clsx('btn-primary flex items-center',
            myDigest.st === S.success ? 'bg-green-600 hover:bg-green-700' : '')}
        >
          {myDigest.st === S.loading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating…</> :
           myDigest.st === S.success ? <><CheckCircle2 className="h-4 w-4 mr-2" />Sent!</> :
           <><Send className="h-4 w-4 mr-2" />Send My Digest Now</>}
        </button>
        {myDigest.st === S.success && myDigest.data?.status === 'no_content' && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            <AlertTriangle className="h-4 w-4 inline mr-1" />
            {myDigest.data.message}
          </div>
        )}
        {(myDigest.st === S.success && myDigest.data?.status !== 'no_content') && (
          <ResultCard status={myDigest.st} result={myDigest.data} />
        )}
        {myDigest.st === S.error && <ResultCard status={myDigest.st} result={myDigest.data} />}
      </SectionCard>

      {/* ── Team Newsletter Testing ── */}
      <SectionCard icon={Users} title="Team Newsletter Testing" color="teal" collapsible>
        <p className="text-sm text-gray-600 mb-4">
          Full end-to-end test: create team → invite → accept/reject → send digest → view history.
          Work through steps A–J in order.
        </p>

        <div className="space-y-3">

          {/* A. Create Team */}
          <Step label="A. Create Test Team (with newsletter)">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Team Name</label>
                <input className="input" value={teamName}
                  onChange={e => setTeamName(e.target.value)} placeholder="Test Engineering Team" />
              </div>
              <button
                onClick={async () => {
                  const result = await teamCreate.run(() => adminTeamCreate(teamName));
                  if (result?.team_id) setTeamId(result.team_id);
                }}
                disabled={teamCreate.st === S.loading}
                className="btn-primary flex items-center whitespace-nowrap"
              >
                {teamCreate.st === S.loading
                  ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  : <Users className="h-4 w-4 mr-2" />}
                Create Team
              </button>
            </div>
            {teamCreate.st === S.success && teamCreate.data && (
              <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3 text-sm space-y-1">
                <p className="font-semibold text-green-800">✅ Team: <strong>{teamCreate.data.team_name}</strong></p>
                <p className="text-xs text-green-700">
                  Team ID: <code className="bg-green-100 px-1 rounded">{teamCreate.data.team_id}</code>
                </p>
                <p className="text-xs text-green-700">Topics: {teamCreate.data.newsletter_topics?.join(', ') || '—'}</p>
                <p className="text-xs text-green-700">Schedule: {teamCreate.data.schedule || '—'}</p>
              </div>
            )}
            {teamCreate.st === S.error && <ResultCard status={teamCreate.st} result={teamCreate.data} />}
          </Step>

          {/* Team ID input */}
          <div className="border rounded-xl p-4 bg-white">
            <label className="block text-xs text-gray-500 mb-1.5">
              Team ID <span className="text-gray-400">(auto-filled from step A, or paste)</span>
            </label>
            <input className="input font-mono text-sm" value={teamId}
              onChange={e => setTeamId(e.target.value)} placeholder="paste team UUID" />
          </div>

          {/* B. Invite Member */}
          <Step label="B. Invite Member">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Member Email</label>
                <input type="email" className="input" value={inviteEmail}
                  onChange={e => setInviteEmail(e.target.value)} placeholder="member@company.com" />
              </div>
              <button
                onClick={() => teamInvite.run(() => adminTeamInvite(teamId, inviteEmail))}
                disabled={!teamId || !inviteEmail || teamInvite.st === S.loading}
                className="btn-primary flex items-center whitespace-nowrap disabled:opacity-50"
              >
                {teamInvite.st === S.loading
                  ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  : <UserPlus className="h-4 w-4 mr-2" />}
                Send Invite
              </button>
            </div>
            {teamInvite.st === S.success && teamInvite.data && (
              <div className="mt-3 space-y-2">
                <div className={clsx('rounded-lg p-3 text-sm border',
                  teamInvite.data.email_sent
                    ? 'bg-green-50 border-green-200 text-green-800'
                    : 'bg-yellow-50 border-yellow-200 text-yellow-800')}>
                  <p className="font-semibold">
                    {teamInvite.data.email_sent ? '✅' : '⚠️'} Invite sent to {teamInvite.data.email}
                    {' · '}{teamInvite.data.email_sent ? 'Email delivered' : 'Email failed — share link'}
                  </p>
                  <p className="text-xs mt-1">
                    Status: <strong>{teamInvite.data.member_status}</strong>
                    {' · '}Token: <code className="bg-white/60 px-1 rounded">
                      {(teamInvite.data.invitation_token || '').slice(0, 16)}…
                    </code>
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <input readOnly className="input text-xs flex-1 font-mono"
                    value={teamInvite.data.invite_url || ''} />
                  <button className="btn-secondary px-3"
                    onClick={() => navigator.clipboard.writeText(teamInvite.data.invite_url || '')}>
                    <Copy className="h-4 w-4" />
                  </button>
                  <a href={teamInvite.data.invite_url} target="_blank" rel="noreferrer"
                    className="btn-secondary px-3">
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>
            )}
            {teamInvite.st === S.error && <ResultCard status={teamInvite.st} result={teamInvite.data} />}
          </Step>

          {/* Token input (shared by accept / reject) */}
          <div className="border rounded-xl p-4 bg-white">
            <label className="block text-xs text-gray-500 mb-1.5">
              Invitation Token <span className="text-gray-400">(for accept / reject steps)</span>
            </label>
            <input className="input font-mono text-sm" value={inviteToken}
              onChange={e => setInviteToken(e.target.value)}
              placeholder={teamInvite.data?.invitation_token || 'paste token'} />
            {teamInvite.data?.invitation_token && !inviteToken && (
              <button className="text-xs text-ms-blue hover:underline mt-1.5 block"
                onClick={() => setInviteToken(teamInvite.data.invitation_token)}>
                ↑ Use token from step B
              </button>
            )}
          </div>

          {/* C. Accept Invite */}
          <Step label="C. Accept Invitation (simulate)">
            <p className="text-xs text-gray-500 mb-3">
              Accepts the invitation without the invitee needing to sign in (admin bypass for testing).
            </p>
            <button
              onClick={() => teamAccept.run(() =>
                adminTeamAcceptInvite(inviteToken || teamInvite.data?.invitation_token))}
              disabled={(!inviteToken && !teamInvite.data?.invitation_token) || teamAccept.st === S.loading}
              className="btn-primary flex items-center disabled:opacity-50"
            >
              {teamAccept.st === S.loading
                ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Accepting…</>
                : teamAccept.st === S.success
                  ? <><CheckCircle2 className="h-4 w-4 mr-2" />Accepted!</>
                  : <><CheckCircle2 className="h-4 w-4 mr-2" />Accept Invite</>}
            </button>
            <ResultCard status={teamAccept.st} result={teamAccept.data} />
          </Step>

          {/* D. Reject Invite */}
          <Step label="D. Reject Invitation (simulate)">
            <p className="text-xs text-gray-500 mb-3">
              Use a different token (from a separate invite) to test rejection.
            </p>
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">Token to reject</label>
                <input className="input font-mono text-sm" value={rejectToken}
                  onChange={e => setRejectToken(e.target.value)} placeholder="paste token to reject" />
              </div>
              <button
                onClick={() => teamReject.run(() => adminTeamRejectInvite(rejectToken))}
                disabled={!rejectToken || teamReject.st === S.loading}
                className="btn-secondary flex items-center whitespace-nowrap disabled:opacity-50 border-red-200 text-red-600 hover:bg-red-50"
              >
                {teamReject.st === S.loading
                  ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  : <XCircle className="h-4 w-4 mr-2" />}
                Reject Invite
              </button>
            </div>
            <ResultCard status={teamReject.st} result={teamReject.data} />
          </Step>

          {/* E. Generate & Send Team Digest */}
          <Step label="E. Generate & Send Team Digest">
            <p className="text-xs text-gray-500 mb-3">
              Generates ONE digest via Groq and sends to all <strong>accepted</strong> members.
              Catalog must be populated first.
            </p>
            <button
              onClick={() => teamDigest.run(() => adminTeamSendDigest(teamId))}
              disabled={!teamId || teamDigest.st === S.loading}
              className="btn-primary flex items-center disabled:opacity-50"
            >
              {teamDigest.st === S.loading
                ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Generating…</>
                : teamDigest.st === S.success
                  ? <><CheckCircle2 className="h-4 w-4 mr-2" />Sent!</>
                  : <><Play className="h-4 w-4 mr-2" />Generate & Send Digest</>}
            </button>
            {teamDigest.st === S.success && teamDigest.data?.status === 'no_content' && (
              <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                <AlertTriangle className="h-4 w-4 inline mr-1" />
                {teamDigest.data.message}
              </div>
            )}
            {(teamDigest.st === S.success && teamDigest.data?.status !== 'no_content') &&
              <ResultCard status={teamDigest.st} result={teamDigest.data} />}
            {teamDigest.st === S.error && <ResultCard status={teamDigest.st} result={teamDigest.data} />}
          </Step>

          {/* F. Delivery Status */}
          <Step label="F. View Delivery Status & Digest History">
            <button
              onClick={() => teamStatus.run(() => adminTeamDeliveryStatus(teamId))}
              disabled={!teamId || teamStatus.st === S.loading}
              className="btn-secondary flex items-center disabled:opacity-50"
            >
              {teamStatus.st === S.loading
                ? <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                : <Database className="h-4 w-4 mr-2" />}
              View Status
            </button>

            {teamStatus.st === S.success && teamStatus.data && (
              <div className="mt-3 space-y-3">
                {/* Newsletter config */}
                {teamStatus.data.newsletter && (
                  <div className="bg-blue-50 rounded-lg p-3 text-sm">
                    <p className="font-semibold text-ms-dark">{teamStatus.data.newsletter.name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{teamStatus.data.newsletter.schedule}</p>
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {teamStatus.data.newsletter.topics?.map(t => (
                        <span key={t} className="text-xs bg-blue-100 text-ms-blue px-2 py-0.5 rounded-full">{t}</span>
                      ))}
                    </div>
                  </div>
                )}
                {/* Member counts */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[
                    { label: 'Total',    val: teamStatus.data.member_count },
                    { label: 'Accepted', val: teamStatus.data.accepted_count,  ok: teamStatus.data.accepted_count > 0 },
                    { label: 'Pending',  val: teamStatus.data.pending_count },
                    { label: 'Declined', val: teamStatus.data.declined_count ?? 0 },
                    { label: 'Expired',  val: teamStatus.data.expired_count ?? 0 },
                  ].map(({ label, val, ok }) => (
                    <div key={label} className="bg-white rounded-lg p-2.5 border text-center">
                      <p className="text-xs text-gray-400">{label}</p>
                      <p className={clsx('text-lg font-bold',
                        ok === true ? 'text-green-600' : ok === false ? 'text-red-500' : 'text-ms-dark')}>
                        {val ?? 0}
                      </p>
                    </div>
                  ))}
                </div>
                {/* Recent digests */}
                {teamStatus.data.recent_digests?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-2">Recent Digests</p>
                    <div className="space-y-1.5">
                      {teamStatus.data.recent_digests.map(d => (
                        <div key={d.id}
                          className="flex items-center justify-between text-xs bg-gray-50 rounded-lg px-3 py-2">
                          <span className="text-ms-dark font-medium truncate flex-1 mr-2">{d.title}</span>
                          <span className={clsx('px-2 py-0.5 rounded-full font-semibold shrink-0',
                            d.status === 'sent'   ? 'bg-green-100 text-green-700' :
                            d.status === 'failed' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-500')}>
                            {d.status}
                          </span>
                          <span className="ml-2 text-gray-400 shrink-0">{d.recipient_count} sent</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {teamStatus.st === S.error && <ResultCard status={teamStatus.st} result={teamStatus.data} />}
          </Step>

        </div>
      </SectionCard>

      {/* ── Learning Engine Testing ── */}
      <LearningEngineSection />

    </div>
  );
}
