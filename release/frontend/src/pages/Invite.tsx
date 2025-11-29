import { useEffect, useState } from 'react'
import { Card, Select, Input, Button, Table, Tag, Space, Progress, Row, Col, message } from 'antd'
import { SendOutlined, CheckCircleOutlined, CloseCircleOutlined, TeamOutlined } from '@ant-design/icons'
import { teamApi, inviteApi } from '../api'
import { useStore } from '../store'

const { TextArea } = Input

interface InviteResult {
  email: string
  success: boolean
  error?: string
}

export default function Invite() {
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null)
  const [emailsText, setEmailsText] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<InviteResult[]>([])
  const { teams, setTeams } = useStore()

  useEffect(() => {
    teamApi.list().then((res: any) => setTeams(res.teams))
  }, [setTeams])

  const emails = emailsText.split(/[\n,;]/).map(e => e.trim()).filter(e => e && e.includes('@'))

  const handleInvite = async () => {
    if (!selectedTeam || emails.length === 0) return
    setLoading(true)
    setResults([])
    try {
      const res: any = await inviteApi.batchInvite(selectedTeam, emails)
      setResults(res.results)
      const successCount = res.results.filter((r: InviteResult) => r.success).length
      if (successCount > 0) {
        message.success(`成功邀请 ${successCount} 人`)
      }
    } finally {
      setLoading(false)
    }
  }

  const successCount = results.filter(r => r.success).length
  const failCount = results.filter(r => !r.success).length
  const selectedTeamInfo = teams.find(t => t.id === selectedTeam)

  const columns = [
    { title: '邮箱', dataIndex: 'email', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'success',
      width: 80,
      render: (v: boolean) => (
        <Tag icon={v ? <CheckCircleOutlined /> : <CloseCircleOutlined />} color={v ? 'success' : 'error'}>
          {v ? '成功' : '失败'}
        </Tag>
      ),
    },
    { 
      title: '错误信息', 
      dataIndex: 'error', 
      ellipsis: true, 
      render: (v: string) => v ? <span style={{ color: '#dc2626', fontSize: 13 }}>{v}</span> : '-'
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>批量邀请</h2>
        <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>向 Team 批量发送邀请邮件</p>
      </div>

      <Row gutter={24}>
        <Col span={14}>
          <Card size="small">
            <Space direction="vertical" style={{ width: '100%' }} size={24}>
              {/* Team 选择 */}
              <div>
                <div style={{ marginBottom: 12, fontWeight: 600, color: '#1a1a2e' }}>选择 Team</div>
                <Select
                  style={{ width: '100%' }}
                  placeholder="请选择要邀请的 Team"
                  value={selectedTeam}
                  onChange={setSelectedTeam}
                  size="large"
                  options={teams.map(t => ({ 
                    label: (
                      <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <TeamOutlined style={{ color: '#64748b' }} />
                        {t.name}
                        <span style={{ color: '#94a3b8', fontSize: 12 }}>({t.member_count}人)</span>
                      </span>
                    ), 
                    value: t.id 
                  }))}
                />
                {selectedTeamInfo && (
                  <div style={{ 
                    marginTop: 14, 
                    padding: '14px 18px', 
                    background: 'rgba(255, 255, 255, 0.6)', 
                    borderRadius: 12, 
                    fontSize: 13, 
                    color: '#64748b',
                    border: '1px solid rgba(0, 0, 0, 0.06)',
                  }}>
                    <TeamOutlined style={{ marginRight: 10, color: '#1a1a2e' }} />
                    当前 <span style={{ fontWeight: 600, color: '#1a1a2e' }}>{selectedTeamInfo.name}</span> 有 {selectedTeamInfo.member_count} 名成员
                  </div>
                )}
              </div>

              {/* 邮箱输入 */}
              <div>
                <div style={{ marginBottom: 12, fontWeight: 600, color: '#1a1a2e' }}>
                  邮箱列表 
                  <span style={{ fontWeight: 400, color: '#94a3b8', marginLeft: 10, fontSize: 13 }}>
                    每行一个，或用逗号分隔
                  </span>
                </div>
                <TextArea
                  rows={14}
                  placeholder={`user1@company.com\nuser2@company.com\nuser3@company.com`}
                  value={emailsText}
                  onChange={e => setEmailsText(e.target.value)}
                  style={{ fontSize: 14 }}
                />
                <div style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ 
                    color: emails.length > 0 ? '#059669' : '#94a3b8', 
                    fontSize: 13,
                    fontWeight: 500,
                  }}>
                    已识别 {emails.length} 个有效邮箱
                  </span>
                  {emails.length > 0 && (
                    <Button type="link" size="small" onClick={() => setEmailsText('')} style={{ color: '#64748b' }}>清空</Button>
                  )}
                </div>
              </div>

              {/* 邀请按钮 */}
              <Button
                type="primary"
                icon={<SendOutlined />}
                size="large"
                block
                loading={loading}
                disabled={!selectedTeam || emails.length === 0}
                onClick={handleInvite}
                style={{ 
                  height: 52, 
                  borderRadius: 14, 
                  fontSize: 15, 
                  fontWeight: 600,
                }}
              >
                {loading ? '邀请中...' : `发送邀请 (${emails.length})`}
              </Button>
            </Space>
          </Card>
        </Col>

        <Col span={10}>
          <Card title="邀请结果" size="small" style={{ height: '100%' }}>
            {loading && (
              <div style={{ textAlign: 'center', padding: 60 }}>
                <Progress type="circle" percent={0} status="active" size={80} strokeColor="#1a1a2e" trailColor="rgba(0, 0, 0, 0.06)" />
                <div style={{ marginTop: 20, color: '#64748b', fontSize: 14 }}>正在发送邀请...</div>
              </div>
            )}

            {!loading && results.length > 0 && (
              <>
                <Row gutter={16} style={{ marginBottom: 20 }}>
                  <Col span={12}>
                    <div style={{ 
                      background: 'rgba(16, 185, 129, 0.08)', 
                      padding: 18, 
                      borderRadius: 14, 
                      textAlign: 'center',
                      border: '1px solid rgba(16, 185, 129, 0.15)',
                    }}>
                      <div style={{ color: '#059669', fontSize: 32, fontWeight: 700 }}>{successCount}</div>
                      <div style={{ color: '#059669', fontSize: 13, fontWeight: 500, marginTop: 4 }}>成功</div>
                    </div>
                  </Col>
                  <Col span={12}>
                    <div style={{ 
                      background: 'rgba(239, 68, 68, 0.08)', 
                      padding: 18, 
                      borderRadius: 14, 
                      textAlign: 'center',
                      border: '1px solid rgba(239, 68, 68, 0.15)',
                    }}>
                      <div style={{ color: '#dc2626', fontSize: 32, fontWeight: 700 }}>{failCount}</div>
                      <div style={{ color: '#dc2626', fontSize: 13, fontWeight: 500, marginTop: 4 }}>失败</div>
                    </div>
                  </Col>
                </Row>
                <Table 
                  dataSource={results} 
                  columns={columns} 
                  rowKey="email" 
                  size="small" 
                  pagination={{ pageSize: 6 }}
                />
              </>
            )}

            {!loading && results.length === 0 && (
              <div style={{ textAlign: 'center', padding: 80, color: '#94a3b8' }}>
                <SendOutlined style={{ fontSize: 48, marginBottom: 16, opacity: 0.5 }} />
                <div style={{ fontSize: 14 }}>邀请结果将在此显示</div>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
