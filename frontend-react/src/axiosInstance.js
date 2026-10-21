import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_BACKEND_BASE_API || '/api/v1'
const axiosInstance = axios.create({ baseURL, timeout: 60000, headers: { 'Content-Type': 'application/json' } })
const publicPaths = ['/register/', '/token/', '/token/refresh/']
let refreshPromise = null

function clearSession() {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
  window.dispatchEvent(new Event('session-expired'))
}

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token && !publicPaths.includes(config.url)) config.headers.Authorization = `Bearer ${token}`
  return config
})

axiosInstance.interceptors.response.use((response) => response, async (error) => {
  const original = error.config
  if (error.response?.status !== 401 || !original || original._retry || publicPaths.includes(original.url)) {
    return Promise.reject(error)
  }
  original._retry = true
  const refresh = localStorage.getItem('refreshToken')
  if (!refresh) {
    clearSession()
    return Promise.reject(error)
  }
  try {
    if (!refreshPromise) {
      refreshPromise = axiosInstance.post('/token/refresh/', { refresh })
        .then(({ data }) => {
          localStorage.setItem('accessToken', data.access)
          return data.access
        })
        .finally(() => { refreshPromise = null })
    }
    const access = await refreshPromise
    original.headers.Authorization = `Bearer ${access}`
    return axiosInstance(original)
  } catch (refreshError) {
    clearSession()
    return Promise.reject(refreshError)
  }
})

export default axiosInstance
