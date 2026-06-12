/**
 * Teams page — one team owns exactly one newsletter configuration.
 *
 * Features:
 *  - Create team (name + description + topics + schedule in one form)
 *  - Edit topics (inline)
 *  - Edit schedule (inline)
 *  - Invite member → sends email
 *  - Resend invitation
 *  - Remove member / cancel pending invite
 *  - Digest history per team
 *  - Delete team
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Users, Mail, Loader2, UserPlus, X, Check, Copy,
  ExternalLink, Trash2, RefreshCw, ChevronDown, ChevronUp,
  Tag, Calendar, RotateCcw, BookOpen, Clock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  getTeams, createTeam, deleteTeam,
  inviteMember, resendInvitation, removeMember,
  updateTeamTopics, updateTeamSchedule, toggleTeamNewsletter,
  getTopics, getTeamDigests,
} from '../services/api';
import clsx from 'clsx';

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const FREQS = ['daily', 'weekly', 'biweekly', 'monthly'];
const TIMES = ['06:00','07:00','08:00','09:00','10:00','11:00','12:00',
               '13:00','14:00','15:00','16:00','17:00','18:00','19:00','20:00'];

const FIXED_TZ = 'Asia/Kolkata'; // never ask users — always IST

const STATUS_PILL = {
  accepted: 'bg-green-100 text-green-700',
  pending:  'bg-yellow-100 text-yellow-700',
  declined: 'bg-red-100 text-red-600',
  expired:  'bg-gray-100 text-gray-400',
  removed:  'bg-gray-100 text-gray-400',
};

const FREQ_LABEL = {
  daily: 'Daily', weekly: 'Weekly', biweekly: 'Bi-weekly', monthly: 'Monthly',
};

const DIGEST_STATUS_PILL = {
  sent:      'bg-green-100 text-green-700',
  generated: 'bg-blue-100 text-blue-700',
  failed:    'bg-red-100 text-red-600',
  no_content:'bg-gray-100 text-gray-500',
};

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function scheduleLabel(nl) {
  if (!nl) return '—';
  const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  const [h, m] = (nl.delivery_time || '09:00').split(':').map(Number);
  const ampm = h < 12 ? 'AM' : 'PM';
  const h12  = h === 0 ? 12 : h > 12 ? h - 12 : h;
  const t    = `${h12}:${String(m).padStart(2,'0')} ${ampm}`;
  if (nl.frequency === 'daily')   return `Daily at ${t} IST`;
  if (nl.frequency === 'monthly') return `Monthly on the 1st at ${t} IST`;
  const day  = days[nl.delivery_day ?? 0];
  const freq = FREQ_LABEL[nl.frequency] || nl.frequency;
  return `${freq} on ${day} at ${t} IST`;
}

// ─────────────────────────────────────────────────────────────────────────────
// Modal: Create Team (one form: name + description + topics + schedule)
// ─────────────────────────────────────────────────────────────────────────────

function CreateTeamModal({ onClose, onCreated }) {
  const [allTopics, setAllTopics] = useState([]);
  const [form, setForm] = useState({
    name: '', description: '',
    topic_ids: [],
    frequency: 'weekly', delivery_day: 0,
    delivery_time: '09:00',
    // timezone is fixed to Asia/Kolkata — not configurable
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getTopics().then(r => setAllTopics(r.data)).catch(() => {});
  }, []);

  const toggleTopic = (id) =>
    setForm(f => ({
      ...f,
      topic_ids: f.topic_ids.includes(id)
        ? f.topic_ids.filter(t => t !== id)
        : [...f.topic_ids, id],
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Team name is required.'); return; }
    if (form.topic_ids.length === 0) { setError('Select at least one topic.'); return; }
    setLoading(true); setError('');
    try {
      const res = await createTeam(form);
      onCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create team.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 my-4">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-ms-dark">Create Team</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400" /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Team Name *</label>
            <input className="input" placeholder="e.g. AI Engineering Team"
              value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea className="input" rows={2} placeholder="Optional"
              value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
          </div>

          {/* Topics */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topics * <span className="text-xs text-gray-400">({form.topic_ids.length} selected)</span>
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-44 overflow-y-auto">
              {allTopics.map(t => {
                const sel = form.topic_ids.includes(t.id);
                return (
                  <button key={t.id} type="button" onClick={() => toggleTopic(t.id)}
                    className={clsx('flex items-center gap-1.5 p-2 rounded-lg border-2 text-left text-sm transition-all',
                      sel ? 'border-ms-blue bg-blue-50' : 'border-gray-200 hover:border-gray-300')}>
                    {sel && <Check className="h-3.5 w-3.5 text-ms-blue shrink-0" />}
                    <span className={sel ? 'text-ms-blue font-medium' : 'text-gray-600'}>{t.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Schedule */}
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              Delivery Schedule <span className="text-xs text-gray-400 font-normal">(Asia/Kolkata IST)</span>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Frequency</label>
                <select className="input" value={form.frequency}
                  onChange={e => setForm({ ...form, frequency: e.target.value })}>
                  {FREQS.map(f => <option key={f} value={f}>{FREQ_LABEL[f]}</option>)}
                </select>
              </div>
              {form.frequency !== 'daily' && form.frequency !== 'monthly' && (
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Day</label>
                  <select className="input" value={form.delivery_day}
                    onChange={e => setForm({ ...form, delivery_day: parseInt(e.target.value) })}>
                    {DAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                  </select>
                </div>
              )}
              {form.frequency === 'monthly' && (
                <div className="flex items-center">
                  <p className="text-xs text-ms-blue bg-blue-50 rounded-lg px-3 py-2 border border-blue-100">
                    Sends on the 1st of every month
                  </p>
                </div>
              )}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Time (IST)</label>
                <select className="input" value={form.delivery_time}
                  onChange={e => setForm({ ...form, delivery_time: e.target.value })}>
                  {TIMES.map(t => {
                    const [h] = t.split(':').map(Number);
                    const ap = h < 12 ? 'AM' : 'PM';
                    const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
                    return <option key={t} value={t}>{h12}:00 {ap}</option>;
                  })}
                </select>
              </div>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex justify-end gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={loading} className="btn-primary flex items-center">
              {loading ? <Loader2 className="animate-spin h-4 w-4 mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              Create Team
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Modal: Edit Topics
// ─────────────────────────────────────────────────────────────────────────────

function EditTopicsModal({ team, onClose, onSaved }) {
  const [allTopics, setAllTopics] = useState([]);
  const currentIds = (team.newsletter?.topics || []).map(t => t.topic_id);
  const [selected, setSelected] = useState(currentIds);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getTopics().then(r => setAllTopics(r.data)).catch(() => {});
  }, []);

  const toggle = (id) =>
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

  const handleSave = async () => {
    if (selected.length === 0) { setError('Select at least one topic.'); return; }
    setLoading(true); setError('');
    try {
      const res = await updateTeamTopics(team.id, selected);
      onSaved(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map(d => d.msg || JSON.stringify(d)).join(', ')
          : (typeof detail === 'string' ? detail : 'Failed to update topics.')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 my-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-ms-dark">Edit Topics</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400" /></button>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Changes take effect on the next scheduled digest.
        </p>
        <div className="grid grid-cols-2 gap-2 max-h-56 overflow-y-auto mb-4">
          {allTopics.map(t => {
            const sel = selected.includes(t.id);
            return (
              <button key={t.id} type="button" onClick={() => toggle(t.id)}
                className={clsx('flex items-center gap-1.5 p-2.5 rounded-lg border-2 text-left text-sm transition-all',
                  sel ? 'border-ms-blue bg-blue-50' : 'border-gray-200 hover:border-gray-300')}>
                {sel && <Check className="h-3.5 w-3.5 text-ms-blue shrink-0" />}
                <span className={sel ? 'text-ms-blue font-medium' : 'text-gray-600'}>{t.name}</span>
              </button>
            );
          })}
        </div>
        <p className="text-xs text-gray-400 mb-4">{selected.length} topic{selected.length !== 1 ? 's' : ''} selected</p>
        {error && <p className="text-sm text-red-600 mb-3">{error}</p>}
        <div className="flex justify-end gap-3">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave} disabled={loading} className="btn-primary flex items-center">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
            Save Topics
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Modal: Edit Schedule
// ─────────────────────────────────────────────────────────────────────────────

function EditScheduleModal({ team, onClose, onSaved }) {
  const nl = team.newsletter;
  const [form, setForm] = useState({
    frequency:     nl?.frequency     || 'weekly',
    delivery_day:  nl?.delivery_day  ?? 0,
    delivery_time: nl?.delivery_time || '09:00',
    // no timezone — always Asia/Kolkata
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    setLoading(true); setError('');
    try {
      const res = await updateTeamSchedule(team.id, form);
      onSaved(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map(d => d.msg || JSON.stringify(d)).join(', ')
          : (typeof detail === 'string' ? detail : 'Failed to update schedule.')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-ms-dark">Edit Schedule</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400" /></button>
        </div>
        <div className="space-y-4">
          {/* Frequency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Frequency</label>
            <div className="grid grid-cols-2 gap-2">
              {FREQS.map(f => (
                <button key={f} type="button" onClick={() => setForm({ ...form, frequency: f })}
                  className={clsx('py-2 rounded-lg border-2 text-sm font-medium capitalize transition-all',
                    form.frequency === f
                      ? 'border-ms-blue bg-blue-50 text-ms-blue'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300')}>
                  {FREQ_LABEL[f]}
                </button>
              ))}
            </div>
          </div>

          {/* Day of week — hidden for daily/monthly */}
          {form.frequency !== 'daily' && form.frequency !== 'monthly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
              <div className="flex flex-wrap gap-2">
                {DAYS.map((d, i) => (
                  <button key={i} type="button" onClick={() => setForm({ ...form, delivery_day: i })}
                    className={clsx('px-3 py-1.5 rounded-lg border-2 text-sm font-medium transition-all',
                      form.delivery_day === i
                        ? 'border-ms-blue bg-blue-50 text-ms-blue'
                        : 'border-gray-200 text-gray-600 hover:border-gray-300')}>
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}

          {form.frequency === 'monthly' && (
            <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-2.5 text-sm text-ms-blue">
              📅 Monthly digests are delivered on the <strong>1st of every month</strong>.
            </div>
          )}

          {/* Delivery time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Delivery Time <span className="text-xs text-gray-400 font-normal">(IST)</span>
            </label>
            <select className="input" value={form.delivery_time}
              onChange={e => setForm({ ...form, delivery_time: e.target.value })}>
              {TIMES.map(t => {
                const [h] = t.split(':').map(Number);
                const ap = h < 12 ? 'AM' : 'PM';
                const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
                return <option key={t} value={t}>{h12}:00 {ap}</option>;
              })}
            </select>
          </div>

          {/* Preview */}
          <div className="text-xs text-gray-400 bg-gray-50 rounded-lg px-3 py-2">
            Preview: <strong>{scheduleLabel({
              frequency: form.frequency,
              delivery_time: form.delivery_time,
              delivery_day: form.delivery_day,
            })}</strong>
          </div>
        </div>

        {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

        <div className="flex justify-end gap-3 mt-5">
          <button onClick={onClose} className="btn-secondary">Cancel</button>
          <button onClick={handleSave} disabled={loading} className="btn-primary flex items-center">
            {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Check className="h-4 w-4 mr-2" />}
            Save Schedule
          </button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Modal: Invite Member
// ─────────────────────────────────────────────────────────────────────────────

function InviteModal({ teamId, onClose, onInvited }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true); setError('');
    try {
      const res = await inviteMember(teamId, { email: email.trim(), role: 'member' });
      setResult(res.data);
      onInvited(res.data.member);
    } catch (err) {
      const d = err.response?.data?.detail;
      setError(typeof d === 'string' ? d : 'Failed to send invitation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-ms-dark">Invite Member</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-gray-400" /></button>
        </div>

        {result ? (
          <div className="space-y-4">
            <div className={clsx('flex items-start gap-2 rounded-lg px-4 py-3 text-sm',
              result.email_sent ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700')}>
              <Check className="h-5 w-5 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Invitation sent to {result.member?.email}</p>
                <p className="text-xs mt-0.5">
                  {result.email_sent ? 'Email delivered ✓' : 'Email failed — share the link below manually'}
                </p>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1.5">Invite link</label>
              <div className="flex items-center gap-2">
                <input readOnly value={result.invite_url || ''} className="input flex-1 text-xs font-mono" />
                <button className="btn-secondary px-3"
                  onClick={() => navigator.clipboard.writeText(result.invite_url || '')}>
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>
            <p className="text-xs text-gray-400">
              Expires: {result.invitation_expires_at
                ? new Date(result.invitation_expires_at).toLocaleDateString() : '—'}
            </p>
            <div className="flex justify-end">
              <button onClick={onClose} className="btn-primary">Done</button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
              <input type="email" className="input" placeholder="colleague@company.com"
                value={email} onChange={e => setEmail(e.target.value)} required />
              <p className="text-xs text-gray-400 mt-1">
                An invitation email is sent automatically. The link expires in 7 days.
              </p>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex justify-end gap-3">
              <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={loading} className="btn-primary flex items-center">
                {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <UserPlus className="h-4 w-4 mr-2" />}
                Send Invite
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Team card (expanded view)
// ─────────────────────────────────────────────────────────────────────────────

function TeamCard({ team: initialTeam, currentUserId, onDeleted }) {
  const [team, setTeam] = useState(initialTeam);
  const [expanded, setExpanded] = useState(false);
  const [tab, setTab] = useState('members'); // members | newsletter | digests
  const [modal, setModal] = useState(null);  // null | 'invite' | 'topics' | 'schedule'
  const [digests, setDigests] = useState([]);
  const [digestLoading, setDigestLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState({});

  const isAdmin = String(team.admin_id) === String(currentUserId);
  const nl = team.newsletter;
  const members = team.members || [];
  const acceptedCount = members.filter(m => m.status === 'accepted').length;
  const pendingCount  = members.filter(m => m.status === 'pending').length;

  const loadDigests = useCallback(async () => {
    setDigestLoading(true);
    try {
      const r = await getTeamDigests(team.id);
      setDigests(r.data);
    } catch {}
    finally { setDigestLoading(false); }
  }, [team.id]);

  const handleTabChange = (t) => {
    setTab(t);
    if (t === 'digests' && digests.length === 0) loadDigests();
  };

  const handleMemberAction = async (action, memberId) => {
    setActionLoading(s => ({ ...s, [memberId]: action }));
    try {
      if (action === 'remove') {
        await removeMember(team.id, memberId);
        setTeam(t => ({ ...t, members: t.members.map(m =>
          m.id === memberId ? { ...m, status: 'removed' } : m) }));
      } else if (action === 'resend') {
        const res = await resendInvitation(team.id, memberId);
        setTeam(t => ({ ...t, members: t.members.map(m =>
          m.id === memberId ? { ...m, status: res.data.member.status } : m) }));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(s => ({ ...s, [memberId]: null }));
    }
  };

  const handleDeleteTeam = async () => {
    if (!window.confirm(`Delete team "${team.name}" and all its data? This cannot be undone.`)) return;
    try {
      await deleteTeam(team.id);
      onDeleted(team.id);
    } catch (e) { console.error(e); }
  };

  const handleTopicsSaved = (updatedNl) => {
    setTeam(t => ({ ...t, newsletter: { ...t.newsletter, topics: updatedNl.topics } }));
    setModal(null);
  };

  const handleScheduleSaved = (updatedNl) => {
    setTeam(t => ({
      ...t, newsletter: {
        ...t.newsletter,
        frequency:     updatedNl.frequency,
        delivery_time: updatedNl.delivery_time,
        delivery_day:  updatedNl.delivery_day,
        timezone:      'Asia/Kolkata',
      },
    }));
    setModal(null);
  };

  const handleMemberInvited = (member) => {
    setTeam(t => ({
      ...t,
      members: [...t.members.filter(m => m.id !== member.id), member],
    }));
    setModal(null);
  };

  return (
    <>
      <div className="card p-0 overflow-hidden">
        {/* Header row */}
        <div className="flex items-center justify-between p-5 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => setExpanded(e => !e)}>
          <div className="flex items-center gap-3">
            <div className="bg-ms-blue/10 rounded-lg p-2.5">
              <Users className="h-5 w-5 text-ms-blue" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-ms-dark">{team.name}</h3>
                {isAdmin && (
                  <span className="text-xs bg-blue-100 text-ms-blue px-1.5 py-0.5 rounded-full">Admin</span>
                )}
                {nl && !nl.is_active && (
                  <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded-full">Paused</span>
                )}
              </div>
              <p className="text-sm text-gray-400 mt-0.5">
                {acceptedCount} accepted · {pendingCount} pending
                {nl && <span className="ml-2">· {FREQ_LABEL[nl.frequency] || nl.frequency}</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAdmin && (
              <button onClick={e => { e.stopPropagation(); handleDeleteTeam(); }}
                className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-colors"
                title="Delete team">
                <Trash2 className="h-4 w-4" />
              </button>
            )}
            {expanded ? <ChevronUp className="h-5 w-5 text-gray-400" /> : <ChevronDown className="h-5 w-5 text-gray-400" />}
          </div>
        </div>

        {/* Expanded content */}
        {expanded && (
          <div className="border-t">
            {/* Tabs */}
            <div className="flex border-b px-5 pt-3 gap-1">
              {[
                { key: 'members',    label: `Members (${members.length})` },
                { key: 'newsletter', label: 'Newsletter' },
                { key: 'digests',    label: 'Digest History' },
              ].map(({ key, label }) => (
                <button key={key} onClick={() => handleTabChange(key)}
                  className={clsx('px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors',
                    tab === key
                      ? 'border-ms-blue text-ms-blue bg-blue-50'
                      : 'border-transparent text-gray-500 hover:text-ms-dark')}>
                  {label}
                </button>
              ))}
            </div>

            {/* Tab: Members */}
            {tab === 'members' && (
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-gray-500">
                    {acceptedCount} accepted · {pendingCount} pending
                  </p>
                  {isAdmin && (
                    <button onClick={() => setModal('invite')}
                      className="text-ms-blue text-sm flex items-center gap-1 hover:underline">
                      <UserPlus className="h-3.5 w-3.5" /> Invite Member
                    </button>
                  )}
                </div>

                {members.length === 0 ? (
                  <p className="text-sm text-gray-400">No members yet. Invite someone to get started.</p>
                ) : (
                  <div className="space-y-2">
                    {members.map(m => (
                      <div key={m.id}
                        className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="h-7 w-7 rounded-full bg-ms-blue/10 flex items-center justify-center shrink-0">
                            <span className="text-xs font-bold text-ms-blue uppercase">
                              {m.email[0]}
                            </span>
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-ms-dark truncate">{m.email}</p>
                            <p className="text-xs text-gray-400 capitalize">{m.role}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0 ml-2">
                          <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium',
                            STATUS_PILL[m.status] || 'bg-gray-100 text-gray-500')}>
                            {m.status}
                          </span>
                          {isAdmin && m.status !== 'removed' && (
                            <div className="flex items-center gap-1">
                              {['pending','declined','expired'].includes(m.status) && (
                                <button
                                  onClick={() => handleMemberAction('resend', m.id)}
                                  disabled={actionLoading[m.id] === 'resend'}
                                  title="Resend invite"
                                  className="p-1 rounded hover:bg-blue-50 text-gray-400 hover:text-ms-blue transition-colors">
                                  {actionLoading[m.id] === 'resend'
                                    ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                    : <RotateCcw className="h-3.5 w-3.5" />}
                                </button>
                              )}
                              <button
                                onClick={() => handleMemberAction('remove', m.id)}
                                disabled={actionLoading[m.id] === 'remove'}
                                title={m.status === 'pending' ? 'Cancel invite' : 'Remove member'}
                                className="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                                {actionLoading[m.id] === 'remove'
                                  ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                  : <X className="h-3.5 w-3.5" />}
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab: Newsletter */}
            {tab === 'newsletter' && (
              <div className="p-5 space-y-4">
                {!nl ? (
                  <p className="text-sm text-gray-400">No newsletter configured.</p>
                ) : (
                  <>
                    {/* Topics */}
                    <div className="bg-gray-50 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2.5">
                        <div className="flex items-center gap-2">
                          <Tag className="h-4 w-4 text-ms-blue" />
                          <span className="text-sm font-semibold text-ms-dark">Topics</span>
                        </div>
                        {isAdmin && (
                          <button onClick={() => setModal('topics')}
                            className="text-xs text-ms-blue hover:underline">Edit Topics</button>
                        )}
                      </div>
                      {(nl.topics || []).length === 0 ? (
                        <p className="text-sm text-gray-400">No topics set.</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {nl.topics.map(t => (
                            <span key={t.id || t.topic_id}
                              className="text-xs bg-blue-100 text-ms-blue px-2.5 py-0.5 rounded-full font-medium">
                              {t.topic_name}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Schedule */}
                    <div className="bg-gray-50 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2.5">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-ms-blue" />
                          <span className="text-sm font-semibold text-ms-dark">Schedule</span>
                        </div>
                        {isAdmin && (
                          <button onClick={() => setModal('schedule')}
                            className="text-xs text-ms-blue hover:underline">Edit Schedule</button>
                        )}
                      </div>
                      <p className="text-sm text-ms-dark font-medium">{scheduleLabel(nl)}</p>
                    </div>

                    {/* Status */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={clsx('h-2 w-2 rounded-full', nl.is_active ? 'bg-green-500' : 'bg-yellow-400')} />
                        <span className="text-sm text-gray-600">
                          {nl.is_active ? 'Active — sending digests' : 'Paused — no digests being sent'}
                        </span>
                      </div>
                      {isAdmin && (
                        <button
                          onClick={async () => {
                            try {
                              const res = await toggleTeamNewsletter(team.id);
                              setTeam(t => ({ ...t, newsletter: { ...t.newsletter, is_active: res.data.is_active } }));
                            } catch {}
                          }}
                          className="text-xs text-gray-500 hover:text-ms-blue underline">
                          {nl.is_active ? 'Pause' : 'Resume'}
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* Tab: Digest History */}
            {tab === 'digests' && (
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm text-gray-500">Last 20 digests for this team</p>
                  <button onClick={loadDigests} className="text-xs text-ms-blue hover:underline flex items-center gap-1">
                    <RefreshCw className="h-3 w-3" /> Refresh
                  </button>
                </div>
                {digestLoading ? (
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <Loader2 className="h-4 w-4 animate-spin" /> Loading…
                  </div>
                ) : digests.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-40" />
                    <p className="text-sm">No digests sent yet.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {digests.map(d => (
                      <div key={d.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <Mail className="h-4 w-4 text-ms-blue shrink-0" />
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-ms-dark truncate">{d.title}</p>
                            <p className="text-xs text-gray-400 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {new Date(d.created_at).toLocaleDateString('en-US',
                                { month:'short', day:'numeric', year:'numeric' })}
                              {d.recipient_count > 0 && ` · ${d.recipient_count} recipients`}
                            </p>
                          </div>
                        </div>
                        <span className={clsx('text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ml-2',
                          DIGEST_STATUS_PILL[d.status] || 'bg-gray-100 text-gray-500')}>
                          {d.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {modal === 'invite' && (
        <InviteModal teamId={team.id} onClose={() => setModal(null)} onInvited={handleMemberInvited} />
      )}
      {modal === 'topics' && (
        <EditTopicsModal team={team} onClose={() => setModal(null)} onSaved={handleTopicsSaved} />
      )}
      {modal === 'schedule' && (
        <EditScheduleModal team={team} onClose={() => setModal(null)} onSaved={handleScheduleSaved} />
      )}
    </>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Teams page
// ─────────────────────────────────────────────────────────────────────────────

export default function Teams() {
  const { user } = useAuth();
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    getTeams()
      .then(r => setTeams(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleTeamCreated = (team) => {
    setTeams(prev => [team, ...prev]);
    setShowCreate(false);
  };

  const handleTeamDeleted = (teamId) => {
    setTeams(prev => prev.filter(t => t.id !== teamId));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-ms-dark">Teams</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Each team has one newsletter configuration — topics, schedule, and members all in one place.
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center">
          <Plus className="mr-2 h-4 w-4" /> Create Team
        </button>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2].map(n => <div key={n} className="card animate-pulse h-20 bg-gray-50" />)}
        </div>
      ) : teams.length === 0 ? (
        <div className="card text-center py-16">
          <Users className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-700">No teams yet</h3>
          <p className="text-gray-400 mt-1 text-sm">
            Create a team to send shared Microsoft Learn digests.
          </p>
          <button onClick={() => setShowCreate(true)} className="btn-primary mt-5 inline-flex">
            <Plus className="inline h-4 w-4 mr-1.5" /> Create your first team
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {teams.map(team => (
            <TeamCard
              key={team.id}
              team={team}
              currentUserId={user?.id}
              onDeleted={handleTeamDeleted}
            />
          ))}
        </div>
      )}

      {showCreate && (
        <CreateTeamModal onClose={() => setShowCreate(false)} onCreated={handleTeamCreated} />
      )}
    </div>
  );
}
