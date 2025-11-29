import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authApi } from '../api'
import { useStore } from '../store'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { setUser } = useStore()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res: any = await authApi.login(values.username, values.password)
      localStorage.setItem('token', res.access_token)
      const user: any = await authApi.getMe()
      setUser(user)
      message.success('登录成功')
      navigate('/admin/dashboard')
    } catch {
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 50%, #f5f7fa 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* 装饰光晕 */}
      <div style={{
        position: 'absolute',
        top: '10%',
        right: '20%',
        width: 500,
        height: 500,
        background: 'radial-gradient(circle, rgba(147, 197, 253, 0.35) 0%, transparent 70%)',
        borderRadius: '50%',
      }} />
      <div style={{
        position: 'absolute',
        bottom: '20%',
        left: '15%',
        width: 400,
        height: 400,
        background: 'radial-gradient(circle, rgba(196, 181, 253, 0.3) 0%, transparent 70%)',
        borderRadius: '50%',
      }} />

      <div style={{
        width: 420,
        padding: 48,
        background: 'rgba(255, 255, 255, 0.75)',
        backdropFilter: 'blur(40px) saturate(180%)',
        WebkitBackdropFilter: 'blur(40px) saturate(180%)',
        borderRadius: 28,
        border: '1px solid rgba(255, 255, 255, 0.9)',
        boxShadow: '0 24px 80px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9)',
        position: 'relative',
        zIndex: 1,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 44 }}>
          <div style={{ 
            width: 64, 
            height: 64, 
            borderRadius: 18,
            background: 'linear-gradient(135deg, #1a1a2e 0%, #2d2d44 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
          }}>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: 26 }}>Z</span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 10px 0', color: '#1a1a2e', letterSpacing: '-0.5px' }}>
            管理后台
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, margin: 0 }}>
            请输入管理员账号登录
          </p>
        </div>
        
        <Form name="login" onFinish={onFinish}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input 
              prefix={<UserOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="用户名" 
              size="large" 
              style={{ height: 52, borderRadius: 14 }}
            />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password 
              prefix={<LockOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="密码" 
              size="large"
              style={{ height: 52, borderRadius: 14 }}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0, marginTop: 36 }}>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading} 
              block 
              size="large"
              style={{ 
                height: 52, 
                borderRadius: 14, 
                fontSize: 15, 
                fontWeight: 600,
              }}
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}
