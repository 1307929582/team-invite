import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Table, Button, Space, Tag, Descriptions, Spin, Input, message, Row, Col, Progress } from 'antd'
import { ArrowLeftOutlined, SyncOutlined, SearchOutlined, DownloadOutlined, DeleteOutlined } from '@ant-design/icons'
import { Popconfirm } from 'antd'
import { teamApi } from '../api'
import { formatDate, formatDateOnly, toLocalDate } from '../utils/date'
import dayjs from 'dayjs'

interface Team { id: number; name: string; description?: string; account_id: string; is_active: boolean; member_count: number; created_at: string }
interface Member { id: number; email: string; name?: string; role: string; synced_at: string; created_time?: string; chatgpt_user_id?: string }
interface Subscription { plan_type: string; seats_in_use: number; seats_entitled: number; active_until: string; will_renew: boolean; billing_period: string }
interface PendingInvite { id: string; email_address: string; role: string; created_time: string }

const InfoCard = ({ label, value, sub, danger }: { label: string; value: string | number; sub?: string; danger?: boolean }) => (
  <div style={{ 
    padding: 20,
    background: 'rgba(255, 255, 255, 0.6)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    borderRadius: 16,
    border: '1px solid rgba(255, 255, 255, 0.9)',
    height: '100%',
    boxShadow: '0 4px 16px rgba(0, 0, 0, 0.03)',
  }}>
    <div style={{ color: '#64748b', fontSize: 12, marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 24, fontWeight: 700, color: danger ? '#dc2626' : '#1a1a2e' }}>{value}</div>
    {sub && <div style={{ color: '#94a3b8', fontSize: 12, marginTop: 6 }}>{sub}</div>}
  </div>
)

