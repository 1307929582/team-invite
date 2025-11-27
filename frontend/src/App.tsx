import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Spin, ConfigProvider, theme as antTheme } from 'antd'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Teams from './pages/Teams'
import TeamDetail from './pages/TeamDetail'
import Invite from './pages/Invite'
import Logs from './pages/Logs'
import RedeemCodes from './pages/RedeemCodes'
import DirectCodes from './pages/DirectCodes'
import LinuxDOUsers from './pages/LinuxDOUsers'
import Settings from './pages/Settings'
import Home from './pages/Home'
import Callback from './pages/Callback'
import Setup from './pages/Setup'
import DirectInvite from './pages/DirectInvite'
import Groups from './pages/Groups'
import InviteRecords from './pages/InviteRecords'
import { useStore } from './store'
import { authApi, setupApi } from './api'

function PrivateRoute({ children, initialized }: { children: React.ReactNode; initialized: boolean }) {
  const { user } = useStore()
  const token = localStorage.getItem('token')
  
  // 未初始化时跳转到设置页
  if (!initialized) {
    return <Navigate to="/setup" replace />
  }
  
  if (!token) {
    return <Navigate to="/admin/login" replace />
  }
  
  if (!user) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }
  
  return <>{children}</>
}

function App() {
  const { setUser, theme } = useStore()
  const [loading, setLoading] = useState(true)
  const [initialized, setInitialized] = useState(true)

  useEffect(() => {
    // 先检查系统是否已初始化
    setupApi.getStatus()
      .then((res: any) => {
        console.log('Setup status:', res)
        setInitialized(res.initialized)
        if (res.initialized) {
          // 已初始化，检查登录状态
          const token = localStorage.getItem('token')
          if (token) {
            return authApi.getMe()
              .then((res: any) => setUser(res))
              .catch(() => localStorage.removeItem('token'))
          }
        }
      })
      .catch((err) => {
        console.error('Failed to get setup status:', err)
        // 获取状态失败，假设已初始化
        setInitialized(true)
      })
      .finally(() => setLoading(false))
  }, [setUser])

  // 应用主题到 body
  useEffect(() => {
    document.body.setAttribute('data-theme', theme)
  }, [theme])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <ConfigProvider
      theme={{
        algorithm: theme === 'dark' ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm,
      }}
    >
    <BrowserRouter>
      <Routes>
        {/* 初始化设置页 */}
        <Route path="/setup" element={
          initialized ? <Navigate to="/" replace /> : <Setup />
        } />
        
        {/* 用户页面 */}
        <Route path="/" element={
          initialized ? <Home /> : <Navigate to="/setup" replace />
        } />
        <Route path="/callback" element={<Callback />} />
        <Route path="/invite/:code" element={<DirectInvite />} />
        
        {/* 管理员登录 */}
        <Route path="/admin/login" element={
          initialized ? <Login /> : <Navigate to="/setup" replace />
        } />
        
        {/* 管理后台 */}
        <Route path="/admin" element={
          <PrivateRoute initialized={initialized}>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="teams" element={<Teams />} />
          <Route path="teams/:id" element={<TeamDetail />} />
          <Route path="groups" element={<Groups />} />
          <Route path="invite" element={<Invite />} />
          <Route path="redeem-codes" element={<RedeemCodes />} />
          <Route path="direct-codes" element={<DirectCodes />} />
          <Route path="users" element={<LinuxDOUsers />} />
          <Route path="invite-records" element={<InviteRecords />} />
          <Route path="logs" element={<Logs />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
