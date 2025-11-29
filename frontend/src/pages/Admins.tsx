import { useEffect, useState } from 'react'
import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, UserOutlined } from '@ant-design/icons'
import { formatDate } from '../utils/date'
import api from '../api'

interface Admin {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

const roleOptions = [
  { value: 'admin', label: '管理员', color: 'red' },
  { value: 'operator', label: '操作员', color: 'blue' },
]

export default function Admins() {
  const [admins, setAdmins] = useState<Admin[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingAdmin, setEditingAdmin] = useState<Admin | null>(null)
  const [form] = Form.useForm()

  const fetchAdmins = async () => {
    setLoading(true)
    try {
      const res: any = await api.get('/admins')
      setAdmins(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAdmins() }, [])

  const handleCreate = () => {
    setEditingAdmin(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (admin: Admin) => {
    setEditingAdmin(admin)
    form.setFieldsValue({ ...admin, password: '' })
    setModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/admins/${id}`)
      message.success('删除成功')
      fetchAdmins()
    } catch {}
  }

  const handleSubmit = async () => {
    const values = await form.validateFields()
    try {
      if (editingAdmin) {
        // 编辑时，如果密码为空则不传
        const data: any = { email: values.email, role: values.role }
        if (values.password) data.password = values.password
        await api.put(`/admins/${editingAdmin.id}`, data)
        message.success('更新成功')
      } else {
        await api.post('/admins', values)
        message.success('创建成功')
      }
      setModalOpen(false)
      fetchAdmins()
    } catch {}
  }

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      render: (v: string) => (
        <Space>
          <UserOutlined style={{ color: '#64748b' }} />
          <span style={{ fontWeight: 500 }}>{v}</span>
        </Space>
      )
    },
    { title: '邮箱', dataIndex: 'email' },
    {
      title: '角色',
      dataIndex: 'role',
      width: 100,
      render: (v: string) => {
        const role = roleOptions.find(r => r.value === v)
        return <Tag color={role?.color}>{role?.label || v}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 80,
      render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? '正常' : '禁用'}</Tag>
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 160,
      render: (v: string) => <span style={{ color: '#64748b', fontSize: 13 }}>{formatDate(v, 'YYYY-MM-DD HH:mm')}</span>
    },
    {
      title: '操作',
      width: 120,
      render: (_: any, r: Admin) => (
        <Space size={4}>
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => handleEdit(r)} />
          <Popconfirm title="确定删除此管理员？" onConfirm={() => handleDelete(r.id)} okText="删除" cancelText="取消">
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h2 style={{ fontSize: 26, fontWeight: 700, margin: 0, color: '#1a1a2e' }}>管理员管理</h2>
          <p style={{ color: '#64748b', fontSize: 14, margin: '8px 0 0' }}>管理系统管理员账号</p>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} size="large" style={{ borderRadius: 12, height: 44 }}>
          添加管理员
        </Button>
      </div>

      <Card bodyStyle={{ padding: 0 }}>
        <Table
          dataSource={admins}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingAdmin ? '编辑管理员' : '添加管理员'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: !editingAdmin, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" disabled={!!editingAdmin} />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱' }
            ]}
          >
            <Input placeholder="邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            label={editingAdmin ? '新密码（留空不修改）' : '密码'}
            rules={[{ required: !editingAdmin, message: '请输入密码' }]}
          >
            <Input.Password placeholder={editingAdmin ? '留空不修改' : '密码'} />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
            initialValue="admin"
          >
            <Select>
              {roleOptions.map(r => (
                <Select.Option key={r.value} value={r.value}>{r.label}</Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
