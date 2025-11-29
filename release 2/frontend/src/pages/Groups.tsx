import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Modal, Form, Input, message, Popconfirm, ColorPicker } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import { groupApi } from '../api'

interface Group {
  id: number
  name: string
  description?: string
  color: string
  team_count: number
  total_seats: number
  used_seats: number
}

export default function Groups() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<Group | null>(null)
  const [form] = Form.useForm()

  const fetchGroups = async () => {
    setLoading(true)
    try {
      const res: any = await groupApi.list()
      setGroups(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGroups()
  }, [])

  const handleCreate = () => {
    setEditingGroup(null)
    form.resetFields()
    form.setFieldsValue({ color: '#1890ff' })
    setModalOpen(true)
  }

  const handleEdit = (group: Group) => {
    setEditingGroup(group)
    form.setFieldsValue({
      name: group.name,
      description: group.description,
      color: group.color
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    const color = typeof values.color === 'string' ? values.color : values.color?.toHexString?.() || '#1890ff'
    
    try {
      if (editingGroup) {
        await groupApi.update(editingGroup.id, { ...values, color })
        message.success('更新成功')
      } else {
        await groupApi.create({ ...values, color })
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchGroups()
    } catch {}
  }

  const handleDelete = async (id: number) => {
    try {
      await groupApi.delete(id)
      message.success('删除成功')
      fetchGroups()
    } catch {}
  }

  const columns = [
    {
      title: '分组名称',
      dataIndex: 'name',
      render: (v: string, r: Group) => (
        <Space>
          <div style={{ width: 12, height: 12, borderRadius: 3, background: r.color }} />
          <span style={{ fontWeight: 500 }}>{v}</span>
        </Space>
      )
    },
    { title: '描述', dataIndex: 'description', render: (v: string) => v || '-' },
    { title: 'Team 数量', dataIndex: 'team_count', width: 100 },
    {
      title: '座位使用',
      width: 120,
      render: (_: any, r: Group) => (
        <span>
          {r.used_seats} / {r.total_seats}
          {r.total_seats > 0 && (
            <span style={{ color: '#94a3b8', marginLeft: 4 }}>
              ({Math.round(r.used_seats / r.total_seats * 100)}%)
            </span>
          )}
        </span>
      )
    },
    {
      title: '操作',
      width: 120,
      render: (_: any, r: Group) => (
        <Space>
          <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          <Popconfirm
            title="确定删除？"
            description="删除前请确保该分组下没有 Team"
            onConfirm={() => handleDelete(r.id)}
          >
            <Button type="text" size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e' }}>Team 分组</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>
            将 Team 分组管理，不同渠道的用户分配到不同分组
          </p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} size="large" style={{ borderRadius: 12, height: 44 }}>
          新建分组
        </Button>
      </div>

      <Card>
        <Table
          dataSource={groups}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingGroup ? '编辑分组' : '新建分组'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item name="name" label="分组名称" rules={[{ required: true, message: '请输入分组名称' }]}>
            <Input placeholder="如：LinuxDO 专用、闲鱼售卖" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input placeholder="可选" />
          </Form.Item>
          <Form.Item name="color" label="标签颜色">
            <ColorPicker />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
