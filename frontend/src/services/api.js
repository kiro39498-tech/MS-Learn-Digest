/**
 * Centralized Axios API client.
 * All API calls go through this module.
 */
 
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 60000,
});

// Attach JWT from localStorage to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export const exchangeGoogleCode = (code, redirectUri) =>
  api.post('/api/auth/google', { code, redirect_uri: redirectUri });

// ── User ──────────────────────────────────────────────────────────────────────

export const getMe = () => api.get('/api/users/me');

export const updatePreferences = (data) => api.put('/api/users/me/preferences', data);

// ── Topics ────────────────────────────────────────────────────────────────────

export const getTopics = () => api.get('/api/topics/');

export const getTopicTree = () => api.get('/api/topics/tree');

export const getRootTopics = () => api.get('/api/topics/roots');

export const getMyTopics = () => api.get('/api/topics/my');

export const subscribeTopics = (topicIds) =>
  api.post('/api/topics/subscribe', { topic_ids: topicIds });

export const completeOnboarding = (topicIds) =>
  api.post('/api/topics/onboard', { topic_ids: topicIds });

// ── Teams ─────────────────────────────────────────────────────────────────────

export const getTeams = () => api.get('/api/teams/');

/** Create a team + newsletter in one request */
export const createTeam = (data) => api.post('/api/teams/', data);

export const getTeam = (teamId) => api.get(`/api/teams/${teamId}`);

export const updateTeam = (teamId, data) => api.patch(`/api/teams/${teamId}`, data);

export const deleteTeam = (teamId) => api.delete(`/api/teams/${teamId}`);

// ── Team newsletter (one per team) ────────────────────────────────────────────

export const getTeamNewsletter = (teamId) =>
  api.get(`/api/teams/${teamId}/newsletter`);

export const updateTeamTopics = (teamId, topicIds) =>
  api.patch(`/api/teams/${teamId}/newsletter/topics`, { topic_ids: topicIds });

export const updateTeamSchedule = (teamId, data) =>
  api.patch(`/api/teams/${teamId}/newsletter/schedule`, data);

export const toggleTeamNewsletter = (teamId) =>
  api.patch(`/api/teams/${teamId}/newsletter/toggle`);

// ── Team Members ──────────────────────────────────────────────────────────────

export const inviteMember = (teamId, data) =>
  api.post(`/api/teams/${teamId}/invite`, data);

export const resendInvitation = (teamId, memberId) =>
  api.post(`/api/teams/${teamId}/members/${memberId}/resend`);

export const removeMember = (teamId, memberId) =>
  api.delete(`/api/teams/${teamId}/members/${memberId}`);

// ── Team Digest History ───────────────────────────────────────────────────────

export const getTeamDigests = (teamId) =>
  api.get(`/api/teams/${teamId}/digests`);

// ── Team Invitations (public) ─────────────────────────────────────────────────

export const getInvitePreview = (token) =>
  api.get(`/api/teams/invite/${token}`);

export const acceptInvitation = (token) =>
  api.post(`/api/teams/invite/${token}/accept`);

export const declineInvitation = (token) =>
  api.post(`/api/teams/invite/${token}/decline`);

// ── Digests ───────────────────────────────────────────────────────────────────

export const getDigests = () => api.get('/api/digests/');

export const getDigest = (digestId) => api.get(`/api/digests/${digestId}`);

// ── Admin — SMTP & test digests ───────────────────────────────────────────────

export const adminGetConfig = () => api.get('/api/admin/config');

export const adminSmtpCheck = () => api.get('/api/admin/smtp-check');

export const adminSendTestEmail = (email) =>
  api.post('/api/admin/send-test-email', { email });

export const adminGenerateTestDigest = () =>
  api.post('/api/admin/generate-test-digest');

export const adminSendTestDigest = (email, userName) =>
  api.post('/api/admin/send-test-digest', { email, user_name: userName });

export const adminPreviewDigest = () =>
  `${api.defaults.baseURL}/api/admin/preview-digest`;

// ── Admin — Catalog cache ─────────────────────────────────────────────────────

export const adminCatalogSync = () =>
  api.post('/api/admin/catalog-sync', null, { timeout: 360000 });

export const adminCatalogCacheStats = () =>
  api.get('/api/admin/catalog-cache/stats');

export const adminCatalogPreview = (topicSlugs, frequency) =>
  api.post('/api/admin/catalog-cache/preview', {
    topic_slugs: topicSlugs,
    frequency,
  });

// ── Admin — Diagnostics ───────────────────────────────────────────────────────

export const adminSendMyDigest = () =>
  api.post('/api/admin/test/send-my-digest', null, { timeout: 120000 });

export const adminRepairTopics = () =>
  api.post('/api/admin/repair-topics');

export const adminDebugOnboarding = () =>
  api.get('/api/admin/debug/onboarding');

// ── Admin — Team Testing ──────────────────────────────────────────────────────

export const adminTeamCreate = (teamName) =>
  api.post('/api/admin/teams/test-create', { team_name: teamName });

export const adminTeamInvite = (teamId, email) =>
  api.post(`/api/admin/teams/${teamId}/test-invite`, { email });

export const adminTeamAcceptInvite = (token) =>
  api.post(`/api/admin/teams/invite/${token}/accept`);

export const adminTeamRejectInvite = (token) =>
  api.post(`/api/teams/invite/${token}/decline`);

export const adminTeamSendDigest = (teamId) =>
  api.post(`/api/admin/teams/${teamId}/test-digest`, null, { timeout: 120000 });

export const adminTeamDeliveryStatus = (teamId) =>
  api.get(`/api/admin/teams/${teamId}/delivery-status`);

// ── Learning Tracks ───────────────────────────────────────────────────────────

export const getLearningTopics = () => api.get('/api/learning/topics');

export const getLearningTopic = (topicId) => api.get(`/api/learning/topics/${topicId}`);

export const getLearningTopicModules = (topicId) =>
  api.get(`/api/learning/topics/${topicId}/modules`);

export const subscribeToLearningTrack = (topicId, frequency) =>
  api.post('/api/learning/subscribe', { topic_id: topicId, frequency });

export const unsubscribeFromLearningTrack = (topicId) =>
  api.delete(`/api/learning/subscribe/${topicId}`);

export const updateLearningFrequency = (topicId, frequency) =>
  api.patch(`/api/learning/subscribe/${topicId}/frequency`, { frequency });

export const getMyLearningTracks = () => api.get('/api/learning/my');

export const getLearningProgress = (topicId) =>
  api.get(`/api/learning/progress/${topicId}`);

export const getCompletedTracks = () => api.get('/api/learning/completed');

export const getLearningAnalytics = () => api.get('/api/learning/analytics');

export const getLearningStatus = () => api.get('/api/learning/status');

export const seedLearningTopics = () => api.post('/api/learning/seed');

// ── Learning Engine (admin) ───────────────────────────────────────────────────

export const adminLearningStatus = () =>
  api.get('/api/admin/learning/status');

export const adminSendLearningLesson = () =>
  api.post('/api/admin/learning/send-lesson', null, { timeout: 120000 });

export default api;