export default function TeamDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [team, setTeam] = useState<Team | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [search, setSearch] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [teamRes, membersRes]: any = await Promise.all([
        teamApi.get(Number(id)),
        teamApi.getMembers(Number(id)),
      ])
      setTeam(teamRes)
      setMembers(membersRes.members)
      
      try {
        const [subRes, invitesRes]: any = await Promise.all([
          teamApi.getSubscription(Number(id)),
          teamApi.getPendingInvites(Number(id)),
        ])
        setSubscription(subRes)
        setPendingInvites(invitesRes.items || [])
      } catch {}
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [id])

  const handleSync = async () => {
    setSyncing(true)
    try { 
      const res: any = await teamApi.syncMembers(Number(id))
      setMembers(res.members)
      message.success(`同步成功，共 ${res.total} 人`)
      try {
        const [subRes, invitesRes]: any = await Promise.all([
          teamApi.getSubscription(Number(id)),
          teamApi.getPendingInvites(Number(id)),
        ])
        setSubscription(subRes)
        setPendingInvites(invitesRes.items || [])
      } catch {}
    } finally { setSyncing(false) }
  }

  const handleExport = () => {
    const csv = [['邮箱', '姓名', '角色', '加入时间'].join(','), ...members.map(m => [m.email, m.name || '', m.role, m.created_time || ''].join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${team?.name}_members_${dayjs().format('YYYYMMDD')}.csv`; a.click()
  }

  const filteredMembers = members.filter(m => m.email.toLowerCase().includes(search.toLowerCase()) || (m.name || '').toLowerCase().includes(search.toLowerCase()))

  const handleRemoveMember = async (userId: string) => {
    try {
      await teamApi.removeMember(Number(id), userId)
      message.success('成员已移除')
      setMembers(members.filter(m => m.chatgpt_user_id !== userId))
    } catch {}
  }

  const handleCancelInvite = async (inviteId: string) => {
    try {
      await teamApi.cancelInvite(Number(id), inviteId)
      message.success('邀请已取消')
      setPendingInvites(pendingInvites.filter(i => i.id !== inviteId))
    } catch {}
  }

  const memberColumns = [
    { title: '邮箱', dataIndex: 'email', ellipsis: true },
    { title: '姓名', dataIndex: 'name', width: 140, render: (v: string) => v || '-' },
    { title: '角色', dataIndex: 'role', width: 120, render: (v: string) => <Tag color={v === 'account-owner' ? 'gold' : 'blue'}>{v === 'account-owner' ? '管理员' : '成员'}</Tag> },
    { title: '加入时间', dataIndex: 'created_time', width: 160, render: (v: string) => v ? <span style={{ color: '#64748b' }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span> : '-' },
    { 
      title: '操作', 
      width: 80, 
      render: (_: any, r: Member) => r.role !== 'account-owner' && r.chatgpt_user_id ? (
        <Popconfirm title="确定移除此成员？" onConfirm={() => handleRemoveMember(r.chatgpt_user_id!)} okText="移除" cancelText="取消">
          <Button size="small" type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ) : null
    },
  ]

  const inviteColumns = [
    { title: '邮箱', dataIndex: 'email_address', ellipsis: true },
    { title: '角色', dataIndex: 'role', width: 100, render: (v: string) => <Tag>{v}</Tag> },
    { title: '邀请时间', dataIndex: 'created_time', width: 160, render: (v: string) => <span style={{ color: '#64748b' }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span> },
    { 
      title: '操作', 
      width: 80, 
      render: (_: any, r: PendingInvite) => (
        <Popconfirm title="确定取消此邀请？" onConfirm={() => handleCancelInvite(r.id)} okText="取消邀请" cancelText="返回">
          <Button size="small" type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      )
    },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <Spin size="large" />
      </div>
    )
  }

  const seatsPercent = subscription ? Math.round((subscription.seats_in_use / subscription.seats_entitled) * 100) : 0
  const daysLeft = subscription ? (toLocalDate(subscription.active_until)?.diff(dayjs(), 'day') || 0) : 0

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/admin/teams')}
          style={{ borderRadius: 10 }}
        />
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>{team?.name}</h2>
          <p style={{ color: '#64748b', fontSize: 13, margin: '6px 0 0' }}>{team?.description || 'ChatGPT Team'}</p>
        </div>
      </div>

      {/* 订阅信息卡片 */}
      {subscription && (
        <Row gutter={16} style={{ marginBottom: 20 }}>
          <Col span={6}>
            <div style={{ 
              padding: 20,
              background: 'rgba(255, 255, 255, 0.6)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              borderRadius: 16,
              border: '1px solid rgba(255, 255, 255, 0.9)',
              height: '100%',
              boxShadow: '0 4px 16px rgba(0, 0, 0, 0.03)',
            }}>
              <div style={{ color: '#64748b', fontSize: 12, marginBottom: 8 }}>座位使用</div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#1a1a2e' }}>
                {subscription.seats_in_use} / {subscription.seats_entitled}
              </div>
              <Progress 
                percent={seatsPercent} 
                showInfo={false} 
                strokeColor={seatsPercent > 80 ? '#dc2626' : '#10b981'} 
                trailColor="rgba(0, 0, 0, 0.06)"
                style={{ marginTop: 10 }}
              />
            </div>
          </Col>
          <Col span={6}>
            <InfoCard 
              label="计划类型" 
              value={subscription.plan_type.toUpperCase()} 
              sub={subscription.billing_period === 'monthly' ? '月付' : '年付'}
            />
          </Col>
          <Col span={6}>
            <InfoCard 
              label="到期时间" 
              value={formatDateOnly(subscription.active_until)} 
              sub={`剩余 ${daysLeft} 天`}
              danger={daysLeft < 7}
            />
          </Col>
          <Col span={6}>
            <InfoCard 
              label="待处理邀请" 
              value={pendingInvites.length} 
              sub="已发送未接受"
            />
          </Col>
        </Row>
      )}

      {/* 基本信息 */}
      <Card style={{ marginBottom: 20 }} size="small">
        <Descriptions column={3} size="small">
          <Descriptions.Item label="Account ID"><code>{team?.account_id}</code></Descriptions.Item>
          <Descriptions.Item label="状态"><Tag color={team?.is_active ? 'green' : 'red'}>{team?.is_active ? '正常' : '禁用'}</Tag></Descriptions.Item>
          <Descriptions.Item label="创建时间">{formatDate(team?.created_at, 'YYYY-MM-DD HH:mm')}</Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 成员列表 */}
      <Card
        title={`成员列表 (${members.length})`}
        size="small"
        extra={
          <Space>
            <Input 
              placeholder="搜索成员" 
              prefix={<SearchOutlined style={{ color: '#94a3b8' }} />} 
              value={search} 
              onChange={e => setSearch(e.target.value)} 
              style={{ width: 180 }} 
              allowClear
            />
            <Button icon={<DownloadOutlined />} onClick={handleExport}>导出</Button>
            <Button type="primary" icon={<SyncOutlined spin={syncing} />} loading={syncing} onClick={handleSync}>同步</Button>
          </Space>
        }
        bodyStyle={{ padding: 0 }}
      >
        <Table dataSource={filteredMembers} columns={memberColumns} rowKey="id" pagination={{ pageSize: 10 }} size="small" />
      </Card>

      {/* 待处理邀请 */}
      {pendingInvites.length > 0 && (
        <Card title={`待处理邀请 (${pendingInvites.length})`} size="small" style={{ marginTop: 20 }} bodyStyle={{ padding: 0 }}>
          <Table dataSource={pendingInvites} columns={inviteColumns} rowKey="id" pagination={false} size="small" />
        </Card>
      )}
    </div>
  )
}
