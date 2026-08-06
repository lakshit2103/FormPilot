import { apiClient as client } from './client'

export const settingsApi = {
  getAccount: () => client.get('/api/settings/account'),

  updateName: (fullName: string) =>
    client.patch('/api/settings/account/name', { full_name: fullName }),

  changePassword: (currentPassword: string, newPassword: string) =>
    client.post('/api/settings/account/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  listSessions: () => client.get('/api/settings/sessions'),

  revokeSession: (sessionId: string) =>
    client.delete(`/api/settings/sessions/${sessionId}`),

  revokeAllSessions: () => client.post('/api/settings/sessions/revoke-all'),

  exportData: () => client.get('/api/settings/data-export'),

  deleteAccount: (password: string) =>
    client.delete('/api/settings/account', {
      data: { password, confirmation: 'DELETE' },
    }),
}
