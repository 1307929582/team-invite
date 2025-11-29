import { useEffect, useState } from 'react'
import { Card, Table, Input, Tag, Space, Select, Avatar, Tooltip } from 'antd'
import { SearchOutlined, UserOutlined } from '@ant-design/icons'
import { linuxdoUserApi } from '../api'
import { formatDate, formatShortDate } from '../utils/date'

interface LinuxDOUser {
  id: number
  linuxdo_id: string
  username: string
  name?: string
  email?: string
  trust_level: number
  avatar_url?: string
  created_at: string
  last_login: string
  invite_email?: string
  invite_team?: string
  invite_status?: string
  invite_time?: string
}

export default function LinuxDOUsers() {
  const [users, setUsers] = useState<LinuxDOUser[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [hasInvite, setHasInvite] = useState<boolean | undefined>()

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const res: any = await linuxdoUserApi.list(search || undefined, hasInvite)
      setUsers(res.users)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [hasInvite])

  const handleSearch = () => {
    fetchUsers()
  }

  const statusMap: Record<string, { label: string; color: string }> = {
    pending: { label: '待接受', color: 'orange' },
    success: { label: '已邀请', color: 'green' },
    failed: { label: '失败', color: 'red' },
  }

  const columns = [
    { 
      title: '用户', 
      width: 200,
      render: (_: any, r: LinuxDOUser) => (
        <Space>
          <Avatar src={r.avatar_url} icon={<UserOutlined />} size={36} />
          <div>
            <div style={{ fontWeight: 500 }}>{r.name || r.username}</div>
            <div style={{ fontSize: 12, color: '#64748b' }}>@{r.username}</div>
          </div>
        </Space>
      )
    },
    { 
      title: 'LinuxDO ID', 
      dataIndex: 'linuxdo_id', 
      width: 100,
      render: (v: string) => <code style={{ fontSize: 12 }}>{v}</code>
    },
    { 
      title: '信任等级', 
      dataIndex: 'trust_level', 
      width: 90,
      render: (v: number) => <Tag color={v >= 2 ? 'green' : v >= 1 ? 'blue' : 'default'}>Lv.{v}</Tag>
    },
    { 
      title: '邀请邮箱', 
      dataIndex: 'invite_email', 
      ellipsis: true,
      render: (v: string) => v || <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '所属 Team', 
      dataIndex: 'invite_team', 
      width: 120,
      render: (v: string) => v || <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '邀请状态', 
      dataIndex: 'invite_status', 
      width: 90,
      render: (v: string) => {
        if (!v) return <span style={{ color: '#94a3b8' }}>-</span>
        const info = statusMap[v] || { label: v, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      }
    },
    { 
      title: '邀请时间', 
      dataIndex: 'invite_time', 
      width: 140,
      render: (v: string) => v ? (
        <Tooltip title={formatDate(v)}>
          <span style={{ color: '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span>
        </Tooltip>
      ) : <span style={{ color: '#94a3b8' }}>-</span>
    },
    { 
      title: '最后登录', 
      dataIndex: 'last_login', 
      width: 140,
      render: (v: string) => <span style={{ color: '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span>
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>用户管理</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>查看 LinuxDO 用户及邀请记录</p>
        </div>
        <Space>
          <Select
            style={{ width: 140 }}
            placeholder="全部用户"
            allowClear
            value={hasInvite}
            onChange={setHasInvite}
            options={[
              { label: '已邀请', value: true },
              { label: '未邀请', value: false },
            ]}
          />
          <Input
            placeholder="搜索用户名/ID"
            prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
            value={search}
            onChange={e => setSearch(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 200 }}
            allowClear
          />
        </Space>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <Table 
          dataSource={users} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 15, showTotal: total => `共 ${total} 个用户` }}
          locale={{ emptyText: '暂无用户' }}
        />
      </Card>
    </div>
  )
}
