const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8015/api'

export function communityPhotoUrl(postId, position, moderation) {
  return `${BASE_URL}/community/${postId}/photos/${position}${moderation ? '/preview' : ''}`
}

export async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (response.status === 204) return null
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'No se pudo completar la solicitud.')
  return body
}

export const api = {
  me: () => request('/auth/me'),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  analyze: (text) => request('/analyze', { method: 'POST', body: JSON.stringify({ text }) }),
  chat: (question, topic) => request('/chat', { method: 'POST', body: JSON.stringify({ question, topic }) }),
  chatTopics: () => request('/chat/topics'),
  report: (text) => request('/reports', { method: 'POST', body: JSON.stringify({ text, consent: true }) }),
  myReports: () => request('/reports/mine'),
  reviewReports: () => request('/review/reports'),
  patterns: () => request('/review/patterns'),
  review: (id, data) => request(`/review/reports/${id}`, { method: 'POST', body: JSON.stringify(data) }),
  duplicate: (id, original_id) => request(`/review/reports/${id}/duplicate`, { method: 'POST', body: JSON.stringify({ original_id }) }),
  createDataset: () => request('/review/dataset', { method: 'POST' }),
  users: () => request('/admin/users'),
  grantRole: (email, role) => request(`/admin/users/${encodeURIComponent(email)}/role`, { method: 'POST', body: JSON.stringify({ role }) }),
  deleteReport: (id, deletion_code) => request(`/reports/${id}/delete`, { method: 'POST', body: JSON.stringify({ deletion_code }) }),
}
