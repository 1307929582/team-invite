import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, message, Popconfirm, Tooltip, Select, Row, Col, Progress } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SyncOutlined, SafetyOutlined, EyeOutlined } from '@ant-design/icons'
import { teamApi, groupApi } from '../api'
import { useStore } from '../store'
import { formatDate } from '../utils/date'

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
  const handleEdit = (team: Team) => { setEditingTeam(team); form.setFieldsValue({ ...team, group_id: team.group_id }); setModalOpen(true) }
  const handleDelete = async (id: number) => { await teamApi.delete(id); message.success('删除成功'); fetchTeams() }
  
  const handleVerify = async (id: number) => { 
    try { 
      await teamApi.verifyToken(id)
      message.success('Token 有效') 
    } catch {} 
  }
  
  const handleSync = async (id: number) => { 
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

  const columns = [
    { 
      title: 'Team 名称', 
      dataIndex: 'name', 
      render: (v: string, r: Team) => (
        <a onClick={() => navigate(`/admin/teams/${r.id}`)} style={{ fontWeight: 600, color: '#1a1a2e' }}>{v}</a>
      )
    },
    {
      title: '分组',
      dataIndex: 'group_name',
      width: 100,
      render: (v: string, r: Team) => v ? (
        <Tag color={groups.find(g => g.id === r.group_id)?.color}>{v}</Tag>
      ) : <span style={{ color: '#94a3b8' }}>未分组</span>
    },
    { 
      title: 'Account ID', 
      dataIndex: 'account_id', 
      width: 140, 
      render: (v: string) => (
        <Tooltip title={v}>
          <code style={{ cursor: 'pointer' }}>{v?.slice(0, 10)}...</code>
        </Tooltip>
      )
    },
    { 
      title: '成员', 
      dataIndex: 'member_count', 
      width: 80, 
      render: (v: number) => <Tag color="blue">{v} 人</Tag>
    },
    { 
      title: '状态', 
      dataIndex: 'is_active', 
      width: 80, 
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '正常' : '禁用'}</Tag>
    },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      width: 150, 
      render: (v: string) => <span style={{ color: '#64748b', fontSize: 13 }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span>
    },
    {
      title: '操作', 
      width: 180,
      render: (_: any, r: Team) => (
        <Space size={4}>
          <Tooltip title="查看详情">
            <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => navigate(`/admin/teams/${r.id}`)} />
          </Tooltip>
          <Tooltip title="同步成员">
            <Button size="small" type="text" icon={<SyncOutlined spin={syncing === r.id} />} onClick={() => handleSync(r.id)} loading={syncing === r.id} />
          </Tooltip>
          <Tooltip title="验证 Token">
            <Button size="small" type="text" icon={<SafetyOutlined />} onClick={() => handleVerify(r.id)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button size="small" type="text" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          </Tooltip>
          <Popconfirm title="确定删除此 Team？" onConfirm={() => handleDelete(r.id)} okText="删除" cancelText="取消">
            <Tooltip title="删除">
              <Button size="small" type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
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

      {/* 座位卡片视图 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        {[...teams]
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
          .map(team => {
            const memberCount = team.member_count || 0
            const maxSeats = team.max_seats || 5
            const usage = maxSeats > 0 ? Math.round((memberCount / maxSeats) * 100) : 0
            return (
              <Col xs={12} sm={8} md={6} lg={4} key={team.id}>
                <div 
                  onClick={() => navigate(`/admin/teams/${team.id}`)}
                  style={{ 
                    padding: 16, 
                    background: 'rgba(255, 255, 255, 0.7)', 
                    borderRadius: 14, 
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    border: usage >= 90 ? '2px solid rgba(239, 68, 68, 0.5)' : '1px solid rgba(0, 0, 0, 0.06)',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.04)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.04)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontWeight: 600, color: '#1a1a2e', fontSize: 14 }}>{team.name}</span>
                    {team.group_name && (
                      <Tag color={groups.find(g => g.id === team.group_id)?.color} style={{ margin: 0, fontSize: 11 }}>
                        {team.group_name}
                      </Tag>
                    )}
                  </div>
                  <Progress 
                    percent={usage} 
                    size="small" 
                    strokeColor={usage >= 90 ? '#ef4444' : usage >= 70 ? '#f59e0b' : '#10b981'}
                    format={() => `${memberCount}/${maxSeats}`}
                  />
                </div>
              </Col>
            )
          })}
      </Row>

      <Card bodyStyle={{ padding: 0 }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Space size="large">
            <Input.Search
              placeholder="搜索 Team 名称"
              allowClear
              style={{ width: 200 }}
              value={searchKeyword}
              onChange={e => setSearchKeyword(e.target.value)}
            />
            <Space>
              <span style={{ color: '#64748b' }}>分组：</span>
              <Select
                placeholder="全部分组"
                allowClear
                style={{ width: 140 }}
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
          </Space>
        </div>
        <Table 
          dataSource={teams.filter(t => {
            const matchGroup = !filterGroupId || t.group_id === filterGroupId
            const matchSearch = !searchKeyword || t.name.toLowerCase().includes(searchKeyword.toLowerCase())
            return matchGroup && matchSearch
          })} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 10, showTotal: total => `共 ${total} 个 Team` }} 
        />
      </Card>

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
            extra="从 Network 请求 URL 中获取，格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          >
            <Input placeholder="eabecad0-0c6a-4932-aeb4-4ad932280677" disabled={!!editingTeam} size="large" />
          </Form.Item>
          <Form.Item 
            name="session_token" 
            label="Session Token" 
            rules={[{ required: !editingTeam, message: '请输入 Token' }]} 
            extra="Headers 中 Authorization: Bearer 后面的内容，约 10 天有效"
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
            extra="Team 的最大成员数量（包括已邀请未接受的）"
            initialValue={5}
          >
            <Input type="number" placeholder="5" size="large" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
