import { useEffect, useState } from 'react'
import { Card, Input, Button, message, Spin, Result, Steps } from 'antd'
import { UserOutlined, GiftOutlined, MailOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { publicApi } from '../api'

interface LinuxDOUser {
  id: number
  linuxdo_id: string
  username: string
  name?: string
  email?: string
  trust_level: number
  avatar_url?: string
  token: string
}

interface UserStatus {
  has_active_invite: boolean
  team_name?: string
  invite_email?: string
  invite_status?: string
  invite_time?: string
}

interface SeatStats {
  total_seats: number
  used_seats: number
  pending_seats: number
  available_seats: number
}

export default function Home() {
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<LinuxDOUser | null>(null)
  const [status, setStatus] = useState<UserStatus | null>(null)
  const [seats, setSeats] = useState<SeatStats | null>(null)
  const [step, setStep] = useState(0)
  
  // 表单
  const [email, setEmail] = useState('')
  const [redeemCode, setRedeemCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string; team?: string } | null>(null)

  useEffect(() => {
    // 获取座位统计
    publicApi.getSeats().then((res: any) => setSeats(res)).catch(() => {})
    
    // 检查本地存储的用户
    const savedUser = localStorage.getItem('linuxdo_user')
    if (savedUser) {
      const u = JSON.parse(savedUser)
      setUser(u)
      // 获取用户状态
      publicApi.getUserStatus(u.token)
        .then((res: any) => {
          setStatus(res)
          if (res.has_active_invite) {
            setStep(2)
          } else {
            setStep(1)
          }
        })
        .catch(() => {
          localStorage.removeItem('linuxdo_user')
          setUser(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = async () => {
    try {
      const res: any = await publicApi.getLinuxDOAuthUrl()
      localStorage.setItem('linuxdo_state', res.state)
      window.location.href = res.auth_url
    } catch {
      message.error('获取登录链接失败，请稍后重试')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('linuxdo_user')
    setUser(null)
    setStatus(null)
    setStep(0)
    setResult(null)
  }

  const handleSubmit = async () => {
    if (!email || !email.includes('@')) {
      message.error('请输入有效的邮箱地址')
      return
    }
    if (!redeemCode.trim()) {
      message.error('请输入兑换码')
      return
    }
    if (!user) {
      message.error('请先登录')
      return
    }

    setSubmitting(true)
    try {
      const res: any = await publicApi.redeem({
        email: email.trim(),
        redeem_code: redeemCode.trim().toUpperCase(),
        linuxdo_token: user.token
      })
      setResult({ success: true, message: res.message, team: res.team_name })
      setStep(2)
      // 更新状态
      setStatus({
        has_active_invite: true,
        team_name: res.team_name,
        invite_email: email,
        invite_status: 'success'
      })
    } catch (e: any) {
      message.error(e.response?.data?.detail || '兑换失败')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%)' }}>
        <Spin size="large" />
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
            ChatGPT Team 自助上车
          </h1>
          <p style={{ color: '#64748b', fontSize: 14, margin: 0 }}>
            使用兑换码加入 Team
          </p>
        </div>

        {/* 座位统计 */}
        {seats && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-around', 
            padding: '16px 0', 
            marginBottom: 24,
            background: 'rgba(0,0,0,0.02)', 
            borderRadius: 12,
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#10b981' }}>{seats.available_seats}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>可用空位</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#f59e0b' }}>{seats.pending_seats}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>待接受</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#3b82f6' }}>{seats.used_seats}</div>
              <div style={{ fontSize: 12, color: '#64748b' }}>已使用</div>
            </div>
          </div>
        )}

        {/* 步骤条 */}
        <Steps current={step} size="small" style={{ marginBottom: 28 }} items={[
          { title: '登录' },
          { title: '兑换' },
          { title: '完成' },
        ]} />

        {/* Step 0: 登录 */}
        {step === 0 && (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#64748b', marginBottom: 24 }}>
              请先使用 LinuxDO 账号登录
            </p>
            <Button 
              type="primary" 
              size="large" 
              block 
              onClick={handleLogin}
              style={{ height: 48, borderRadius: 12, fontWeight: 600 }}
            >
              <UserOutlined /> 使用 LinuxDO 登录
            </Button>
          </div>
        )}

        {/* Step 1: 输入兑换码 */}
        {step === 1 && user && (
          <div>
            {/* 用户信息 */}
            <div style={{ 
              display: 'flex', alignItems: 'center', gap: 12, 
              padding: 16, background: 'rgba(0,0,0,0.02)', borderRadius: 12, marginBottom: 24 
            }}>
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="" style={{ width: 40, height: 40, borderRadius: 20 }} />
              ) : (
                <div style={{ width: 40, height: 40, borderRadius: 20, background: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserOutlined style={{ fontSize: 18, color: '#64748b' }} />
                </div>
              )}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{user.name || user.username}</div>
                <div style={{ fontSize: 12, color: '#64748b' }}>@{user.username} · Lv.{user.trust_level}</div>
              </div>
              <Button type="link" size="small" onClick={handleLogout}>退出</Button>
            </div>

            {/* 邮箱 */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>邮箱地址</div>
              <Input
                prefix={<MailOutlined style={{ color: '#94a3b8', marginRight: 8 }} />}
                placeholder="  your@email.com"
                size="large"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
              <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 6 }}>
                邀请邮件将发送到此邮箱
              </div>
            </div>

            {/* 兑换码 */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>兑换码</div>
              <Input
                prefix={<GiftOutlined style={{ color: '#94a3b8', marginRight: 8 }} />}
                placeholder="  输入兑换码"
                size="large"
                value={redeemCode}
                onChange={e => setRedeemCode(e.target.value.toUpperCase())}
              />
            </div>

            <Button 
              type="primary" 
              block 
              size="large" 
              loading={submitting}
              onClick={handleSubmit}
              disabled={!email || !redeemCode}
              style={{ height: 48, borderRadius: 12, fontWeight: 600 }}
            >
              立即兑换
            </Button>
          </div>
        )}

        {/* Step 2: 完成 */}
        {step === 2 && (
          <Result
            status="success"
            icon={<CheckCircleOutlined style={{ color: '#10b981' }} />}
            title={result?.success ? '兑换成功！' : '您已加入 Team'}
            subTitle={
              <div>
                <p>{result?.message || `已加入 ${status?.team_name || 'Team'}`}</p>
                {status?.invite_email && (
                  <p style={{ color: '#64748b', fontSize: 13 }}>
                    邀请邮箱：{status.invite_email}
                  </p>
                )}
                <p style={{ color: '#f59e0b', fontSize: 13, marginTop: 12 }}>
                  请查收邮箱并接受邀请
                </p>
              </div>
            }
            extra={
              <Button onClick={handleLogout}>退出登录</Button>
            }
          />
        )}


      </Card>
    </div>
  )
}
