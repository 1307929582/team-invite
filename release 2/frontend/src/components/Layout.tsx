import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Avatar, Dropdown, Badge, Popover, List, Button, Empty, Tag } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  MailOutlined,
  FileTextOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GiftOutlined,
  SettingOutlined,
  AppstoreOutlined,
  UnorderedListOutlined,
  SunOutlined,
  MoonOutlined,
  BellOutlined,
  WarningOutlined,
  ExclamationCircleOutlined,
  CloseOutlined,
} from '@ant-design/icons'
import { useStore } from '../store'
import { teamApi } from '../api'
import { toLocalDate } from '../utils/date'
import dayjs from 'dayjs'

interface Warning {
  id: string
  type: 'error' | 'warning'
  message: string
  team?: string
  teamId?: number
}

const { Header, Sider, Content } = AntLayout

const menuItems = [
  { key: '/admin/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/admin/groups', icon: <AppstoreOutlined />, label: 'Team 分组' },
  { key: '/admin/teams', icon: <TeamOutlined />, label: 'Team 管理' },
  { key: '/admin/invite', icon: <MailOutlined />, label: '批量邀请' },
  { key: '/admin/redeem-codes', icon: <GiftOutlined />, label: 'LinuxDO 兑换码' },
  { key: '/admin/direct-codes', icon: <GiftOutlined />, label: '直接邀请链接' },
  { key: '/admin/invite-records', icon: <UnorderedListOutlined />, label: '邀请记录' },
  { key: '/admin/users', icon: <UserOutlined />, label: 'LinuxDO 用户' },
  { type: 'divider' as const },
  { key: '/admin/logs', icon: <FileTextOutlined />, label: '操作日志' },
  { key: '/admin/settings', icon: <SettingOutlined />, label: '系统设置' },
]

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [warnings, setWarnings] = useState<Warning[]>([])
  const [dismissedWarnings, setDismissedWarnings] = useState<string[]>(() => {
    const saved = localStorage.getItem('dismissedWarnings')
    return saved ? JSON.parse(saved) : []
  })
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout, theme, toggleTheme, teams, setTeams } = useStore()

  // 获取 Teams 并检查预警
  useEffect(() => {
    const fetchTeams = async () => {
      try {
        const res: any = await teamApi.list()
        setTeams(res.teams)
      } catch (e) {
        console.error('Failed to fetch teams:', e)
      }
    }
    fetchTeams()
  }, [setTeams])

  // 检查预警
  useEffect(() => {
    const memberLimit = 5
    const newWarnings: Warning[] = []
    
    teams.forEach(team => {
      // 超员预警
      if (team.member_count > memberLimit) {
        newWarnings.push({
          id: `overmember-${team.id}`,
          type: 'error',
          message: `成员超限！当前 ${team.member_count} 人，超过 ${memberLimit} 人限制，有封号风险！`,
          team: team.name,
          teamId: team.id,
        })
      } else if (team.member_count === memberLimit) {
        newWarnings.push({
          id: `atlimit-${team.id}`,
          type: 'warning',
          message: `成员已达上限 ${team.member_count} 人，请勿再邀请`,
          team: team.name,
          teamId: team.id,
        })
      }
      
      // Token 过期预警
      if (team.token_expires_at) {
        const expiresAt = toLocalDate(team.token_expires_at)
        const daysLeft = expiresAt ? expiresAt.diff(dayjs(), 'day') : 0
        if (daysLeft <= 0) {
          newWarnings.push({
            id: `token-expired-${team.id}`,
            type: 'error',
            message: 'Token 已过期',
            team: team.name,
            teamId: team.id,
          })
        } else if (daysLeft <= 7) {
          newWarnings.push({
            id: `token-expiring-${team.id}`,
            type: 'warning',
            message: `Token 将在 ${daysLeft} 天后过期`,
            team: team.name,
            teamId: team.id,
          })
        }
      }
    })
    
    setWarnings(newWarnings)
  }, [teams])

  // 过滤掉已消除的警告
  const activeWarnings = warnings.filter(w => !dismissedWarnings.includes(w.id))

  const dismissWarning = (id: string) => {
    const newDismissed = [...dismissedWarnings, id]
    setDismissedWarnings(newDismissed)
    localStorage.setItem('dismissedWarnings', JSON.stringify(newDismissed))
  }

  const dismissAllWarnings = () => {
    const allIds = warnings.map(w => w.id)
    setDismissedWarnings(allIds)
    localStorage.setItem('dismissedWarnings', JSON.stringify(allIds))
  }

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  const userMenu = {
    items: [
      { key: 'profile', icon: <UserOutlined />, label: user?.username, disabled: true },
      { type: 'divider' as const },
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout },
    ]
  }

  const siderWidth = collapsed ? 80 : 240

  return (
    <AntLayout style={{ minHeight: '100vh', background: 'transparent' }}>
      {/* 背景 */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'linear-gradient(135deg, #f0f4f8 0%, #e8eef5 50%, #f5f7fa 100%)',
        zIndex: -2,
      }} />
      {/* 装饰光晕 */}
      <div style={{
        position: 'fixed',
        top: '-20%',
        right: '-10%',
        width: 600,
        height: 600,
        background: 'radial-gradient(circle, rgba(147, 197, 253, 0.3) 0%, transparent 70%)',
        borderRadius: '50%',
        zIndex: -1,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'fixed',
        bottom: '-10%',
        left: '-5%',
        width: 500,
        height: 500,
        background: 'radial-gradient(circle, rgba(196, 181, 253, 0.25) 0%, transparent 70%)',
        borderRadius: '50%',
        zIndex: -1,
        pointerEvents: 'none',
      }} />

      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        width={240}
        collapsedWidth={80}
        style={{ 
          background: 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(40px)',
          WebkitBackdropFilter: 'blur(40px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.8)',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          boxShadow: '4px 0 24px rgba(0, 0, 0, 0.04)',
          overflow: 'hidden',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'flex-start',
          padding: collapsed ? '0' : '0 20px',
          borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
        }}>
          <div style={{ 
            width: 36, 
            height: 36, 
            borderRadius: 10,
            background: 'linear-gradient(135deg, #1a1a2e 0%, #2d2d44 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}>
            <span style={{ color: '#fff', fontWeight: 700, fontSize: 15 }}>Z</span>
          </div>
          {!collapsed && (
            <span style={{ fontSize: 16, fontWeight: 700, color: '#1a1a2e', letterSpacing: '-0.3px', marginLeft: 12 }}>
              TeamHub
            </span>
          )}
        </div>
        <div style={{ padding: '16px 0', overflow: 'hidden' }}>
          <Menu
            mode="inline"
            inlineCollapsed={collapsed}
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ border: 'none', background: 'transparent' }}
          />
        </div>
      </Sider>

      <AntLayout style={{ marginLeft: siderWidth, transition: 'margin-left 0.2s', background: 'transparent' }}>
        <Header style={{
          padding: '0 20px',
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(40px)',
          WebkitBackdropFilter: 'blur(40px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.8)',
          height: 64,
          position: 'sticky',
          top: 0,
          zIndex: 99,
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.03)',
          overflow: 'hidden',
        }}>
          <div 
            onClick={() => setCollapsed(!collapsed)} 
            style={{ 
              cursor: 'pointer', 
              color: '#64748b',
              width: 32,
              height: 32,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 6,
              transition: 'all 0.2s',
              flexShrink: 0,
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'rgba(0, 0, 0, 0.04)'
              e.currentTarget.style.color = '#1a1a2e'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'transparent'
              e.currentTarget.style.color = '#64748b'
            }}
          >
            {collapsed ? <MenuUnfoldOutlined style={{ fontSize: 15 }} /> : <MenuFoldOutlined style={{ fontSize: 15 }} />}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* 预警按钮 */}
            <Popover
              placement="bottomRight"
              trigger="click"
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>系统预警</span>
                  {activeWarnings.length > 0 && (
                    <Button type="link" size="small" onClick={dismissAllWarnings} style={{ padding: 0 }}>
                      全部已读
                    </Button>
                  )}
                </div>
              }
              content={
                <div style={{ width: 320, maxHeight: 400, overflow: 'auto' }}>
                  {activeWarnings.length === 0 ? (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无预警" />
                  ) : (
                    <List
                      size="small"
                      dataSource={activeWarnings}
                      renderItem={item => (
                        <List.Item
                          style={{ 
                            padding: '12px 0',
                            background: item.type === 'error' ? 'rgba(239, 68, 68, 0.05)' : 'rgba(245, 158, 11, 0.05)',
                            borderRadius: 8,
                            marginBottom: 8,
                            paddingLeft: 12,
                            paddingRight: 8,
                          }}
                          actions={[
                            <Button 
                              type="text" 
                              size="small" 
                              icon={<CloseOutlined />}
                              onClick={() => dismissWarning(item.id)}
                              style={{ color: '#94a3b8' }}
                            />
                          ]}
                        >
                          <List.Item.Meta
                            avatar={
                              item.type === 'error' 
                                ? <ExclamationCircleOutlined style={{ color: '#ef4444', fontSize: 18 }} />
                                : <WarningOutlined style={{ color: '#f59e0b', fontSize: 18 }} />
                            }
                            title={
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Tag color={item.type === 'error' ? 'red' : 'orange'} style={{ margin: 0 }}>
                                  {item.team}
                                </Tag>
                              </div>
                            }
                            description={
                              <span 
                                style={{ fontSize: 13, color: '#64748b', cursor: 'pointer' }}
                                onClick={() => item.teamId && navigate(`/admin/teams/${item.teamId}`)}
                              >
                                {item.message}
                              </span>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  )}
                </div>
              }
            >
              <Badge count={activeWarnings.length} size="small" offset={[-2, 2]}>
                <div 
                  style={{ 
                    cursor: 'pointer', 
                    color: activeWarnings.length > 0 ? '#f59e0b' : '#64748b',
                    width: 32,
                    height: 32,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 6,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(0, 0, 0, 0.04)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'transparent'
                  }}
                >
                  <BellOutlined style={{ fontSize: 16 }} />
                </div>
              </Badge>
            </Popover>

            <div 
              onClick={toggleTheme}
              style={{ 
                cursor: 'pointer', 
                color: '#64748b',
                width: 32,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: 6,
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(0, 0, 0, 0.04)'
                e.currentTarget.style.color = '#1a1a2e'
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'transparent'
                e.currentTarget.style.color = '#64748b'
              }}
            >
              {theme === 'light' ? <MoonOutlined style={{ fontSize: 15 }} /> : <SunOutlined style={{ fontSize: 15 }} />}
            </div>
            <Dropdown menu={userMenu} placement="bottomRight">
              <div style={{ 
                cursor: 'pointer', 
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '4px 10px 4px 4px', 
                borderRadius: 20, 
                transition: 'all 0.2s',
                background: 'rgba(0, 0, 0, 0.03)',
                flexShrink: 0,
              }}>
                <Avatar size={26} icon={<UserOutlined />} />
                <span style={{ color: '#1a1a2e', fontSize: 13, fontWeight: 500 }}>{user?.username}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content style={{ 
          margin: 24, 
          padding: 24, 
          background: 'rgba(255, 255, 255, 0.7)',
          backdropFilter: 'blur(40px)',
          WebkitBackdropFilter: 'blur(40px)',
          borderRadius: 20,
          border: '1px solid rgba(255, 255, 255, 0.9)',
          minHeight: 'calc(100vh - 112px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
        }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
