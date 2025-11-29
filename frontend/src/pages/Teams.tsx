import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Button, Space, Tag, Modal, Form, Input, message, Select, Row, Col, Progress, Dropdown, Spin } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined, SafetyOutlined, MoreOutlined } from '@ant-design/icons'
import { teamApi, groupApi } from '../api'
import { useStore } from '../store'

const { TextArea } = Input

type Team = {
  id: number
  name: string
  description?: string
  account_id: string
  is_active: boolean
  member_count: number
  max_seats: number
  group_id?: number | null
  group_name?: string | null
  created_at: string
}

type Group = {
  id: number
  name: string
  color: string
}

export default function Teams() {
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTeam, setEditingTeam] = useState<Team | null>(null)
  const [syncing, setSyncing] = useState<number | null>(null)
  const [syncingAll, setSyncingAll] = useState(false)
  const [groups, setGroups] = useState<Group[]>([])
  const [form] = Form.useForm()
  const navigate = useNavigate()
  const { teams, setTeams } = useStore()
  const [filterGroupId, setFilterGroupId] = useState<number | undefined>(undefined)
  const [searchKeyword, setSearchKeyword] = useState('')

  const fetchTeams = async () => {
    setLoading(true)
    try {
      const res: any = await teamApi.list()
      setTeams(res.teams as Team[])
    } finally {
      setLoading(false)
    }
  }

  const fetchGroups = async () => {
    try {
      const res: any = await groupApi.list()
      setGroups(res)
    } catch {}
  }

  useEffect(() => { fetchTeams(); fetchGroups() }, [])

  const handleCreate = () => { setEditingTeam(null); form.resetFields(); setModalOpen(true) }
  const handleEdit = (team: Team, e: React.MouseEvent) => { 
    e.stopPropagation()
    setEditingTeam(team)
    form.setFieldsValue({ ...team, group_id: team.group_id })
    setModalOpen(true) 
  }
  const handleDelete = async (id: number) => { 
    Modal.confirm({
      title: '确定删除此 Team？',
      content: '删除后无法恢复',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        await teamApi.delete(id)
        message.success('删除成功')
        fetchTeams()
      }
    })
  }
  
  const handleVerify = async (id: number, e: React.MouseEvent) => { 
    e.stopPropagation()
    try { 
      await teamApi.verifyToken(id)
      message.success('Token 有效') 
    } catch {} 
  }
  
  const handleSync = async (id: number, e: React.MouseEvent) => { 
    e.stopPropagation()
    setSyncing(id)
    try { 
      const res: any = await teamApi.syncMembers(id)
      message.success(`同步成功，共 ${res.total} 人`)
      fetchTeams() 
    } catch {} 
    finally { setSyncing(null) }
  }

  const handleSyncAll = async () => {
    setSyncingAll(true)
    try {
      const res: any = await teamApi.syncAll()
      message.success(res.message)
      fetchTeams()
    } catch {}
    finally { setSyncingAll(false) }
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    try {
      if (editingTeam) {
        await teamApi.update(editingTeam.id, values)
        message.success('更新成功')
      } else {
        await teamApi.create(values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchTeams()
    } catch {}
  }

  const filteredTeams = [...teams]
    .filter(t => {
      const matchGroup = !filterGroupId || t.group_id === filterGroupId
      const matchSearch = !searchKeyword || t.name.toLowerCase().includes(searchKeyword.toLowerCase())
      return matchGroup && matchSearch
    })
    .sort((a, b) => {
      const usageA = (a.member_count || 0) / (a.max_seats || 5)
      const usageB = (b.member_count || 0) / (b.max_seats || 5)
      return usageB - usageA
    })

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>Team 座位管理</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>管理所有 ChatGPT Team 账号和座位使用情况</p>
        </div>
        <Space>
          <Button icon={<SyncOutlined spin={syncingAll} />} onClick={handleSyncAll} loading={syncingAll} size="large" style={{ borderRadius: 12, height: 44 }}>
            同步全部
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} size="large" style={{ borderRadius: 12, height: 44 }}>
            添加 Team
          </Button>
        </Space>
      </div>

      {/* 筛选栏 */}
      <Card size="small" style={{ marginBottom: 20 }}>
        <Space size="large">
          <Input.Search
            placeholder="搜索 Team 名称"
            allowClear
            style={{ width: 220 }}
            value={searchKeyword}
            onChange={e => setSearchKeyword(e.target.value)}
          />
          <Space>
            <span style={{ color: '#64748b' }}>分组：</span>
            <Select
              placeholder="全部分组"
              allowClear
              style={{ width: 160 }}
              value={filterGroupId}
              onChange={setFilterGroupId}
            >
              {groups.map(g => (
                <Select.Option key={g.id} value={g.id}>
                  <Space><div style={{ width: 10, height: 10, borderRadius: 2, background: g.color }} />{g.name}</Space>
                </Select.Option>
              ))}
            </Select>
          </Space>
          <span style={{ color: '#94a3b8' }}>共 {filteredTeams.length} 个 Team</span>
        </Space>
      </Card>

      {/* 座位卡片视图 */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" /></div>
      ) : filteredTeams.length === 0 ? (
        <Card>
          <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
            {teams.length === 0 ? '暂无 Team，点击右上角添加' : '没有匹配的 Team'}
          </div>
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {filteredTeams.map(team => {
            const memberCount = team.member_count || 0
            const maxSeats = team.max_seats || 5
            const usage = maxSeats > 0 ? Math.round((memberCount / maxSeats) * 100) : 0
            
            const menuItems = [
              { key: 'sync', label: '同步成员', icon: <SyncOutlined spin={syncing === team.id} />, onClick: (e: any) => handleSync(team.id, e.domEvent) },
              { key: 'verify', label: '验证 Token', icon: <SafetyOutlined />, onClick: (e: any) => handleVerify(team.id, e.domEvent) },
              { key: 'edit', label: '编辑', icon: <EditOutlined />, onClick: (e: any) => handleEdit(team, e.domEvent) },
              { type: 'divider' as const },
              { key: 'delete', label: '删除', icon: <DeleteOutlined />, danger: true, onClick: () => handleDelete(team.id) },
            ]
            
            return (
              <Col xs={12} sm={8} md={6} lg={4} key={team.id}>
                <Card
                  size="small"
                  hoverable
                  onClick={() => navigate(`/admin/teams/${team.id}`)}
                  style={{ 
                    borderRadius: 14,
                    border: usage >= 90 ? '2px solid rgba(239, 68, 68, 0.5)' : '1px solid rgba(0, 0, 0, 0.06)',
                  }}
                  styles={{ body: { padding: 16 } }}
                  extra={
                    <Dropdown 
                      menu={{ 
                        items: menuItems,
                        onClick: ({ key, domEvent }) => {
                          domEvent.stopPropagation()
                          if (key === 'delete') {
                            // 删除需要确认
                          }
                        }
                      }} 
                      trigger={['click']}
                    >
                      <Button type="text" size="small" icon={<MoreOutlined />} onClick={e => e.stopPropagation()} />
                    </Dropdown>
                  }
                >
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ fontWeight: 600, color: '#1a1a2e', fontSize: 15, marginBottom: 4 }}>{team.name}</div>
                    {team.group_name && (
                      <Tag color={groups.find(g => g.id === team.group_id)?.color} style={{ fontSize: 11 }}>
                        {team.group_name}
                      </Tag>
                    )}
                  </div>
                  <Progress 
                    percent={usage} 
                    strokeColor={usage >= 90 ? '#ef4444' : usage >= 70 ? '#f59e0b' : '#10b981'}
                    format={() => <span style={{ fontSize: 13, fontWeight: 600 }}>{memberCount}/{maxSeats}</span>}
                  />
                </Card>
              </Col>
            )
          })}
        </Row>
      )}

      <Modal 
        title={editingTeam ? '编辑 Team' : '添加 Team'} 
        open={modalOpen} 
        onOk={handleSubmit} 
        onCancel={() => setModalOpen(false)} 
        width={560} 
        okText="保存" 
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Form.Item name="name" label="Team 名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="如：研发部、市场部" size="large" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <TextArea rows={2} placeholder="Team 描述（可选）" />
          </Form.Item>
          <Form.Item name="group_id" label="所属分组" extra="选择分组后，该分组的邀请码只会分配到此 Team">
            <Select placeholder="选择分组（可选）" allowClear>
              {groups.map(g => (
                <Select.Option key={g.id} value={g.id}>
                  <Space><div style={{ width: 10, height: 10, borderRadius: 2, background: g.color }} />{g.name}</Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item 
            name="account_id" 
            label="Account ID" 
            rules={[{ required: true, message: '请输入 Account ID' }]} 
            extra="从 Network 请求 URL 中获取"
          >
            <Input placeholder="eabecad0-0c6a-4932-aeb4-4ad932280677" disabled={!!editingTeam} size="large" />
          </Form.Item>
          <Form.Item 
            name="session_token" 
            label="Session Token" 
            rules={[{ required: !editingTeam, message: '请输入 Token' }]} 
            extra="Headers 中 Authorization: Bearer 后面的内容"
          >
            <TextArea rows={2} placeholder="eyJhbGci..." />
          </Form.Item>
          <Form.Item 
            name="device_id" 
            label="Device ID" 
            rules={[{ required: !editingTeam, message: '请输入 Device ID' }]}
            extra="Headers 中 oai-device-id 的值"
          >
            <Input placeholder="0f404cce-2645-42e0-8163-80947354fad3" size="large" />
          </Form.Item>
          <Form.Item 
            name="max_seats" 
            label="最大座位数"
            extra="Team 的最大成员数量"
            initialValue={5}
          >
            <Input type="number" placeholder="5" size="large" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
