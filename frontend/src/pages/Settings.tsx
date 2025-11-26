import { useEffect, useState } from 'react'
import { Card, Form, Input, Button, message, Divider, Alert } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { configApi } from '../api'

interface ConfigItem {
  key: string
  value: string
  description: string
}

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
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
          value: String(value || ''),
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
        </Form>
      </Card>
    </div>
  )
}
