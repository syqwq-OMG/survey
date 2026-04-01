import axios from 'axios'

// 创建一个 axios 实例
const request = axios.create({
  // 这里假设你的 FastAPI 后端运行在 8000 端口
  baseURL: 'http://127.0.0.1:8000', 
  timeout: 5000
})

// 请求拦截器：自动注入 Token
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      // 如果后端返回 401 未授权，清除本地 token 并刷新页面让路由拦截
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default request