import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, message, Popconfirm, Tooltip, Radio } from 'antd'
import { PlusOutlined, DeleteOutlined, CopyOutlined, StopOutlined, CheckOutlined, EyeOutlined } from '@ant-design/icons'
import { redeemApi } from '../api'
import { formatDate, formatDateOnly, toLocalDate } from '../utils/date'
import dayjs from 'dayjs'

interface RedeemCode {
  id: number
  code: string
  max_uses: number
  used_count: number
  expires_at?: string
  is_active: boolean
  created_at: string
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

export default function RedeemCodes() {
  const [codes, setCodes] = useState<RedeemCode[]>([])
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
      const res: any = await redeemApi.list(undefined, undefined, 'linuxdo')
      setCodes(res.codes)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCodes()
  }, [])

  // 根据筛选条件过滤
  const isExpiredCode = (code: RedeemCode) => code.expires_at && toLocalDate(code.expires_at)?.isBefore(dayjs())
  
  const filteredCodes = codes.filter(code => {
    const isExpired = isExpiredCode(code)
    const isUsedUp = code.used_count >= code.max_uses
    const isAvailable = code.is_active && !isExpired && !isUsedUp

    switch (filter) {
      case 'available':
        return isAvailable
      case 'used':
        return isUsedUp
      case 'expired':
        return isExpired
      default:
        return true
    }
  })

  // 统计数量
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
      const res: any = await redeemApi.batchCreate({
        ...values,
        code_type: 'linuxdo'
      })
      setNewCodes(res.codes)
      message.success(`成功创建 ${res.count} 个兑换码`)
      fetchCodes()
    } catch {
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

  const handleViewRecords = async (code: RedeemCode) => {
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
    message.success(`成功删除 ${selectedRowKeys.length} 个兑换码`)
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
    message.success(`已禁用 ${selectedRowKeys.length} 个兑换码`)
    setSelectedRowKeys([])
    fetchCodes()
  }

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code)
    message.success('已复制')
  }

  const copyAllCodes = () => {
    navigator.clipboard.writeText(newCodes.join('\n'))
    message.success('已复制全部')
  }

  const columns = [
    { 
      title: '兑换码', 
      dataIndex: 'code', 
      render: (v: string) => (
        <Space>
          <code style={{ fontSize: 13 }}>{v}</code>
          <Tooltip title="复制">
            <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyCode(v)} />
          </Tooltip>
        </Space>
      )
    },

    { 
      title: '使用情况', 
      width: 100,
      render: (_: any, r: RedeemCode) => (
        <Button type="link" size="small" style={{ padding: 0, color: r.used_count >= r.max_uses ? '#ef4444' : '#64748b' }} onClick={() => handleViewRecords(r)}>
          {r.used_count} / {r.max_uses}
        </Button>
      )
    },
    { 
      title: '过期时间', 
      dataIndex: 'expires_at', 
      width: 140,
      render: (v: string) => v ? (
        <span style={{ color: toLocalDate(v)?.isBefore(dayjs()) ? '#ef4444' : '#64748b', fontSize: 13 }}>
          {formatDateOnly(v)}
        </span>
      ) : <span style={{ color: '#94a3b8' }}>永不</span>
    },
    { 
      title: '状态', 
      dataIndex: 'is_active', 
      width: 80,
      render: (v: boolean, r: RedeemCode) => {
        const expired = isExpiredCode(r)
        const used = r.used_count >= r.max_uses
        if (expired) return <Tag color="default">已过期</Tag>
        if (used) return <Tag color="default">已用完</Tag>
        return <Tag color={v ? 'green' : 'default'}>{v ? '有效' : '禁用'}</Tag>
      }
    },
    { 
      title: '创建时间', 
      dataIndex: 'created_at', 
      width: 140,
      render: (v: string) => <span style={{ color: '#64748b', fontSize: 13 }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span>
    },
    {
      title: '操作', 
      width: 120,
      render: (_: any, r: RedeemCode) => (
        <Space size={4}>
          <Tooltip title="查看记录">
            <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => handleViewRecords(r)} />
          </Tooltip>
          <Tooltip title={r.is_active ? '禁用' : '启用'}>
            <Button size="small" type="text" icon={r.is_active ? <StopOutlined /> : <CheckOutlined />} onClick={() => handleToggle(r.id)} />
          </Tooltip>
          <Popconfirm title="确定删除？" onConfirm={() => handleDelete(r.id)} okText="删除" cancelText="取消">
            <Tooltip title="删除">
              <Button size="small" type="text" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
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
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e', letterSpacing: '-0.5px' }}>LinuxDO 兑换码</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>需要 LinuxDO 登录后使用</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { form.resetFields(); setNewCodes([]); setModalOpen(true) }} size="large" style={{ borderRadius: 12, height: 44 }}>
          生成兑换码
        </Button>
      </div>

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
              <Popconfirm title={`确定禁用 ${selectedRowKeys.length} 个兑换码？`} onConfirm={handleBatchDisable} okText="禁用" cancelText="取消">
                <Button size="small" icon={<StopOutlined />}>批量禁用</Button>
              </Popconfirm>
              <Popconfirm title={`确定删除 ${selectedRowKeys.length} 个兑换码？`} onConfirm={handleBatchDelete} okText="删除" cancelText="取消">
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

      <Modal 
        title="生成兑换码" 
        open={modalOpen} 
        onOk={handleCreate} 
        onCancel={() => setModalOpen(false)} 
        width={480} 
        okText="生成" 
        cancelText="取消"
        confirmLoading={creating}
      >
        {newCodes.length > 0 ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontWeight: 500 }}>已生成 {newCodes.length} 个兑换码</span>
              <Button size="small" icon={<CopyOutlined />} onClick={copyAllCodes}>复制全部</Button>
            </div>
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: 12, maxHeight: 300, overflow: 'auto' }}>
              {newCodes.map(code => (
                <div key={code} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #e2e8f0' }}>
                  <code>{code}</code>
                  <Button type="text" size="small" icon={<CopyOutlined />} onClick={() => copyCode(code)} />
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Form form={form} layout="vertical" initialValues={{ count: 1, max_uses: 1, prefix: '' }}>
            <Form.Item name="count" label="生成数量" rules={[{ required: true }]}>
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="max_uses" label="每码可用次数" rules={[{ required: true }]}>
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="expires_days" label="有效天数">
              <InputNumber min={1} placeholder="不填则永不过期" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="prefix" label="前缀">
              <Input placeholder="如 VIP-、PROMO-" />
            </Form.Item>
          </Form>
        )}
      </Modal>

      <Modal title={`使用记录 - ${currentCode}`} open={recordsModal} onCancel={() => setRecordsModal(false)} footer={null} width={700}>
        <Table dataSource={records} columns={recordColumns} rowKey="id" pagination={false} size="small" locale={{ emptyText: '暂无使用记录' }} />
      </Modal>
    </div>
  )
}
