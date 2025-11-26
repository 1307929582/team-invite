import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Divider, Alert, Switch, Space } from 'antd'
import { SaveOutlined, MailOutlined, SendOutlined, BellOutlined } from '@ant-design/icons'
import { configApi } from '../api'

interface ConfigItem {
  key: string
  value: string
  description: string
}

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testingEmail, setTestingEmail] = useState(false)
  const [checkingAlerts, setCheckingAlerts] = useState(false)
  const [form] = Form.useForm()

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const res: any = await configApi.list()
      const values: Record<string, string> = {}
      res.configs.forEach((c: ConfigItem) => {
        values[c.key] = c.value || ''
      })
      form.setFieldsValue(values)
    } catch (e: any) {
      console.error('Fetch config error:', e)
      message.error('获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      const configs = Object.entries(values)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => ({
          key,
          value: typeof value === 'boolean' ? (value ? 'true' : 'false') : String(value || ''),
          description: null,
        }))
      console.log('Saving configs:', configs)
      await configApi.batchUpdate(configs)
      message.success('配置已保存')
    } catch (e: any) {
      console.error('Save config error:', e)
      const detail = e.response?.data?.detail
      if (Array.isArray(detail)) {
        message.error(detail.map((d: any) => d.msg).join(', '))
      } else {
        message.error(detail || '保存失败，请重试')
      }
    } finally {
      setSaving(false)
    }
  }

  const handleTestEmail = async () => {
    setTestingEmail(true)
    try {
      await configApi.testEmail()
      message.success('测试邮件已发送，请检查收件箱')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '发送失败，请检查 SMTP 配置')
    } finally {
      setTestingEmail(false)
    }
  }

  const handleCheckAlerts = async () => {
    setCheckingAlerts(true)
    try {
      const res: any = await configApi.checkAlerts()
      if (res.alerts?.length > 0) {
        message.warning(`发现 ${res.alerts.length} 个预警，已发送邮件通知`)
      } else {
        message.success('检查完成，暂无预警')
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '检查失败')
    } finally {
      setCheckingAlerts(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>系统设置</h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>配置 LinuxDO OAuth 等系统参数</p>
      </div>

      <Card loading={loading}>
        <Form form={form} layout="vertical">
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>LinuxDO OAuth 配置</h3>
          
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 20 }}
            message="配置说明"
            description={
              <div>
                <p>1. 访问 <a href="https://connect.linux.do" target="_blank" rel="noreferrer">connect.linux.do</a> 创建 OAuth 应用</p>
                <p>2. 回调地址填写：<code>http://你的域名/callback</code></p>
                <p>3. 将获取的 Client ID 和 Client Secret 填入下方</p>
              </div>
            }
          />

          <Form.Item 
            name="linuxdo_client_id" 
            label="Client ID"
            extra="LinuxDO OAuth 应用的 Client ID"
          >
            <Input placeholder="输入 Client ID" size="large" />
          </Form.Item>

          <Form.Item 
            name="linuxdo_client_secret" 
            label="Client Secret"
            extra="LinuxDO OAuth 应用的 Client Secret（已保存的不会显示）"
          >
            <Input.Password placeholder="输入 Client Secret" size="large" />
          </Form.Item>

          <Form.Item 
            name="linuxdo_redirect_uri" 
            label="回调地址"
            extra="OAuth 授权后的回调地址，如 http://localhost:5173/callback"
          >
            <Input placeholder="http://localhost:5173/callback" size="large" />
          </Form.Item>

          <Divider />

          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>站点配置</h3>

          <Form.Item 
            name="site_title" 
            label="站点标题"
          >
            <Input placeholder="ChatGPT Team 自助上车" size="large" />
          </Form.Item>

          <Form.Item 
            name="site_description" 
            label="站点描述"
          >
            <Input placeholder="使用兑换码加入 ChatGPT Team" size="large" />
          </Form.Item>

          <Form.Item 
            name="min_trust_level" 
            label="最低信任等级"
            extra="LinuxDO 用户需要达到的最低信任等级才能使用（0-4）"
          >
            <Input placeholder="0" size="large" type="number" />
          </Form.Item>

          <Divider />

          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
            <MailOutlined style={{ marginRight: 8 }} />
            邮件通知配置
          </h3>

          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 20 }}
            message="SMTP 配置说明"
            description={
              <div>
                <p>配置 SMTP 后可接收超员预警、Token 过期提醒等通知</p>
                <p>常用配置：Gmail smtp.gmail.com:587 | Outlook smtp.office365.com:587</p>
              </div>
            }
          />

          <Form.Item 
            name="email_enabled" 
            label="启用邮件通知"
            valuePropName="checked"
            getValueFromEvent={(checked) => checked}
            getValueProps={(value) => ({ checked: value === 'true' || value === true })}
          >
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>

          <Form.Item 
            name="smtp_host" 
            label="SMTP 服务器"
            extra="如 smtp.gmail.com、smtp.office365.com"
          >
            <Input placeholder="smtp.gmail.com" size="large" />
          </Form.Item>

          <Form.Item 
            name="smtp_port" 
            label="SMTP 端口"
            extra="Gmail/Outlook 使用 587 (TLS)，SSL 使用 465"
          >
            <Input placeholder="587" size="large" type="number" />
          </Form.Item>

          <Form.Item 
            name="smtp_user" 
            label="发件邮箱"
          >
            <Input placeholder="your-email@gmail.com" size="large" />
          </Form.Item>

          <Form.Item 
            name="smtp_password" 
            label="邮箱应用密码"
            extra="Gmail 需要在 Google 账户中生成应用专用密码"
          >
            <Input.Password placeholder="应用专用密码（非登录密码）" size="large" />
          </Form.Item>

          <Form.Item 
            name="admin_email" 
            label="管理员邮箱"
            extra="接收预警通知的邮箱地址"
          >
            <Input placeholder="admin@example.com" size="large" />
          </Form.Item>

          <Divider />

          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
            <BellOutlined style={{ marginRight: 8 }} />
            预警阈值设置
          </h3>

          <Form.Item 
            name="alert_member_threshold" 
            label="超员预警阈值"
            extra="Team 成员超过此数量时发送预警（建议设为 5，避免封号）"
          >
            <Input placeholder="5" size="large" type="number" />
          </Form.Item>

          <Form.Item 
            name="alert_token_days" 
            label="Token 过期预警天数"
            extra="Token 剩余天数少于此值时发送预警"
          >
            <Input placeholder="7" size="large" type="number" />
          </Form.Item>

          <Divider />

          <Space size="middle">
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              size="large"
              loading={saving}
              onClick={handleSave}
              style={{ borderRadius: 10 }}
            >
              保存配置
            </Button>
            <Button 
              icon={<SendOutlined />} 
              size="large"
              loading={testingEmail}
              onClick={handleTestEmail}
              style={{ borderRadius: 10 }}
            >
              发送测试邮件
            </Button>
            <Button 
              icon={<BellOutlined />} 
              size="large"
              loading={checkingAlerts}
              onClick={handleCheckAlerts}
              style={{ borderRadius: 10 }}
            >
              立即检查预警
            </Button>
          </Space>
        </Form>
      </Card>
    </div>
  )
}
