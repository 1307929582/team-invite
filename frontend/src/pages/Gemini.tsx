import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, message, Popconfirm, Tooltip, Tabs } from 'antd'
import { PlusOutlined, DeleteOutlined, SyncOutlined, UserAddOutlined, UserDeleteOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { geminiApi } from '../api'
import { formatDate } from '../utils/date'

interface GeminiTeam {
  id: number
  name: string
  description?: string
  account_id: string
  max_seats: number
  member_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

interface GeminiMember {
  id: number
  email: string
  role: string
  gemini_member_id?: number
  synced_at: string
}

interface InviteRecord {
  id: number
  email: string
  role: string
  status: string
  error_message?: string
  created_at: string
}

export default function Gemini() {
  const [teams, setTeams] = useState<GeminiTeam[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [selectedTeam, setSelectedTeam] = useState<GeminiTeam | null>(null)
  const [members, setMembers] = useState<GeminiMember[]>([])
  const [invites, setInvites] = useState<InviteRecord[]>([])
  const [membersLoading, setMembersLoading] = useState(false)
  const [inviteModalOpen, setInviteModalOpen] = useState(false)
  const [inviting, setInviting] = useState(false)
  const [form] = Form.useForm()
  const [inviteForm] = Form.useForm()

  const fetchTeams = async () => {
    setLoading(true)
    try {
      const res: any = await geminiApi.listTeams()
      setTeams(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchMembers = async (teamId: number) => {
    setMembersLoading(true)
    try {
      const [membersRes, invitesRes]: any = await Promise.all([
        geminiApi.getMembers(teamId),
        geminiApi.getInvites(teamId)
      ])
      setMembers(membersRes)
      setInvites(invitesRes)
    } finally {
      setMembersLoading(false)
    }
  }

  const handleSelectTeam = async (team: GeminiTeam) => {
    setSelectedTeam(team)
    await fetchMembers(team.id)
  }

  const handleCreate = async () => {
    const values = await form.validateFields()
    setCreating(true)
    try {
      await geminiApi.createTeam(values)
      message.success('创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchTeams()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '创建失败')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    await geminiApi.deleteTeam(id)
    message.success('删除成功')
    if (selectedTeam?.id === id) {
      setSelectedTeam(null)
      setMembers([])
    }
    fetchTeams()
  }

  const handleSync = async (teamId: number) => {
    try {
      const res: any = await geminiApi.syncTeam(teamId)
      message.success(`同步完成，共 ${res.member_count} 个成员`)
      if (selectedTeam?.id === teamId) {
        await fetchMembers(teamId)
      }
      fetchTeams()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '同步失败')
    }
  }

  const handleTest = async (teamId: number) => {
    try {
      const res: any = await geminiApi.testConnection(teamId)
      if (res.success) {
        message.success(`连接正常，共 ${res.member_count} 个成员`)
      } else {
        message.error(`连接失败: ${res.error}`)
      }
    } catch (e: any) {
      message.error(e.response?.data?.detail || '测试失败')
    }
  }

  const handleInvite = async () => {
    if (!selectedTeam) return
    const values = await inviteForm.validateFields()
    const emails = values.emails.split('\n').map((e: string) => e.trim()).filter((e: string) => e)
    
    if (emails.length === 0) {
      message.error('请输入邮箱')
      return
    }

    setInviting(true)
    try {
      const res: any = await geminiApi.inviteMembers(selectedTeam.id, emails, values.role)
      if (res.success.length > 0) {
        message.success(`成功邀请 ${res.success.length} 人`)
      }
      if (res.failed.length > 0) {
        message.warning(`${res.failed.length} 人邀请失败`)
      }
      setInviteModalOpen(false)
      inviteForm.resetFields()
      await fetchMembers(selectedTeam.id)
      fetchTeams()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '邀请失败')
    } finally {
      setInviting(false)
    }
  }

  const handleRemove = async (email: string) => {
    if (!selectedTeam) return
    try {
      await geminiApi.removeMember(selectedTeam.id, email)
      message.success('移除成功')
      await fetchMembers(selectedTeam.id)
      fetchTeams()
    } catch (e: any) {
      message.error(e.response?.data?.detail || '移除失败')
    }
  }

  const teamColumns = [
    { title: '名称', dataIndex: 'name', render: (v: string, r: GeminiTeam) => (
      <Button type="link" style={{ padding: 0 }} onClick={() => handleSelectTeam(r)}>{v}</Button>
    )},
    { title: '账户 ID', dataIndex: 'account_id', width: 140 },
    { title: '成员', dataIndex: 'member_count', width: 80, render: (v: number, r: GeminiTeam) => `${v}/${r.max_seats}` },
    { title: '状态', dataIndex: 'is_active', width: 80, render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '启用' : '禁用'}</Tag> },
    { title: '操作', width: 180, render: (_: any, r: GeminiTeam) => (
      <Space size={4}>
        <Tooltip title="同步成员"><Button size="small" type="text" icon={<SyncOutlined />} onClick={() => handleSync(r.id)} /></Tooltip>
        <Tooltip title="测试连接"><Button size="small" type="text" icon={<SafetyCertificateOutlined />} onClick={() => handleTest(r.id)} /></Tooltip>
        <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}>
          <Tooltip title="删除"><Button size="small" type="text" danger icon={<DeleteOutlined />} /></Tooltip>
        </Popconfirm>
      </Space>
    )}
  ]

  const memberColumns = [
    { title: '邮箱', dataIndex: 'email' },
    { title: '角色', dataIndex: 'role', width: 100, render: (v: string) => <Tag color={v === 'admin' ? 'blue' : 'default'}>{v}</Tag> },
    { title: '同步时间', dataIndex: 'synced_at', width: 160, render: (v: string) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    { title: '操作', width: 80, render: (_: any, r: GeminiMember) => (
      <Popconfirm title={`确定移除 ${r.email}？`} onConfirm={() => handleRemove(r.email)}>
        <Tooltip title="移除"><Button size="small" type="text" danger icon={<UserDeleteOutlined />} /></Tooltip>
      </Popconfirm>
    )}
  ]

  const inviteColumns = [
    { title: '邮箱', dataIndex: 'email' },
    { title: '角色', dataIndex: 'role', width: 80 },
    { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === 'success' ? 'green' : 'red'}>{v}</Tag> },
    { title: '时间', dataIndex: 'created_at', width: 160, render: (v: string) => formatDate(v, 'YYYY-MM-DD HH:mm') },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e' }}>Gemini Business 管理</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>管理 Gemini Business 团队成员</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setModalOpen(true) }} size="large" style={{ borderRadius: 12, height: 44 }}>
          添加 Team
        </Button>
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        {/* 左侧 Team 列表 */}
        <Card title="Team 列表" style={{ flex: 1 }} bodyStyle={{ padding: 0 }}>
          <Table dataSource={teams} columns={teamColumns} rowKey="id" loading={loading} pagination={false} size="small" />
        </Card>

        {/* 右侧成员详情 */}
        {selectedTeam && (
          <Card 
            title={`${selectedTeam.name} - 成员管理`} 
            style={{ flex: 1.5 }}
            extra={
              <Button type="primary" icon={<UserAddOutlined />} onClick={() => { inviteForm.resetFields(); setInviteModalOpen(true) }}>
                邀请成员
              </Button>
            }
          >
            <Tabs items={[
              {
                key: 'members',
                label: `成员 (${members.length})`,
                children: <Table dataSource={members} columns={memberColumns} rowKey="id" loading={membersLoading} pagination={false} size="small" />
              },
              {
                key: 'invites',
                label: `邀请记录 (${invites.length})`,
                children: <Table dataSource={invites} columns={inviteColumns} rowKey="id" loading={membersLoading} pagination={false} size="small" />
              }
            ]} />
          </Card>
        )}
      </div>

      {/* 创建 Team Modal */}
      <Modal title="添加 Gemini Team" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} okText="创建" cancelText="取消" confirmLoading={creating} width={520}>
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="如：Gemini Team 1" />
          </Form.Item>
          <Form.Item name="account_id" label="账户 ID" rules={[{ required: true }]} extra="在 business.gemini.google 后台 URL 中的 project 参数">
            <Input placeholder="如：393661537155" />
          </Form.Item>
          <Form.Item name="cookies" label="Cookies" rules={[{ required: true }]} extra="从浏览器复制完整的 Cookie 字符串">
            <Input.TextArea rows={4} placeholder="__Host-C_OSES=...; __Secure-C_SES=...; NID=..." />
          </Form.Item>
          <Form.Item name="max_seats" label="最大座位数" initialValue={10}>
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 邀请成员 Modal */}
      <Modal title="邀请成员" open={inviteModalOpen} onOk={handleInvite} onCancel={() => setInviteModalOpen(false)} okText="邀请" cancelText="取消" confirmLoading={inviting}>
        <Form form={inviteForm} layout="vertical" initialValues={{ role: 'viewer' }}>
          <Form.Item name="emails" label="邮箱列表" rules={[{ required: true }]} extra="每行一个邮箱">
            <Input.TextArea rows={6} placeholder="user1@example.com&#10;user2@example.com" />
          </Form.Item>
          <Form.Item name="role" label="角色">
            <Input placeholder="viewer 或 admin" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
