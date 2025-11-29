import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Tag, message, Popconfirm, Select } from 'antd'
import { SyncOutlined, DeleteOutlined } from '@ant-design/icons'
import { teamApi } from '../api'
import { useStore } from '../store'
import { formatDate } from '../utils/date'
import dayjs from 'dayjs'

interface PendingInvite {
  id: string
  email_address: string
  role: string
  created_time: string
  team_id: number
  team_name: string
}

export default function PendingInvites() {
  const [loading, setLoading] = useState(false)
  const [invites, setInvites] = useState<PendingInvite[]>([])
  const [filterTeamId, setFilterTeamId] = useState<number | undefined>(undefined)
  const { teams, setTeams } = useStore()

  const fetchAllInvites = async () => {
    setLoading(true)
    try {
      const res: any = await teamApi.list()
      const teamsList = res.teams || []
      setTeams(teamsList)

      const allInvites: PendingInvite[] = []
      for (const team of teamsList) {
        try {
          const invitesRes: any = await teamApi.getPendingInvites(team.id)
          const items = invitesRes.items || []
          items.forEach((item: any) => {
            allInvites.push({
              ...item,
              team_id: team.id,
              team_name: team.name,
            })
          })
        } catch {}
      }
      
      // 按邀请时间倒序
      allInvites.sort((a, b) => dayjs(b.created_time).valueOf() - dayjs(a.created_time).valueOf())
      setInvites(allInvites)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllInvites()
  }, [])

  const handleCancelInvite = async (teamId: number, email: string) => {
    try {
      await teamApi.cancelInvite(teamId, email)
      message.success('邀请已取消')
      setInvites(invites.filter(i => !(i.team_id === teamId && i.email_address === email)))
    } catch {}
  }

  const filteredInvites = filterTeamId 
    ? invites.filter(i => i.team_id === filterTeamId) 
    : invites

  // 计算等待天数
  const getDaysWaiting = (createdTime: string) => {
    const days = dayjs().diff(dayjs(createdTime), 'day')
    if (days === 0) return '今天'
    if (days === 1) return '1 天'
    return `${days} 天`
  }

  const columns = [
    { 
      title: '邮箱', 
      dataIndex: 'email_address', 
      ellipsis: true,
      render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>
    },
    { 
      title: 'Team', 
      dataIndex: 'team_name', 
      width: 150,
      render: (v: string) => <Tag color="blue">{v}</Tag>
    },
    { 
      title: '角色', 
      dataIndex: 'role', 
      width: 120, 
      render: (v: string) => <Tag>{v === 'standard-user' ? '成员' : v}</Tag>
    },
    { 
      title: '邀请时间', 
      dataIndex: 'created_time', 
      width: 160, 
      render: (v: string) => <span style={{ color: '#64748b' }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span>
    },
    { 
      title: '等待时长', 
      dataIndex: 'created_time', 
      width: 100, 
      render: (v: string) => {
        const days = dayjs().diff(dayjs(v), 'day')
        return (
          <Tag color={days > 7 ? 'red' : days > 3 ? 'orange' : 'default'}>
            {getDaysWaiting(v)}
          </Tag>
        )
      }
    },
    {
      title: '操作',
      width: 100,
      render: (_: any, r: PendingInvite) => (
        <Popconfirm 
          title="确定取消此邀请？" 
          onConfirm={() => handleCancelInvite(r.team_id, r.email_address)} 
          okText="取消邀请" 
          cancelText="返回"
        >
          <Button size="small" type="text" danger icon={<DeleteOutlined />}>
            取消
          </Button>
        </Popconfirm>
      )
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>待处理邀请</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>查看所有已发送但未接受的邀请</p>
        </div>
        <Button 
          icon={<SyncOutlined spin={loading} />} 
          onClick={fetchAllInvites} 
          loading={loading}
          size="large"
          style={{ borderRadius: 12, height: 44 }}
        >
          刷新
        </Button>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #f0f0f0' }}>
          <Space size="large">
            <Space>
              <span style={{ color: '#64748b' }}>Team 筛选：</span>
              <Select
                placeholder="全部 Team"
                allowClear
                style={{ width: 180 }}
                value={filterTeamId}
                onChange={setFilterTeamId}
              >
                {teams.map(t => (
                  <Select.Option key={t.id} value={t.id}>{t.name}</Select.Option>
                ))}
              </Select>
            </Space>
            <span style={{ color: '#94a3b8' }}>
              共 {filteredInvites.length} 条待处理邀请
            </span>
          </Space>
        </div>
        <Table 
          dataSource={filteredInvites} 
          columns={columns} 
          rowKey={r => `${r.team_id}-${r.email_address}`}
          loading={loading} 
          pagination={{ pageSize: 20, showTotal: total => `共 ${total} 条` }}
        />
      </Card>
    </div>
  )
}
