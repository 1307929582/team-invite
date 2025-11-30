import { useNavigate } from 'react-router-dom'
import { Card, Row, Col } from 'antd'
import {
  GlobalOutlined,
  MailOutlined,
  BellOutlined,
  SafetyOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const settingModules = [
  {
    key: 'oauth',
    title: 'LinuxDO OAuth',
    description: '配置 LinuxDO 登录授权',
    icon: <SafetyOutlined style={{ fontSize: 28, color: '#3b82f6' }} />,
    path: '/admin/settings/oauth',
  },
  {
    key: 'site',
    title: '站点配置',
    description: '自定义站点标题、描述、公告等',
    icon: <GlobalOutlined style={{ fontSize: 28, color: '#10b981' }} />,
    path: '/admin/settings/site',
  },
  {
    key: 'email',
    title: '邮件通知',
    description: '配置 SMTP 和预警通知',
    icon: <MailOutlined style={{ fontSize: 28, color: '#f59e0b' }} />,
    path: '/admin/settings/email',
  },
  {
    key: 'telegram',
    title: 'Telegram 通知',
    description: '配置 Telegram Bot 推送',
    icon: <BellOutlined style={{ fontSize: 28, color: '#0088cc' }} />,
    path: '/admin/settings/telegram',
  },
  {
    key: 'alerts',
    title: '预警设置',
    description: '配置预警阈值和规则',
    icon: <BellOutlined style={{ fontSize: 28, color: '#ef4444' }} />,
    path: '/admin/settings/alerts',
  },
]

export default function Settings() {
  const navigate = useNavigate()

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>
          <SettingOutlined style={{ marginRight: 12 }} />
          系统设置
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>管理系统配置和通知设置</p>
      </div>

      <Row gutter={[20, 20]}>
        {settingModules.map(module => (
          <Col xs={24} sm={12} lg={6} key={module.key}>
            <Card
              hoverable
              onClick={() => navigate(module.path)}
              style={{
                borderRadius: 16,
                cursor: 'pointer',
                height: '100%',
                transition: 'all 0.3s',
              }}
              bodyStyle={{ padding: 24 }}
            >
              <div style={{ marginBottom: 16 }}>{module.icon}</div>
              <h3 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 8px', color: '#1a1a2e' }}>
                {module.title}
              </h3>
              <p style={{ color: '#64748b', fontSize: 13, margin: 0 }}>
                {module.description}
              </p>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}
