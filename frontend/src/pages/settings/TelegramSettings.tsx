import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Switch, Divider, Alert } from 'antd'
import { ArrowLeftOutlined, SendOutlined, RobotOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { configApi } from '../../api'

export default function TelegramSettings() {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [settingWebhook, setSettingWebhook] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetchConfigs()
  }, [])

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const res: any = await configApi.list()
      const configs: Record<string, string> = {}
      res.configs.forEach((c: any) => {
        configs[c.key] = c.value || ''
      })
      form.setFieldsValue({
        telegram_bot_token: configs.telegram_bot_token,
        telegram_chat_id: configs.telegram_chat_id,
        telegram_enabled: configs.telegram_enabled === 'true',
        telegram_notify_invite: configs.telegram_notify_invite === 'true',
        telegram_notify_alert: configs.telegram_notify_alert === 'true',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    const values = await form.validateFields()
    setSaving(true)
    try {
      await configApi.batchUpdate([
        { key: 'telegram_bot_token', value: values.telegram_bot_token || '' },
        { key: 'telegram_chat_id', value: values.telegram_chat_id || '' },
        { key: 'telegram_enabled', value: values.telegram_enabled ? 'true' : 'false' },
        { key: 'telegram_notify_invite', value: values.telegram_notify_invite ? 'true' : 'false' },
        { key: 'telegram_notify_alert', value: values.telegram_notify_alert ? 'true' : 'false' },
      ])
      message.success('保存成功')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      await configApi.testTelegram()
      message.success('测试消息已发送，请检查 Telegram')
    } catch (e: any) {
      message.error(e.response?.data?.detail || '发送失败')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <Button 
          type="text" 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/admin/settings')}
          style={{ marginBottom: 12, padding: '4px 0' }}
        >
          返回设置
        </Button>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e' }}>
          <SendOutlined style={{ marginRight: 12, color: '#0088cc' }} />
          Telegram 通知
        </h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>
          配置 Telegram Bot 接收系统通知
        </p>
      </div>

      <Card loading={loading} style={{ maxWidth: 600 }}>
        <Alert
          message="如何获取 Bot Token 和 Chat ID？"
          description={
            <ol style={{ paddingLeft: 20, margin: '8px 0 0' }}>
              <li>在 Telegram 搜索 @BotFather，发送 /newbot 创建机器人</li>
              <li>按提示设置名称，获取 Bot Token</li>
              <li>搜索 @userinfobot，发送任意消息获取你的 Chat ID</li>
              <li>如果要发到群组，先把机器人加入群组，然后获取群组 ID</li>
            </ol>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form form={form} layout="vertical">
          <Form.Item 
            name="telegram_bot_token" 
            label="Bot Token"
            extra="从 @BotFather 获取"
          >
            <Input.Password placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz" />
          </Form.Item>

          <Form.Item 
            name="telegram_chat_id" 
            label="Chat ID"
            extra="个人 ID 或群组 ID（群组 ID 以 - 开头）"
          >
            <Input placeholder="123456789 或 -100123456789" />
          </Form.Item>

          <Divider />

          <Form.Item 
            name="telegram_enabled" 
            label="启用 Telegram 通知" 
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item 
            name="telegram_notify_invite" 
            label="新用户上车时通知" 
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Form.Item 
            name="telegram_notify_alert" 
            label="座位预警时通知" 
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>

          <Divider />

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Button type="primary" onClick={handleSave} loading={saving}>
              保存配置
            </Button>
            <Button onClick={handleTest} loading={testing}>
              发送测试消息
            </Button>
          </div>
        </Form>
      </Card>

      {/* Bot 命令功能 */}
      <Card style={{ maxWidth: 600, marginTop: 20 }}>
        <h3 style={{ margin: '0 0 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ color: '#0088cc' }} />
          Telegram Bot 命令
        </h3>
        <Alert
          message="启用 Bot 命令功能"
          description={
            <div>
              <p style={{ margin: '8px 0' }}>设置 Webhook 后，可以在 Telegram 中使用以下命令管理系统：</p>
              <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                <li><code>/status</code> - 查看系统状态</li>
                <li><code>/seats</code> - 座位统计</li>
                <li><code>/teams</code> - Team 列表</li>
                <li><code>/alerts</code> - 查看预警</li>
                <li><code>/sync</code> - 同步所有成员</li>
                <li><code>/code 5</code> - 生成 5 个兑换码</li>
                <li><code>/dcode 5</code> - 生成 5 个直接链接</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Button 
          icon={<RobotOutlined />}
          loading={settingWebhook}
          onClick={async () => {
            setSettingWebhook(true)
            try {
              await configApi.setupTelegramWebhook()
              message.success('Webhook 设置成功！现在可以在 Telegram 中使用命令了')
            } catch (e: any) {
              message.error(e.response?.data?.detail || '设置失败')
            } finally {
              setSettingWebhook(false)
            }
          }}
        >
          设置 Webhook
        </Button>
        <p style={{ color: '#64748b', fontSize: 12, marginTop: 8 }}>
          注意：需要先在「站点配置」中设置正确的站点 URL
        </p>
      </Card>
    </div>
  )
}
