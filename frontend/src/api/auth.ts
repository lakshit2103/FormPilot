import { apiClient } from './client'

export interface RegisterData { full_name: string; email: string; password: string }
export interface LoginData { email: string; password: string }
export interface TokenResponse { access_token: string; refresh_token: string; token_type: string; setup_complete: boolean }
export interface UserResponse { id: string; full_name: string; email: string; is_email_verified: boolean; setup_complete: boolean }

export const authApi = {
  register: (data: RegisterData) => apiClient.post<UserResponse>('/api/auth/register', data),
  verifyEmail: (token: string) => apiClient.post<UserResponse>('/api/auth/verify-email', { token }),
  resendVerification: (email: string) => apiClient.post('/api/auth/resend-verification', { email }),
  login: (data: LoginData) => apiClient.post<TokenResponse>('/api/auth/login', data),
  logout: (refresh_token: string) => apiClient.post('/api/auth/logout', { refresh_token }),
  refresh: (refresh_token: string) => apiClient.post<TokenResponse>('/api/auth/refresh', { refresh_token }),
  forgotPassword: (email: string) => apiClient.post('/api/auth/forgot-password', { email }),
  resetPassword: (token: string, new_password: string) => apiClient.post('/api/auth/reset-password', { token, new_password }),
  getMe: () => apiClient.get<UserResponse>('/api/auth/me'),
}
