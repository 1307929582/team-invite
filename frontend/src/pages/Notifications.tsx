import { useEffect, useState } from 'react'
import { Card, Form, Switch, InputNumber, Button, message, Divider, Alert, Space, Spin, Tag, Tooltip } from 'antd'
import { 
  SaveOutlined, 
  MailOutlined, 
  SendOutlined, 
  BellOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  KeyOutlined
} from '@ant-design/icons'
import { notificationApi } from '../api'

export default function Notifications() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savingSmtp, setSavingSmtp] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testingSend, setTestingSend] = useState(false)
  const [emailConfigured, setEmailConfigured] = useState(false)
  const [settingsForm] = Form.useForm()
  const [smtpForm] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const [settingsRes, smtpRes]: any = await Promise.all([
        notificationApi.getSettings(),
        notificationApi.getSmtp()
      ])
      
      settingsForm.setFieldsValue(settingsRes.settings)
      smtpForm.setFieldsValue(smtpRes)
      setEmailConfigured(smtpRes.configured)
    } catch (e: any) {
      message.error('获取配置失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleSaveSettings = async () => {
    const values = await settingsForm.validateFields()
    setSaving(true)
    try {
      await notificationApi.updateSettings(values)
      message.success('通知设置已保存')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveSmtp = async () => {
    const values = await smtpForm.validateFields()
    setSavingSmtp(true)
    try {
      await notificationApi.updateSmtp(values)
      message.success('SMTP 配置已保存')
      setEmailConfigured(true)
    } catch (e: any) {
      message.error(e.response?.data?.detail || '保存失败')
    } finally {
      setSavingSmtp(false)
    }
  }

  const handleTestConnection = async () => {
    setTesting(true)
    try {
      await notificationApi.testConnection()
      message.success('SMTP 连接成功')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '连接失败')
    } finally {
      setTesting(false)
    }
  }

  const handleTestSend = async () => {
    setTestingSend(true)
    try {
      await notificationApi.testSend()
      message.success('测试邮件已发送，请检查收件箱')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '发送失败')
    } finally {
      setTestingSend(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>
          <BellOutlined style={{ marginRight: 12 }} />
          通知设置
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>
          配置邮件通知，接收 Token 过期、座位预警等提醒
        </p>
      </div>

      {/* SMTP 配置 */}
      <Card 
        title={
          <Space>
            <MailOutlined />
            <span>SMTP 邮件配置</span>
            {emailConfigured ? (
              <Tag color="success" icon={<CheckCircleOutlined />}>已配置</Tag>
            ) : (
              <Tag color="warning" icon={<CloseCircleOutlined />}>未配置</Tag>
            )}
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Alert
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 20 }}
          message="SMTP 配置说明"
          description={
            <div style={{ fontSize: 13 }}>
              <p style={{ margin: '4px 0' }}>• Gmail: smtp.gmail.com 端口 587，需要开启两步验证并生成应用专用密码</p>
              <p style={{ margin: '4px 0' }}>• Outlook: smtp.office365.com 端口 587</p>
              <p style={{ margin: '4px 0' }}>• QQ邮箱: smtp.qq.com 端口 587，需要开启 SMTP 服务并获取授权码</p>
              <p style={{ margin: '4px 0' }}>• 163邮箱: smtp.163.com 端口 465 (SSL)</p>
            </div>
          }
        />

        <Form form={smtpForm} layout="vertical">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item 
              name="smtp_host" 
              label="SMTP 服务器"
              rules={[{ required: true, message: '请输入 SMTP 服务器' }]}
            >
              <input 
                className="ant-input ant-input-lg"
                placeholder="smtp.gmail.com" 
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8 }}
              />
            </Form.Item>

            <Form.Item 
              name="smtp_port" 
              label="端口"
              rules={[{ required: true, message: '请输入端口' }]}
            >
              <InputNumber 
                placeholder="587" 
                style={{ width: '100%' }}
                size="large"
                min={1}
                max={65535}
              />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item 
              name="smtp_user" 
              label="发件邮箱"
              rules={[{ required: true, message: '请输入发件邮箱' }]}
            >
              <input 
                className="ant-input ant-input-lg"
                placeholder="your-email@gmail.com" 
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8 }}
              />
            </Form.Item>

            <Form.Item 
              name="smtp_password" 
              label="应用密码"
              rules={[{ required: true, message: '请输入应用密码' }]}
            >
              <input 
                type="password"
                className="ant-input ant-input-lg"
                placeholder="应用专用密码" 
                style={{ width: '100%', padding: '8px 12px', borderRadius: 8 }}
              />
            </Form.Item>
          </div>

          <Form.Item 
            name="admin_email" 
            label="接收通知邮箱"
            rules={[{ required: true, message: '请输入接收邮箱' }]}
            extra="预警通知将发送到此邮箱"
          >
            <input 
              className="ant-input ant-input-lg"
              placeholder="admin@example.com" 
              style={{ width: '100%', padding: '8px 12px', borderRadius: 8 }}
            />
          </Form.Item>

          <Space size="middle">
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              loading={savingSmtp}
              onClick={handleSaveSmtp}
              style={{ borderRadius: 8 }}
            >
              保存配置
            </Button>
            <Button 
              icon={<CheckCircleOutlined />} 
              loading={testing}
              onClick={handleTestConnection}
              style={{ borderRadius: 8 }}
              disabled={!emailConfigured}
            >
              测试连接
            </Button>
            <Button 
              icon={<SendOutlined />} 
              loading={testingSend}
              onClick={handleTestSend}
              style={{ borderRadius: 8 }}
              disabled={!emailConfigured}
            >
              发送测试邮件
            </Button>
          </Space>
        </Form>
      </Card>

      {/* 通知设置 */}
      <Card 
        title={
          <Space>
            <BellOutlined />
            <span>通知规则设置</span>
          </Space>
        }
      >
        {!emailConfigured && (
          <Alert
            type="warning"
            showIcon
            style={{ marginBottom: 20 }}
            message="请先配置 SMTP 邮件服务"
            description="配置完成后才能启用邮件通知功能"
          />
        )}

        <Form form={settingsForm} layout="vertical">
          <Form.Item 
            name="enabled" 
            label={
              <Space>
                <span style={{ fontWeight: 600, fontSize: 15 }}>启用邮件通知</span>
                <Tooltip title="开启后将根据下方规则发送邮件通知">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              </Space>
            }
            valuePropName="checked"
          >
            <Switch 
              checkedChildren="开启" 
              unCheckedChildren="关闭" 
              disabled={!emailConfigured}
            />
          </Form.Item>

          <Divider orientation="left">
            <Space>
              <KeyOutlined />
              Token 过期提醒
            </Space>
          </Divider>

          <Form.Item 
            name="token_expiring_days" 
            label="提前提醒天数"
            extra="Token 剩余天数少于此值时发送提醒"
          >
            <InputNumber 
              min={1} 
              max={30} 
              style={{ width: 200 }}
              addonAfter="天"
              disabled={!emailConfigured}
            />
          </Form.Item>

          <Divider orientation="left">
            <Space>
              <TeamOutlined />
              座位容量预警
            </Space>
          </Divider>

          <Form.Item 
            name="seat_warning_threshold" 
            label="预警阈值"
            extra="座位使用率超过此百分比时发送预警"
          >
            <InputNumber 
              min={50} 
              max={100} 
              style={{ width: 200 }}
              addonAfter="%"
              disabled={!emailConfigured}
            />
          </Form.Item>

          <Divider orientation="left">
            <Space>
              <MailOutlined />
              邀请通知
            </Space>
          </Divider>

          <Form.Item 
            name="notify_new_invite" 
            label="新邀请发送通知"
            valuePropName="checked"
            extra="发送邀请后通知管理员"
          >
            <Switch disabled={!emailConfigured} />
          </Form.Item>

          <Form.Item 
            name="notify_invite_accepted" 
            label="邀请接受通知"
            valuePropName="checked"
            extra="用户接受邀请后通知管理员"
          >
            <Switch disabled={!emailConfigured} />
          </Form.Item>

          <Divider orientation="left">
            <Space>
              <ClockCircleOutlined />
              每日报告
            </Space>
          </Divider>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item 
              name="daily_report_enabled" 
              label="启用每日报告"
              valuePropName="checked"
              extra="每天发送数据统计报告"
            >
              <Switch disabled={!emailConfigured} />
            </Form.Item>

            <Form.Item 
              name="daily_report_hour" 
              label="发送时间"
              extra="每天几点发送报告"
            >
              <InputNumber 
                min={0} 
                max={23} 
                style={{ width: 200 }}
                addonAfter="点"
                disabled={!emailConfigured}
              />
            </Form.Item>
          </div>

          <Divider />

          <Button 
            type="primary" 
            icon={<SaveOutlined />} 
            size="large"
            loading={saving}
            onClick={handleSaveSettings}
            style={{ borderRadius: 10 }}
            disabled={!emailConfigured}
          >
            保存通知设置
          </Button>
        </Form>
      </Card>
    </div>
  )
}
