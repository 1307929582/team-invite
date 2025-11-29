import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Spin, message } from 'antd'
import { publicApi } from '../api'

export default function Callback() {
  const navigate = useNavigate()
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const state = params.get('state')
    
    if (!code) {
      setError('授权失败：未获取到授权码')
      return
    }

    // 验证 state
    const savedState = localStorage.getItem('linuxdo_state')
    if (state !== savedState) {
      setError('授权失败：state 验证失败')
      return
    }

    // 换取用户信息
    publicApi.linuxdoCallback(code, state || '')
      .then((res: any) => {
        localStorage.setItem('linuxdo_user', JSON.stringify(res))
        localStorage.removeItem('linuxdo_state')
        message.success(`欢迎，${res.name || res.username}！`)
        navigate('/')
      })
      .catch((e: any) => {
        setError(e.response?.data?.detail || '登录失败')
      })
  }, [navigate])

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%)',
      }}>
        <div style={{ color: '#ef4444', fontSize: 18, marginBottom: 16 }}>😢 {error}</div>
        <a href="/" style={{ color: '#64748b' }}>返回首页</a>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%)',
    }}>
      <Spin size="large" />
      <div style={{ marginTop: 20, color: '#64748b' }}>正在登录...</div>
    </div>
  )
}
