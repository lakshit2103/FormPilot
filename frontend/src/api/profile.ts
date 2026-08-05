import { apiClient } from './client'

export const profileApi = {
  getProfile: () => apiClient.get('/api/profile'),
  updateProfile: (data: Record<string, unknown>) => apiClient.put('/api/profile', data),
  getCompletion: () => apiClient.get('/api/profile/completion'),

  listEducation: () => apiClient.get('/api/profile/education'),
  createEducation: (data: Record<string, unknown>) => apiClient.post('/api/profile/education', data),
  updateEducation: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/education/${id}`, data),
  deleteEducation: (id: string) => apiClient.delete(`/api/profile/education/${id}`),

  listExperience: () => apiClient.get('/api/profile/experience'),
  createExperience: (data: Record<string, unknown>) => apiClient.post('/api/profile/experience', data),
  updateExperience: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/experience/${id}`, data),
  deleteExperience: (id: string) => apiClient.delete(`/api/profile/experience/${id}`),

  listSkills: () => apiClient.get('/api/profile/skills'),
  createSkill: (data: Record<string, unknown>) => apiClient.post('/api/profile/skills', data),
  updateSkill: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/skills/${id}`, data),
  deleteSkill: (id: string) => apiClient.delete(`/api/profile/skills/${id}`),

  listProjects: () => apiClient.get('/api/profile/projects'),
  createProject: (data: Record<string, unknown>) => apiClient.post('/api/profile/projects', data),
  updateProject: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/projects/${id}`, data),
  deleteProject: (id: string) => apiClient.delete(`/api/profile/projects/${id}`),

  listCertifications: () => apiClient.get('/api/profile/certifications'),
  createCertification: (data: Record<string, unknown>) => apiClient.post('/api/profile/certifications', data),
  updateCertification: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/certifications/${id}`, data),
  deleteCertification: (id: string) => apiClient.delete(`/api/profile/certifications/${id}`),

  listAddresses: () => apiClient.get('/api/profile/addresses'),
  createAddress: (data: Record<string, unknown>) => apiClient.post('/api/profile/addresses', data),
  updateAddress: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/addresses/${id}`, data),
  deleteAddress: (id: string) => apiClient.delete(`/api/profile/addresses/${id}`),

  getPreferences: () => apiClient.get('/api/profile/preferences'),
  updatePreferences: (data: Record<string, unknown>) => apiClient.put('/api/profile/preferences', data),

  listLinks: () => apiClient.get('/api/profile/professional-links'),
  createLink: (data: Record<string, unknown>) => apiClient.post('/api/profile/professional-links', data),
  updateLink: (id: string, data: Record<string, unknown>) => apiClient.patch(`/api/profile/professional-links/${id}`, data),
  deleteLink: (id: string) => apiClient.delete(`/api/profile/professional-links/${id}`),
}
