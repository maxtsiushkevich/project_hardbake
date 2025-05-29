import { authApi } from './api'

export const getToken = () => {
  const cookies = document.cookie.split(';')
  const tokenCookie = cookies.find(cookie => cookie.trim().startsWith('access_token='))
  return tokenCookie ? tokenCookie.split('=')[1] : null
}

export const setToken = (token) => {
  document.cookie = `access_token=${token}; path=/`
}

export const removeToken = () => {
  document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
}

export const login = async (username, password) => {
  const response = await authApi.post('/auth/token', null, {
    params: { username, password }
  })
  setToken(response.data.access_token)
  return response.data
}

export const logout = async () => {
  try {
    await authApi.post('/auth/logout')
  } finally {
    removeToken()
  }
}

export const getCurrentUser = async () => {
  const response = await authApi.get('/auth/users/me/')
  return response.data
}

export const isAuthenticated = () => {
  return !!getToken()
} 