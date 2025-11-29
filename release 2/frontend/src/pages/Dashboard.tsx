import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Card, Table, Spin, Tag, Progress, Button } from 'antd'
import { TeamOutlined, UserOutlined, MailOutlined, RightOutlined } from '@ant-design/icons'
import { Line } from '@ant-design/charts'
import { dashboardApi, teamApi } from '../api'
import { useStore } from '../store'
import { formatShortDate, formatDateOnly } from '../utils/date'

interface Stats {
  total_teams: number
  total_members: number
  invites_today: number
  invites_this_week: number
  invite_trend?: { date: string; count: number }[]
  queue_pending?: number
  daily_invite_limit?: number
}

interface Log {
  id: number
  action: string
  target: string
  details: string
  user_name: string
  team_name: string
  created_at: string
}

interface Team {
  id: number
  name: string
  member_count: number
  max_seats: number
  token_expires_at?: string
}

const StatCard = ({ icon, label, value, gradient }: { icon: React.ReactNode; label: string; value: number; gradient: string }) => (
  <div style={{ 
    padding: 24,
    background: 'rgba(255, 255, 255, 0.7)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 20,
    border: '1px solid rgba(255, 255, 255, 0.9)',
    transition: 'all 0.3s ease',
    cursor: 'default',
    boxShadow: '0 4px 24px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.8)',
  }}
  onMouseEnter={e => {
    e.currentTarget.style.transform = 'translateY(-2px)'
    e.currentTarget.style.boxShadow = '0 12px 40px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9)'
  }}
  onMouseLeave={e => {
    e.currentTarget.style.transform = 'translateY(0)'
    e.currentTarget.style.boxShadow = '0 4px 24px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.8)'
  }}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
      <div style={{ 
        width: 52, 
        height: 52, 
        borderRadius: 14, 
        background: gradient,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 22,
        color: '#fff',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
      }}>
        {icon}
      </div>
      <div>
        <div style={{ color: '#64748b', fontSize: 13, marginBottom: 4 }}>{label}</div>
        <div style={{ fontSize: 32, fontWeight: 700, color: '#1a1a2e', letterSpacing: '-1px' }}>{value}</div>
      </div>
    </div>
  </div>
)

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [logs, setLogs] = useState<Log[]>([])
  const [loading, setLoading] = useState(true)
  const [teamList, setTeamList] = useState<Team[]>([])
  const { teams, setTeams } = useStore()
  const navigate = useNavigate()

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, logsRes, teamsRes]: any = await Promise.all([
          dashboardApi.getStats(),
          dashboardApi.getLogs(10),
          teamApi.list(),
        ])
        setStats(statsRes)
        setLogs(logsRes.logs)
        setTeams(teamsRes.teams)
        setTeamList(teamsRes.teams)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [setTeams])

  const logColumns = [
    { 
      title: '时间', 
      dataIndex: 'created_at', 
      width: 140, 
      render: (v: string) => (
        <span style={{ color: '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span>
      )
    },
    { 
      title: '操作', 
      dataIndex: 'action', 
      width: 100, 
      render: (v: string) => <Tag>{v}</Tag>
    },
    { 
      title: 'Team', 
      dataIndex: 'team_name', 
      width: 120, 
      render: (v: string) => v || '-'
    },
    { 
      title: '详情', 
      dataIndex: 'details', 
      ellipsis: true, 
      render: (v: string) => <span style={{ color: '#64748b', fontSize: 13 }}>{v || '-'}</span>
    },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  // 计算总座位使用率
  const totalSeats = teamList.reduce((sum, t) => sum + (t.max_seats || 5), 0)
  const usedSeats = teamList.reduce((sum, t) => sum + (t.member_count || 0), 0)
  const seatUsagePercent = totalSeats > 0 ? Math.round((usedSeats / totalSeats) * 100) : 0

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>工作台</h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>
          欢迎使用 ChatGPT Team 管理平台
        </p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={20} style={{ marginBottom: 28 }}>
        <Col span={6}>
          <StatCard 
            icon={<TeamOutlined />} 
            label="管理 Teams" 
            value={stats?.total_teams || 0} 
            gradient="linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)"
          />
        </Col>
        <Col span={6}>
          <StatCard 
            icon={<UserOutlined />} 
            label="总成员数" 
            value={stats?.total_members || 0} 
            gradient="linear-gradient(135deg, #10b981 0%, #34d399 100%)"
          />
        </Col>
        <Col span={6}>
          <StatCard 
            icon={<MailOutlined />} 
            label="今日邀请" 
            value={stats?.invites_today || 0} 
            gradient="linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)"
          />
        </Col>
        <Col span={6}>
          <StatCard 
            icon={<MailOutlined />} 
            label="本周邀请" 
            value={stats?.invites_this_week || 0} 
            gradient="linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)"
          />
        </Col>
      </Row>

      {/* 座位使用率 + 邀请趋势 */}
      <Row gutter={20} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <Card title="总座位使用率" size="small">
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Progress 
                type="dashboard" 
                percent={seatUsagePercent} 
                strokeColor={seatUsagePercent >= 90 ? '#ef4444' : seatUsagePercent >= 70 ? '#f59e0b' : '#10b981'}
                format={percent => (
                  <div>
                    <div style={{ fontSize: 28, fontWeight: 700 }}>{percent}%</div>
                    <div style={{ fontSize: 12, color: '#64748b' }}>{usedSeats}/{totalSeats}</div>
                  </div>
                )}
              />
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card title="近7天邀请趋势" size="small">
            <div style={{ height: 160 }}>
              {stats?.invite_trend && stats.invite_trend.length > 0 ? (
                <Line
                  data={stats.invite_trend.map(item => ({
                    date: formatDateOnly(item.date).slice(5),
                    count: item.count,
                  }))}
                  xField="date"
                  yField="count"
                  smooth
                  point={{ size: 4, shape: 'circle' }}
                  color="#8b5cf6"
                  areaStyle={{ fill: 'l(270) 0:rgba(139, 92, 246, 0.1) 1:rgba(139, 92, 246, 0.3)' }}
                  area={{}}
                  yAxis={{ 
                    min: 0,
                    tickCount: 4,
                    label: { style: { fill: '#94a3b8', fontSize: 11 } },
                    grid: { line: { style: { stroke: '#f0f0f0', lineDash: [4, 4] } } },
                  }}
                  xAxis={{
                    label: { style: { fill: '#94a3b8', fontSize: 11 } },
                    line: { style: { stroke: '#f0f0f0' } },
                  }}
                  tooltip={{
                    formatter: (datum: { count: number }) => ({ name: '邀请数', value: datum.count }),
                  }}
                  animation={{ appear: { animation: 'wave-in', duration: 800 } }}
                />
              ) : (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
                  暂无数据
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Team 列表 */}
      <Card 
        title="Team 座位情况" 
        size="small"
        extra={
          <Button type="link" size="small" onClick={() => navigate('/admin/teams')} style={{ color: '#64748b' }}>
            查看全部 <RightOutlined />
          </Button>
        }
        style={{ marginBottom: 20 }}
      >
        <Row gutter={16}>
          {teams.slice(0, 4).map(team => {
            const memberCount = team.member_count || 0
            const maxSeats = team.max_seats || 5
            const usage = maxSeats > 0 ? Math.round((memberCount / maxSeats) * 100) : 0
            return (
              <Col span={6} key={team.id}>
                <div 
                  onClick={() => navigate(`/admin/teams/${team.id}`)}
                  style={{ 
                    padding: 20, 
                    background: 'rgba(255, 255, 255, 0.5)', 
                    borderRadius: 14, 
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    border: '1px solid rgba(0, 0, 0, 0.04)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.8)'
                    e.currentTarget.style.borderColor = 'rgba(0, 0, 0, 0.08)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.5)'
                    e.currentTarget.style.borderColor = 'rgba(0, 0, 0, 0.04)'
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 8, color: '#1a1a2e' }}>{team.name}</div>
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
          {teams.length === 0 && (
            <Col span={24}>
              <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                暂无 Team，点击右上角添加
              </div>
            </Col>
          )}
        </Row>
      </Card>

      {/* 最近操作 */}
      <Card title="最近操作" size="small" bodyStyle={{ padding: 0 }}>
        <Table 
          dataSource={logs} 
          columns={logColumns} 
          rowKey="id" 
          pagination={false} 
          size="small"
          locale={{ emptyText: '暂无操作记录' }}
        />
      </Card>
    </div>
  )
}
