import { useEffect, useState } from 'react'
import { Card, Table, Select, Tag, Space } from 'antd'
import { dashboardApi, teamApi } from '../api'
import { useStore } from '../store'
import dayjs from 'dayjs'

interface Log {
  id: number
  action: string
  target: string
  details: string
  user_name: string
  team_name: string
  ip_address: string
  created_at: string
}

const actionMap: Record<string, { label: string; color: string }> = {
  batch_invite: { label: '批量邀请', color: 'blue' },
  sync: { label: '同步成员', color: 'green' },
  create: { label: '创建', color: 'purple' },
  update: { label: '更新', color: 'orange' },
  delete: { label: '删除', color: 'red' },
}

export default function Logs() {
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTeam, setSelectedTeam] = useState<number | undefined>()
  const { teams, setTeams } = useStore()

  const fetchLogs = async (teamId?: number) => {
    setLoading(true)
    try {
      const res: any = await dashboardApi.getLogs(100, teamId)
      setLogs(res.logs)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    teamApi.list().then((res: any) => setTeams(res.teams))
    fetchLogs()
  }, [setTeams])

  const handleTeamChange = (value: number | undefined) => {
    setSelectedTeam(value)
    fetchLogs(value)
  }

  const columns = [
    { 
      title: '时间', 
      dataIndex: 'created_at', 
      width: 160, 
      render: (v: string) => <span style={{ color: '#888', fontSize: 12 }}>{dayjs(v).format('YYYY-MM-DD HH:mm:ss')}</span>
    },
    { 
      title: '操作', 
      dataIndex: 'action', 
      width: 100, 
      render: (v: string) => {
        const info = actionMap[v] || { label: v, color: 'default' }
        return <Tag color={info.color}>{info.label}</Tag>
      }
    },
    { title: 'Team', dataIndex: 'team_name', width: 120, render: (v: string) => v || '-' },
    { title: '操作人', dataIndex: 'user_name', width: 100, render: (v: string) => v || '-' },
    { title: '对象', dataIndex: 'target', width: 120, render: (v: string) => v || '-' },
    { title: '详情', dataIndex: 'details', ellipsis: true, render: (v: string) => <span style={{ fontSize: 12 }}>{v || '-'}</span> },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 600, margin: 0 }}>操作日志</h2>
          <p style={{ color: '#888', fontSize: 13, margin: '4px 0 0' }}>查看所有操作记录</p>
        </div>
        <Space>
          <span style={{ color: '#888', fontSize: 13 }}>筛选 Team：</span>
          <Select
            style={{ width: 180 }}
            placeholder="全部 Team"
            allowClear
            value={selectedTeam}
            onChange={handleTeamChange}
            options={teams.map(t => ({ label: t.name, value: t.id }))}
          />
        </Space>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <Table 
          dataSource={logs} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 15, showTotal: total => `共 ${total} 条记录` }} 
        />
      </Card>
    </div>
  )
}
