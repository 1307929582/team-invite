import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, message, Popconfirm, Tooltip, Radio, Select, Alert, Collapse } from 'antd'
import { QuestionCircleOutlined } from '@ant-design/icons'
import { PlusOutlined, DeleteOutlined, CopyOutlined, StopOutlined, CheckOutlined, LinkOutlined, EyeOutlined } from '@ant-design/icons'
import { redeemApi, groupApi } from '../api'
import { formatDate, formatShortDate, toLocalDate } from '../utils/date'
import dayjs from 'dayjs'

interface DirectCode {
  id: number
  code: string
  code_type: string
  max_uses: number
  used_count: number
  expires_at?: string
  is_active: boolean
  note?: string
  group_id?: number
  group_name?: string
  created_at: string
}

interface Group {
  id: number
  name: string
  color: string
}

interface InviteRecord {
  id: number
  email: string
  team_name: string
  status: string
  created_at: string
  accepted_at?: string
}

type FilterType = 'all' | 'available' | 'used' | 'expired'

export default function DirectCodes() {
  const [codes, setCodes] = useState<DirectCode[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newCodes, setNewCodes] = useState<string[]>([])
  const [filter, setFilter] = useState<FilterType>('all')
  const [recordsModal, setRecordsModal] = useState(false)
  const [records, setRecords] = useState<InviteRecord[]>([])
  const [currentCode, setCurrentCode] = useState('')
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [form] = Form.useForm()

  const fetchCodes = async () => {
    setLoading(true)
    try {
      const res: any = await redeemApi.list(undefined, undefined, 'direct')
      setCodes(res.codes)
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

  useEffect(() => {
    fetchCodes()
    fetchGroups()
  }, [])

  const isExpiredCode = (code: DirectCode) => code.expires_at && toLocalDate(code.expires_at)?.isBefore(dayjs())

  const filteredCodes = codes.filter(code => {
    const isExpired = isExpiredCode(code)
    const isUsedUp = code.used_count >= code.max_uses
    const isAvailable = code.is_active && !isExpired && !isUsedUp
    switch (filter) {
      case 'available': return isAvailable
      case 'used': return isUsedUp
      case 'expired': return isExpired
      default: return true
    }
  })

  const stats = {
    all: codes.length,
    available: codes.filter(c => c.is_active && !isExpiredCode(c) && c.used_count < c.max_uses).length,
    used: codes.filter(c => c.used_count >= c.max_uses).length,
    expired: codes.filter(c => isExpiredCode(c)).length,
  }

  const handleCreate = async () => {
    const values = await form.validateFields()
    setCreating(true)
    try {
      const res: any = await redeemApi.batchCreate({ ...values, code_type: 'direct' })
      setNewCodes(res.codes)
      message.success(`成功创建 ${res.count} 个直接链接`)
      fetchCodes()
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number) => {
    await redeemApi.delete(id)
    message.success('删除成功')
    fetchCodes()
  }

  const handleToggle = async (id: number) => {
    const res: any = await redeemApi.toggle(id)
    message.success(res.message)
    fetchCodes()
  }

  const handleViewRecords = async (code: DirectCode) => {
    setCurrentCode(code.code)
    try {
      const res: any = await redeemApi.getRecords(code.id)
      setRecords(res.records)
      setRecordsModal(true)
    } catch {}
  }

  // 批量删除
  const handleBatchDelete = async () => {
    for (const id of selectedRowKeys) {
      await redeemApi.delete(id)
    }
    message.success(`成功删除 ${selectedRowKeys.length} 个链接`)
    setSelectedRowKeys([])
    fetchCodes()
  }

  // 批量禁用
  const handleBatchDisable = async () => {
    for (const id of selectedRowKeys) {
      const code = codes.find(c => c.id === id)
      if (code?.is_active) {
        await redeemApi.toggle(id)
      }
    }
    message.success(`已禁用 ${selectedRowKeys.length} 个链接`)
    setSelectedRowKeys([])
    fetchCodes()
  }

  const getInviteUrl = (code: string) => `${window.location.origin}/invite/${code}`
  const copyUrl = (code: string) => { navigator.clipboard.writeText(getInviteUrl(code)); message.success('链接已复制') }
  const copyAllUrls = () => { navigator.clipboard.writeText(newCodes.map(c => getInviteUrl(c)).join('\n')); message.success('已复制全部链接') }

  const columns = [
    { 
      title: '邀请链接', 
      dataIndex: 'code', 
      render: (v: string) => (
        <Space>
          <a href={getInviteUrl(v)} target="_blank" rel="noreferrer" style={{ fontSize: 13 }}>/invite/{v}</a>
          <Tooltip title="复制链接"><Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyUrl(v)} /></Tooltip>
        </Space>
      )
    },
    { 
      title: '分组', 
      dataIndex: 'group_name', 
      width: 100,
      render: (v: string, r: DirectCode) => v ? (
        <Tag color={groups.find(g => g.id === r.group_id)?.color}>{v}</Tag>
      ) : <span style={{ color: '#94a3b8' }}>全部</span>
    },
    { title: '备注', dataIndex: 'note', width: 100, render: (v: string) => v || <span style={{ color: '#94a3b8' }}>-</span> },
    { 
      title: '使用情况', 
      width: 100,
      render: (_: any, r: DirectCode) => (
        <Button type="link" size="small" style={{ padding: 0, color: r.used_count >= r.max_uses ? '#ef4444' : '#64748b' }} onClick={() => handleViewRecords(r)}>
          {r.used_count} / {r.max_uses}
        </Button>
      )
    },
    { 
      title: '过期时间', 
      dataIndex: 'expires_at', 
      width: 110,
      render: (v: string) => v ? <span style={{ color: toLocalDate(v)?.isBefore(dayjs()) ? '#ef4444' : '#64748b', fontSize: 13 }}>{formatShortDate(v)}</span> : <span style={{ color: '#94a3b8' }}>永不</span>
    },
    { 
      title: '状态', 
      width: 80,
      render: (_: any, r: DirectCode) => {
        const expired = isExpiredCode(r)
        const used = r.used_count >= r.max_uses
        if (expired) return <Tag color="default">已过期</Tag>
        if (used) return <Tag color="default">已用完</Tag>
        return <Tag color={r.is_active ? 'green' : 'default'}>{r.is_active ? '有效' : '禁用'}</Tag>
      }
    },
    {
      title: '操作', 
      width: 120,
      render: (_: any, r: DirectCode) => (
        <Space size={4}>
          <Tooltip title="查看记录"><Button size="small" type="text" icon={<EyeOutlined />} onClick={() => handleViewRecords(r)} /></Tooltip>
          <Tooltip title={r.is_active ? '禁用' : '启用'}><Button size="small" type="text" icon={r.is_active ? <StopOutlined /> : <CheckOutlined />} onClick={() => handleToggle(r.id)} /></Tooltip>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)}><Tooltip title="删除"><Button size="small" type="text" danger icon={<DeleteOutlined />} /></Tooltip></Popconfirm>
        </Space>
      ),
    },
  ]

  const recordColumns = [
    { title: '邮箱', dataIndex: 'email' },
    { title: '加入 Team', dataIndex: 'team_name' },
    { title: '状态', dataIndex: 'status', width: 80, render: (v: string) => <Tag color={v === 'success' ? 'green' : 'default'}>{v === 'success' ? '成功' : v}</Tag> },
    { title: '邀请时间', dataIndex: 'created_at', width: 150, render: (v: string) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    { title: '接受时间', dataIndex: 'accepted_at', width: 150, render: (v: string) => v ? formatDate(v, 'YYYY-MM-DD HH:mm') : <span style={{ color: '#94a3b8' }}>未接受</span> },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e' }}>直接邀请链接</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>无需登录，点击链接即可邀请（适合闲鱼等渠道）</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setNewCodes([]); setModalOpen(true) }} size="large" style={{ borderRadius: 12, height: 44 }}>生成链接</Button>
      </div>

      {/* 使用说明 */}
      <Collapse 
        ghost 
        style={{ marginBottom: 16, background: 'rgba(59, 130, 246, 0.05)', borderRadius: 12 }}
        items={[{
          key: '1',
          label: <span style={{ color: '#3b82f6' }}><QuestionCircleOutlined style={{ marginRight: 8 }} />使用说明</span>,
          children: (
            <div style={{ color: '#64748b', fontSize: 13, lineHeight: 1.8 }}>
              <p><strong>适用场景：</strong>闲鱼、淘宝等渠道销售，用户无需登录即可使用</p>
              <p><strong>使用流程：</strong></p>
              <ol style={{ paddingLeft: 20, margin: '8px 0' }}>
                <li>点击「生成链接」创建邀请链接</li>
                <li>复制链接发送给买家</li>
                <li>买家打开链接，输入邮箱即可收到 ChatGPT Team 邀请</li>
                <li>买家在邮箱中点击接受邀请，完成加入</li>
              </ol>
              <p><strong>建议设置：</strong></p>
              <ul style={{ paddingLeft: 20, margin: '8px 0' }}>
                <li>每个链接可用次数设为 <strong>1</strong>，一人一链接，方便追踪</li>
                <li>备注填写订单号，便于售后查询</li>
                <li>可设置有效期，过期自动失效</li>
              </ul>
            </div>
          )
        }]}
      />

      <Card bodyStyle={{ padding: 0 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Radio.Group value={filter} onChange={e => setFilter(e.target.value)} buttonStyle="solid">
            <Radio.Button value="all">全部 ({stats.all})</Radio.Button>
            <Radio.Button value="available">可用 ({stats.available})</Radio.Button>
            <Radio.Button value="used">已用完 ({stats.used})</Radio.Button>
            <Radio.Button value="expired">已过期 ({stats.expired})</Radio.Button>
          </Radio.Group>
          {selectedRowKeys.length > 0 && (
            <Space>
              <span style={{ color: '#64748b' }}>已选 {selectedRowKeys.length} 项</span>
              <Popconfirm title={`确定禁用 ${selectedRowKeys.length} 个链接？`} onConfirm={handleBatchDisable} okText="禁用" cancelText="取消">
                <Button size="small" icon={<StopOutlined />}>批量禁用</Button>
              </Popconfirm>
              <Popconfirm title={`确定删除 ${selectedRowKeys.length} 个链接？`} onConfirm={handleBatchDelete} okText="删除" cancelText="取消">
                <Button size="small" danger icon={<DeleteOutlined />}>批量删除</Button>
              </Popconfirm>
            </Space>
          )}
        </div>
        <Table 
          dataSource={filteredCodes} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 15, showTotal: total => `共 ${total} 个` }}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys as number[]),
          }}
        />
      </Card>

      <Modal title="生成直接邀请链接" open={modalOpen} onOk={handleCreate} onCancel={() => setModalOpen(false)} width={520} okText="生成" cancelText="取消" confirmLoading={creating}>
        {newCodes.length > 0 ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 500 }}>已生成 {newCodes.length} 个邀请链接</span>
              <Button size="small" icon={<CopyOutlined />} onClick={copyAllUrls}>复制全部</Button>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 12, maxHeight: 300, overflow: 'auto' }}>
              {newCodes.map(code => (
                <div key={code} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #e2e8f0' }}>
                  <a href={getInviteUrl(code)} target="_blank" rel="noreferrer" style={{ fontSize: 13 }}><LinkOutlined style={{ marginRight: 6 }} />{getInviteUrl(code)}</a>
                  <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyUrl(code)} />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Form form={form} layout="vertical" initialValues={{ count: 1, max_uses: 1 }}>
            <Form.Item name="group_id" label="分配到分组" extra="选择后，使用此链接的用户只会被分配到该分组的 Team">
              <Select placeholder="不选则从所有 Team 分配" allowClear>
                {groups.map(g => <Select.Option key={g.id} value={g.id}><Space><div style={{ width: 10, height: 10, borderRadius: 2, background: g.color }} />{g.name}</Space></Select.Option>)}
              </Select>
            </Form.Item>
            <Form.Item name="count" label="生成数量" rules={[{ required: true }]}><InputNumber min={1} max={100} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="max_uses" label="每个链接可用次数" rules={[{ required: true }]} extra="建议设为 1，一人一链接"><InputNumber min={1} max={100} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="expires_days" label="有效天数"><InputNumber min={1} placeholder="不填则永不过期" style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="note" label="备注/订单号"><Input placeholder="如：闲鱼订单123456" /></Form.Item>
          </Form>
        )}
      </Modal>

      <Modal title={`使用记录 - ${currentCode}`} open={recordsModal} onCancel={() => setRecordsModal(false)} footer={null} width={700}>
        <Table dataSource={records} columns={recordColumns} rowKey="id" pagination={false} size="small" locale={{ emptyText: '暂无使用记录' }} />
      </Modal>
    </div>
  )
}
