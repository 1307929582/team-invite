import { useState } from 'react'
import { Card, Form, Input, Button, message, Result } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { setupApi } from '../api'

export default function Setup() {
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      await setupApi.initialize({
        username: values.username,
        email: values.email,
        password: values.password,
        confirm_password: values.confirmPassword
      })
      setSuccess(true)
      // 延迟跳转，让用户看到成功提示
      setTimeout(() => {
        navigate('/admin/login')
        // 刷新页面以更新初始化状态
        window.location.reload()
      }, 2000)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '初始化失败')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%)',
        padding: 20,
      }}>
        <Card style={{
          width: 440,
          background: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(40px)',
          borderRadius: 24,
          border: '1px solid rgba(255, 255, 255, 0.9)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)',
        }}>
          <Result
            icon={<CheckCircleOutlined style={{ color: '#10b981' }} />}
            title="系统初始化成功！"
            subTitle={
              <div>
                <p>管理员账号已创建</p>
                <p style={{ color: '#64748b', fontSize: 13, marginTop: 8 }}>
                  正在跳转到登录页面...
                </p>
              </div>
            }
          />
        </Card>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%)',
      padding: 20,
    }}>
      {/* 装饰光晕 */}
      <div style={{ position: 'fixed', top: '10%', right: '20%', width: 400, height: 400, background: 'radial-gradient(circle, rgba(147, 197, 253, 0.3) 0%, transparent 70%)', borderRadius: '50%', zIndex: 0 }} />
      <div style={{ position: 'fixed', bottom: '20%', left: '15%', width: 300, height: 300, background: 'radial-gradient(circle, rgba(196, 181, 253, 0.25) 0%, transparent 70%)', borderRadius: '50%', zIndex: 0 }} />

      <Card style={{
        width: 440,
        background: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(40px)',
        WebkitBackdropFilter: 'blur(40px)',
        borderRadius: 24,
        border: '1px solid rgba(255, 255, 255, 0.9)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.08)',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ 
            width: 56, height: 56, borderRadius: 16,
            background: 'linear-gradient(135deg, #1a1a2e 0%, #2d2d44 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
          }}>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: 22 }}>Z</span>
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 8px', color: '#1a1a2e' }}>
            系统初始化
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, margin: 0 }}>
            首次部署，请设置管理员账号
          </p>
        </div>

        <Form form={form} onFinish={handleSubmit} layout="vertical" size="large">
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3位' }
            ]}
          >
            <Input 
              prefix={<UserOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="管理员用户名"
              style={{ height: 48, borderRadius: 12 }}
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱' }
            ]}
          >
            <Input 
              prefix={<MailOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="管理员邮箱"
              style={{ height: 48, borderRadius: 12 }}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="设置密码"
              style={{ height: 48, borderRadius: 12 }}
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined style={{ color: '#94a3b8' }} />} 
              placeholder="确认密码"
              style={{ height: 48, borderRadius: 12 }}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
            <Button 
              type="primary" 
              htmlType="submit" 
              block 
              loading={loading}
              style={{ height: 48, borderRadius: 12, fontWeight: 600 }}
            >
              完成初始化
            </Button>
          </Form.Item>
        </Form>

        <div style={{ marginTop: 20, padding: 16, background: 'rgba(251, 191, 36, 0.1)', borderRadius: 12 }}>
          <p style={{ margin: 0, fontSize: 13, color: '#92400e' }}>
            ⚠️ 请牢记管理员账号密码，初始化后无法通过此页面重置
          </p>
        </div>
      </Card>
    </div>
  )
}
