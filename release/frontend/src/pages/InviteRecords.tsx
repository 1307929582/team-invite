import { useEffect, useState } from 'react'
import { Card, Table, Input, Tag, Space, Select, Tooltip, Radio, Button, message } from 'antd'
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons'
import { inviteRecordApi, teamApi, groupApi } from '../api'
import { formatDate, formatShortDate } from '../utils/date'

interface InviteRecord {
  id: number
  email: string
  team_id: number
  team_name: string
  group_id?: number
  group_name?: string
  group_color?: string
  status: string
  redeem_code?: string
  linuxdo_username?: string
  created_at: string
  accepted_at?: string
}

interface Team {
  id: number
  name: string
  group_id?: number
}

interface Group {
  id: number
  name: string
  color: string
}

type FilterType = 'all' | 'pending' | 'accepted'

export default function InviteRecords() {
  const [records, setRecords] = useState<InviteRecord[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [teamId, setTeamId] = useState<number | undefined>()
  const [groupId, setGroupId] = useState<number | undefined>()
  const [filter, setFilter] = useState<FilterType>('all')

  const fetchRecords = async () => {
    setLoading(true)
    try {
      const res: any = await inviteRecordApi.list({ search, team_id: teamId, group_id: groupId })
      setRecords(res.records)
    } finally {
      setLoading(false)
    }
  }

  const fetchTeamsAndGroups = async () => {
    try {
      const [teamsRes, groupsRes]: any = await Promise.all([
        teamApi.list(),
        groupApi.list()
      ])
      setTeams(teamsRes.teams)
      setGroups(groupsRes)
    } catch {}
  }

  useEffect(() => {
    fetchTeamsAndGroups()
  }, [])

  useEffect(() => {
    fetchRecords()
  }, [teamId, groupId])

  const handleSearch = () => {
    fetchRecords()
  }

  // 导出 CSV
  const exportCSV = () => {
    const headers = ['邮箱', 'Team', '分组', '邀请码', 'LinuxDO用户', '发送状态', '接受状态', '邀请时间', '接受时间']
    const rows = filteredRecords.map(r => [
      r.email,
      r.team_name || '',
      r.group_name || '',
      r.redeem_code || '手动邀请',
      r.linuxdo_username || '',
      r.status === 'success' ? '已发送' : r.status === 'pending' ? '待处理' : '失败',
      r.accepted_at ? '已接受' : '待接受',
      formatDate(r.created_at),
      r.accepted_at ? formatDate(r.accepted_at) : ''
    ])
    
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `邀请记录_${formatDate(new Date(), 'YYYYMMDD_HHmmss')}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  }

  // 根据筛选条件过滤
  const filteredRecords = records.filter(r => {
    switch (filter) {
      case 'pending':
        return !r.accepted_at
      case 'accepted':
        return !!r.accepted_at
      default:
        return true
    }
  })

  // 统计
  const stats = {
    all: records.length,
    pending: records.filter(r => !r.accepted_at).length,
    accepted: records.filter(r => !!r.accepted_at).length,
  }

  const statusMap: Record<string, { label: string; color: string }> = {
    pending: { label: '待处理', color: 'orange' },
    success: { label: '已发送', color: 'blue' },
    failed: { label: '失败', color: 'red' },
  }

  const columns = [
    { 
      title: '邮箱', 
      dataIndex: 'email',
      ellipsis: true,
      render: (v: string) => <span style={{ fontWeight: 500 }}>{v}</span>
    },
    { 
      title: 'Team', 
      dataIndex: 'team_name', 
      width: 140,
      render: (v: string) => v || <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '分组', 
      width: 100,
      render: (_: any, r: InviteRecord) => r.group_name ? (
        <Tag color={r.group_color}>{r.group_name}</Tag>
      ) : <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '邀请码', 
      dataIndex: 'redeem_code', 
      width: 120,
      render: (v: string) => v ? <code style={{ fontSize: 12 }}>{v}</code> : <span style={{ color: '#94a3b8' }}>手动邀请</span>
    },
    { 
      title: 'LinuxDO 用户', 
      dataIndex: 'linuxdo_username', 
      width: 120,
      render: (v: string) => v ? <span>@{v}</span> : <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '发送状态', 
      dataIndex: 'status', 
      width: 90,
      render: (v: string) => {
        const info = statusMap[v] || { label: v, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      }
    },
    { 
      title: '接受状态', 
      width: 90,
      render: (_: any, r: InviteRecord) => r.accepted_at ? (
        <Tag color="green">已接受</Tag>
      ) : (
        <Tag color="default">待接受</Tag>
      )
    },
    { 
      title: '邀请时间', 
      dataIndex: 'created_at', 
      width: 140,
      render: (v: string) => (
        <Tooltip title={formatDate(v)}>
          <span style={{ color: '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span>
        </Tooltip>
      )
    },
    { 
      title: '接受时间', 
      dataIndex: 'accepted_at', 
      width: 140,
      render: (v: string) => v ? (
        <Tooltip title={formatDate(v)}>
          <span style={{ color: '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span>
        </Tooltip>
      ) : <span style={{ color: '#94a3b8' }}>-</span>
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>邀请记录</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>查看所有邀请的邮箱及状态</p>
        </div>
        <Space>
          <Select
            style={{ width: 120 }}
            placeholder="全部分组"
            allowClear
            value={groupId}
            onChange={setGroupId}
            options={groups.map(g => ({ label: g.name, value: g.id }))}
          />
          <Select
            style={{ width: 140 }}
            placeholder="全部 Team"
            allowClear
            value={teamId}
            onChange={setTeamId}
            options={teams.map(t => ({ label: t.name, value: t.id }))}
          />
          <Input
            placeholder="搜索邮箱/邀请码"
            prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
            value={search}
            onChange={e => setSearch(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 200 }}
            allowClear
          />
          <Button icon={<DownloadOutlined />} onClick={exportCSV}>导出 CSV</Button>
        </Space>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f0f0f0' }}>
          <Radio.Group value={filter} onChange={e => setFilter(e.target.value)} buttonStyle="solid">
            <Radio.Button value="all">全部 ({stats.all})</Radio.Button>
            <Radio.Button value="pending">待接受 ({stats.pending})</Radio.Button>
            <Radio.Button value="accepted">已接受 ({stats.accepted})</Radio.Button>
          </Radio.Group>
        </div>
        <Table 
          dataSource={filteredRecords} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 20, showTotal: total => `共 ${total} 条记录` }}
          locale={{ emptyText: '暂无邀请记录' }}
        />
      </Card>
    </div>
  )
}
