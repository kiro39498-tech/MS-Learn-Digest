/**
 * Learning Center — Browse, subscribe, and track structured learning paths.
 *
 * Completely independent from the Update Digest / News system.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  BookOpen, GraduationCap, Play, Check, ChevronRight,
  BarChart2, Clock, Zap, Loader2, XCircle, Trophy,
  ChevronDown, ChevronUp, BookMarked, Target, AlertTriangle,
  RefreshCw, CheckCircle2,
} from 'lucide-react';
import {
  getLearningTopics, getMyLearningTracks,
  subscribeToLearningTrack, unsubscribeFromLearningTrack,
  updateLearningFrequency, getLearningTopicModules,
} from '../services/api';
import api from '../services/api';
import clsx from 'clsx';

const FREQ_OPTIONS = [
  { value: 'daily',    label: 'Daily',     desc: 'One lesson every day' },
  { value: 'weekly',   label: 'Weekly',    desc: 'One lesson per week' },
  { value: 'biweekly', label: 'Bi-weekly', desc: 'Every two weeks' },
];

const DIFF_COLORS = {
  beginner:     'bg-green-100 text-green-700',
  intermediate: 'bg-yellow-100 text-yellow-700',
  advanced:     'bg-red-100 text-red-700',
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function ProgressBar({ pct, status }) {
  const color = status === 'completed' ? 'bg-green-500' : 'bg-ms-blue';
  return (
    <div className="mt-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{status === 'completed' ? '✅ Completed' : `${pct}% complete`}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx('h-2 rounded-full transition-all duration-500', color)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function FrequencyPicker({ value, onChange, disabled }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {FREQ_OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          disabled={disabled}
          onClick={() => onChange(opt.value)}
          title={opt.desc}
          className={clsx(
            'px-3 py-1.5 rounded-lg border text-xs font-medium transition-all',
            value === opt.value
              ? 'border-ms-blue bg-blue-50 text-ms-blue'
              : 'border-gray-200 text-gray-600 hover:border-gray-300',
            disabled && 'opacity-50 cursor-not-allowed',
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// ── Migration / seed error banner ─────────────────────────────────────────────

function SetupBanner({ onSeed, seeding }) {
  return (
    <div className="card border-2 border-yellow-300 bg-yellow-50">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-6 w-6 text-yellow-600 shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-yellow-800">Learning Engine — Setup Required</h3>
          <p className="text-sm text-yellow-700 mt-1">
            The learning curriculum hasn't been seeded yet. This usually means the database
            migration needs to be applied, or the server just restarted.
          </p>
          <div className="mt-3 space-y-1 text-xs text-yellow-700 font-mono bg-yellow-100 rounded-lg p-3">
            <p># Run inside your backend container:</p>
            <p className="font-bold">alembic upgrade head</p>
          </div>
          <button
            onClick={onSeed}
            disabled={seeding}
            className="mt-4 flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {seeding
              ? <><Loader2 className="h-4 w-4 animate-spin" />Seeding…</>
              : <><RefreshCw className="h-4 w-4" />Seed Curriculum Now</>
            }
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Active track card ─────────────────────────────────────────────────────────

function ActiveTrackCard({ progress, onUnsubscribe, onFrequencyChange }) {
  const [showModules, setShowModules] = useState(false);
  const [modules, setModules] = useState([]);
  const [loadingMods, setLoadingMods] = useState(false);
  const [freq, setFreq] = useState(progress.frequency);
  const [updatingFreq, setUpdatingFreq] = useState(false);

  const handleToggleModules = async () => {
    if (!showModules && modules.length === 0) {
      setLoadingMods(true);
      try {
        const res = await getLearningTopicModules(progress.topic_id);
        setModules(res.data);
      } catch (_) {}
      setLoadingMods(false);
    }
    setShowModules((v) => !v);
  };

  const handleFreqChange = async (newFreq) => {
    setFreq(newFreq);
    setUpdatingFreq(true);
    try {
      await onFrequencyChange(progress.topic_id, newFreq);
    } finally {
      setUpdatingFreq(false);
    }
  };

  return (
    <div className="card border border-gray-200">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{progress.topic_icon || '📚'}</span>
          <div>
            <h3 className="font-semibold text-ms-dark">{progress.topic_name}</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Module {progress.current_module_sequence} of {progress.total_modules}
              &nbsp;·&nbsp;{progress.modules_completed} completed
              &nbsp;·&nbsp;{progress.modules_remaining} remaining
            </p>
          </div>
        </div>
        {progress.status === 'completed' && (
          <Trophy className="h-6 w-6 text-yellow-500 shrink-0" />
        )}
      </div>

      <ProgressBar pct={progress.progress_pct} status={progress.status} />

      {/* Frequency */}
      {progress.status !== 'completed' && (
        <div className="mt-4">
          <p className="text-xs text-gray-500 mb-2 font-medium">Delivery frequency</p>
          <FrequencyPicker value={freq} onChange={handleFreqChange} disabled={updatingFreq} />
        </div>
      )}

      {/* Last sent */}
      {progress.last_sent_at && (
        <p className="text-xs text-gray-400 mt-3">
          Last lesson:{' '}
          {new Date(progress.last_sent_at).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit',
          })}
        </p>
      )}

      {/* Actions */}
      <div className="mt-4 flex items-center gap-3 flex-wrap">
        <button
          onClick={handleToggleModules}
          className="btn-secondary text-xs flex items-center gap-1"
        >
          {loadingMods
            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
            : showModules
              ? <ChevronUp className="h-3.5 w-3.5" />
              : <ChevronDown className="h-3.5 w-3.5" />
          }
          {showModules ? 'Hide' : 'View'} Curriculum
        </button>
        <button
          onClick={() => onUnsubscribe(progress.topic_id)}
          className="text-xs text-red-400 hover:text-red-600 transition-colors"
        >
          Unsubscribe
        </button>
      </div>

      {/* Curriculum module list */}
      {showModules && modules.length > 0 && (
        <div className="mt-4 border-t pt-4 max-h-64 overflow-y-auto">
          <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            Curriculum — {modules.length} modules
          </p>
          <div className="space-y-1">
            {modules.map((mod) => {
              const done    = mod.sequence_number < progress.current_module_sequence;
              const current = mod.sequence_number === progress.current_module_sequence;
              return (
                <div
                  key={mod.id}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm',
                    done    && 'bg-green-50 text-green-700',
                    current && 'bg-blue-50 text-ms-blue font-medium border border-blue-200',
                    !done && !current && 'text-gray-400',
                  )}
                >
                  <span className="text-xs font-mono w-6 shrink-0 text-gray-400">
                    {String(mod.sequence_number).padStart(2, '0')}
                  </span>
                  <span className="flex-1 truncate">{mod.title}</span>
                  {done    && <Check className="h-3.5 w-3.5 text-green-600 shrink-0" />}
                  {current && <Play  className="h-3.5 w-3.5 text-ms-blue shrink-0" />}
                  <span className={clsx(
                    'text-xs px-2 py-0.5 rounded-full shrink-0',
                    DIFF_COLORS[mod.difficulty_level] || 'bg-gray-100 text-gray-500',
                  )}>
                    {mod.difficulty_level}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Browse topic card ─────────────────────────────────────────────────────────

function TopicCard({ topic, onSubscribe }) {
  const [freq, setFreq] = useState('weekly');
  const [subscribing, setSubscribing] = useState(false);
  const [showModules, setShowModules] = useState(false);
  const [modules, setModules] = useState([]);
  const [loadingMods, setLoadingMods] = useState(false);

  const handlePreview = async () => {
    if (!showModules && modules.length === 0) {
      setLoadingMods(true);
      try {
        const res = await getLearningTopicModules(topic.id);
        setModules(res.data);
      } catch (_) {}
      setLoadingMods(false);
    }
    setShowModules((v) => !v);
  };

  const handleSubscribe = async () => {
    setSubscribing(true);
    try {
      await onSubscribe(topic.id, freq);
    } finally {
      setSubscribing(false);
    }
  };

  return (
    <div className="card border border-gray-200 hover:border-ms-blue transition-colors flex flex-col">
      {/* Topic header */}
      <div className="flex items-start gap-3">
        <span className="text-3xl shrink-0">{topic.icon || '📚'}</span>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-ms-dark">{topic.name}</h3>
          {topic.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{topic.description}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
            <span className="flex items-center gap-1">
              <BookMarked className="h-3.5 w-3.5" />
              {topic.total_modules} modules
            </span>
            {topic.estimated_hours && (
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                ~{topic.estimated_hours}h
              </span>
            )}
            {topic.difficulty_range && (
              <span className="flex items-center gap-1">
                <Target className="h-3.5 w-3.5" />
                {topic.difficulty_range}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Curriculum preview */}
      <div className="mt-3">
        <button
          type="button"
          onClick={handlePreview}
          className="text-xs text-ms-blue hover:underline flex items-center gap-1"
        >
          {loadingMods
            ? <Loader2 className="h-3 w-3 animate-spin" />
            : showModules ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
          }
          {showModules ? 'Hide' : 'Preview'} curriculum
        </button>

        {showModules && modules.length > 0 && (
          <div className="mt-2 bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto space-y-1">
            {modules.map((mod) => (
              <div key={mod.id} className="flex items-center gap-2 text-xs text-gray-600">
                <span className="font-mono text-gray-400 w-5 shrink-0">
                  {String(mod.sequence_number).padStart(2, '0')}
                </span>
                <span className="flex-1 truncate">{mod.title}</span>
                <span className={clsx(
                  'px-1.5 py-0.5 rounded text-xs shrink-0',
                  DIFF_COLORS[mod.difficulty_level] || 'bg-gray-100 text-gray-500',
                )}>
                  {mod.difficulty_level.charAt(0).toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Frequency & enroll */}
      <div className="mt-4 pt-4 border-t">
        <p className="text-xs text-gray-500 mb-2 font-medium">Delivery frequency</p>
        <FrequencyPicker value={freq} onChange={setFreq} />
      </div>

      <button
        onClick={handleSubscribe}
        disabled={subscribing}
        className="mt-4 w-full btn-primary flex items-center justify-center gap-2 text-sm disabled:opacity-50"
      >
        {subscribing
          ? <><Loader2 className="h-4 w-4 animate-spin" />Enrolling…</>
          : <><Play className="h-4 w-4" />Start Learning</>
        }
      </button>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function LearningCenter() {
  const [topics, setTopics] = useState([]);
  const [myTracks, setMyTracks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [setupNeeded, setSetupNeeded] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [tab, setTab] = useState('browse');
  const [toast, setToast] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const loadData = useCallback(async () => {
    setLoadError(null);
    try {
      const [topicsRes, myRes] = await Promise.all([
        getLearningTopics().catch(() => ({ data: [] })),
        getMyLearningTracks().catch(() => ({ data: [] })),
      ]);
      const topicList = topicsRes.data || [];
      const trackList = myRes.data || [];
      setTopics(topicList);
      setMyTracks(trackList);

      // If API returned empty topics, check if it's a setup issue
      if (topicList.length === 0) {
        setSetupNeeded(true);
      } else {
        setSetupNeeded(false);
      }
    } catch (err) {
      console.error(err);
      setLoadError('Failed to load learning data. The learning engine may not be set up yet.');
      setSetupNeeded(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await api.post('/api/learning/seed');
      if (res.data.total_topics > 0) {
        showToast(`✅ Seeded ${res.data.total_topics} learning topics!`);
        setSetupNeeded(false);
        await loadData();
      } else {
        showToast('Migration may not be applied yet. Run: alembic upgrade head', 'error');
      }
    } catch (err) {
      showToast(
        err.response?.data?.detail || 'Seed failed. Run alembic upgrade head first.',
        'error',
      );
    } finally {
      setSeeding(false);
    }
  };

  const subscribedIds = new Set(myTracks.map((t) => String(t.topic_id)));
  const availableTopics = topics.filter((t) => !subscribedIds.has(String(t.id)));
  const activeTracks = myTracks.filter((t) => t.status === 'active');
  const completedTracks = myTracks.filter((t) => t.status === 'completed');

  const handleSubscribe = async (topicId, frequency) => {
    try {
      await subscribeToLearningTrack(topicId, frequency);
      showToast('Enrolled! Your first lesson will arrive at the scheduled time.');
      await loadData();
      setTab('active');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to subscribe', 'error');
    }
  };

  const handleUnsubscribe = async (topicId) => {
    if (!window.confirm('Unsubscribe from this learning track? Your progress will be lost.')) return;
    try {
      await unsubscribeFromLearningTrack(topicId);
      showToast('Unsubscribed from learning track.');
      await loadData();
    } catch (err) {
      showToast('Failed to unsubscribe', 'error');
    }
  };

  const handleFrequencyChange = async (topicId, frequency) => {
    try {
      await updateLearningFrequency(topicId, frequency);
      showToast('Delivery frequency updated.');
      await loadData();
    } catch (err) {
      showToast('Failed to update frequency', 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 text-ms-blue animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">

      {/* Toast */}
      {toast && (
        <div className={clsx(
          'fixed top-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-sm font-medium flex items-center gap-2',
          toast.type === 'error' ? 'bg-red-600 text-white' : 'bg-green-600 text-white',
        )}>
          {toast.type === 'error'
            ? <XCircle className="h-4 w-4" />
            : <CheckCircle2 className="h-4 w-4" />
          }
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="bg-ms-blue rounded-xl p-3">
          <GraduationCap className="h-6 w-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-ms-dark">Learning Center</h1>
          <p className="text-gray-500 mt-1">
            Progressive structured learning tracks delivered to your inbox.
            Each track is independent — choose your own pace.
          </p>
        </div>
      </div>

      {/* Setup banner — shown when tables not seeded */}
      {setupNeeded && <SetupBanner onSeed={handleSeed} seeding={seeding} />}

      {/* Stats row — only when data is available */}
      {!setupNeeded && (
        <div className="grid grid-cols-3 gap-4">
          <div className="card text-center">
            <p className="text-3xl font-bold text-ms-blue">{activeTracks.length}</p>
            <p className="text-xs text-gray-500 mt-1">Active Tracks</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold text-green-600">{completedTracks.length}</p>
            <p className="text-xs text-gray-500 mt-1">Completed</p>
          </div>
          <div className="card text-center">
            <p className="text-3xl font-bold text-purple-600">{topics.length}</p>
            <p className="text-xs text-gray-500 mt-1">Topics Available</p>
          </div>
        </div>
      )}

      {/* Only show tabs when data is ready */}
      {!setupNeeded && topics.length > 0 && (
        <>
          {/* Tabs */}
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit">
            {[
              { key: 'browse',    label: 'Browse Topics', count: availableTopics.length },
              { key: 'active',    label: 'My Tracks',     count: activeTracks.length },
              { key: 'completed', label: 'Completed',     count: completedTracks.length },
            ].map(({ key, label, count }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={clsx(
                  'px-4 py-2 rounded-md text-sm font-medium transition-all',
                  tab === key
                    ? 'bg-white text-ms-blue shadow-sm'
                    : 'text-gray-600 hover:text-gray-800',
                )}
              >
                {label}
                {count > 0 && (
                  <span className={clsx(
                    'ml-2 text-xs px-1.5 py-0.5 rounded-full',
                    tab === key ? 'bg-blue-100 text-ms-blue' : 'bg-gray-200 text-gray-500',
                  )}>
                    {count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* ── Browse tab ── */}
          {tab === 'browse' && (
            <div>
              {availableTopics.length === 0 && myTracks.length > 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Trophy className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">You're enrolled in all available tracks!</p>
                  <p className="text-xs mt-1">Check your progress in "My Tracks".</p>
                  <button onClick={() => setTab('active')} className="btn-primary mt-4 text-sm">
                    View My Tracks →
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {availableTopics.map((topic) => (
                    <TopicCard key={topic.id} topic={topic} onSubscribe={handleSubscribe} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── My Tracks tab ── */}
          {tab === 'active' && (
            <div className="space-y-4">
              {activeTracks.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <BookOpen className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">No active learning tracks yet</p>
                  <p className="text-xs mt-1">Browse topics to get started.</p>
                  <button onClick={() => setTab('browse')} className="btn-primary mt-4 text-sm">
                    Browse Topics →
                  </button>
                </div>
              ) : (
                activeTracks.map((track) => (
                  <ActiveTrackCard
                    key={track.topic_id}
                    progress={track}
                    onUnsubscribe={handleUnsubscribe}
                    onFrequencyChange={handleFrequencyChange}
                  />
                ))
              )}
            </div>
          )}

          {/* ── Completed tab ── */}
          {tab === 'completed' && (
            <div className="space-y-4">
              {completedTracks.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <Trophy className="h-10 w-10 mx-auto mb-3 opacity-40" />
                  <p className="font-medium">No completed tracks yet</p>
                  <p className="text-xs mt-1">Keep learning — completions appear here.</p>
                </div>
              ) : (
                completedTracks.map((track) => (
                  <div key={track.topic_id} className="card border border-green-200 bg-green-50">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{track.topic_icon || '📚'}</span>
                      <div className="flex-1">
                        <h3 className="font-semibold text-ms-dark">{track.topic_name}</h3>
                        <p className="text-xs text-green-700 mt-0.5">
                          ✅ Completed {track.total_modules} modules
                          {track.completed_at && (
                            <> · {new Date(track.completed_at).toLocaleDateString('en-US', {
                              month: 'short', day: 'numeric', year: 'numeric',
                            })}</>
                          )}
                        </p>
                      </div>
                      <Trophy className="h-6 w-6 text-yellow-500 shrink-0" />
                    </div>
                    <div className="mt-3 h-2 bg-green-200 rounded-full">
                      <div className="h-2 bg-green-500 rounded-full w-full" />
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}

    </div>
  );
}
