import { apiClient } from './client'

export const documentsApi = {
  upload: (documentType: string, file: File) => {
    const form = new FormData()
    form.append('document_type', documentType)
    form.append('file', file)
    return apiClient.post('/api/documents/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  list: () => apiClient.get('/api/documents'),
  setDefault: (id: string) => apiClient.patch(`/api/documents/${id}/set-default`),
  delete: (id: string) => apiClient.delete(`/api/documents/${id}`),
  downloadUrl: (id: string) => `${apiClient.defaults.baseURL}/api/documents/${id}/download`,
}
