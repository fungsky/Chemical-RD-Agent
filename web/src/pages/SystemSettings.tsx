import { useEffect, useState } from 'react';
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';

interface ConfigRow {
  key: string;
  value?: string;
  description?: string;
}

interface UserRow {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  is_active: boolean;
  is_superadmin?: boolean;
  created_at?: string;
  roles?: string[];
}

interface RoleRow {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  is_system?: boolean;
}

interface AuditRow {
  id: number;
  timestamp?: string;
  username?: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details?: string;
  status?: string;
}

function ConfigRowEditor({ row, onSave }: { row: ConfigRow; onSave: (value: string) => void }) {
  const [value, setValue] = useState(row.value || '');
  const secretLike = row.key.toLowerCase().includes('key') || row.key.toLowerCase().includes('secret');
  return (
    <Space.Compact style={{ width: '100%' }}>
      <Input value={value} onChange={(e) => setValue(e.target.value)} type={secretLike ? 'password' : 'text'} />
      <Button onClick={() => onSave(value)}>保存</Button>
    </Space.Compact>
  );
}

export default function SystemSettings() {
  const { message } = App.useApp();
  const [configs, setConfigs] = useState<ConfigRow[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [audits, setAudits] = useState<AuditRow[]>([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const [showThinking, setShowThinking] = useState(
    localStorage.getItem('chem_show_thinking') !== '0',
  );

  const changeShowThinking = (checked: boolean) => {
    setShowThinking(checked);
    localStorage.setItem('chem_show_thinking', checked ? '1' : '0');
    message.success(checked ? '已开启：AI 显示思考过程' : '已关闭：AI 不显示思考过程');
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      const [c, u, r, a] = await Promise.all([
        api.get('/admin/config'),
        api.get('/admin/users'),
        api.get('/admin/roles'),
        api.get('/admin/audit', { params: { page: 1, limit: 100 } }),
      ]);
      setConfigs(c.data || []);
      setUsers(u.data || []);
      setRoles(r.data || []);
      setAudits(a.data?.items || []);
      setAuditTotal(a.data?.total || 0);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '系统设置加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const saveConfig = async (row: ConfigRow, value: string) => {
    try {
      await api.put('/admin/config', {
        configs: [{ key: row.key, value, description: row.description }],
      });
      message.success(`已保存 ${row.key}`);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '配置保存失败');
    }
  };

  const createUser = async (values: any) => {
    setSaving(true);
    try {
      const created = await api.post('/admin/users', {
        username: values.username,
        password: values.password,
        email: values.email,
        full_name: values.full_name,
      });
      if (values.role_ids?.length) {
        await api.put(`/admin/users/${created.data.id}/roles`, { role_ids: values.role_ids });
      }
      message.success('用户已创建');
      setUserOpen(false);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '创建失败');
    } finally {
      setSaving(false);
    }
  };

  const toggleUser = async (user: UserRow) => {
    try {
      await api.post(`/admin/users/${user.id}/toggle-active`);
      message.success(`${user.username} 已${user.is_active ? '停用' : '启用'}`);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '操作失败');
    }
  };

  const configColumns: ColumnsType<ConfigRow> = [
    { title: '配置项', dataIndex: 'key', width: 260 },
    {
      title: '值',
      dataIndex: 'value',
      render: (v, row) => <ConfigRowEditor key={row.key} row={row} onSave={(value) => saveConfig(row, value)} />,
    },
    { title: '说明', dataIndex: 'description' },
  ];

  const userColumns: ColumnsType<UserRow> = [
    { title: '用户名', dataIndex: 'username' },
    { title: '姓名', dataIndex: 'full_name' },
    { title: '邮箱', dataIndex: 'email' },
    { title: '角色', dataIndex: 'roles', render: (v: string[]) => (v || []).map((r) => <Tag key={r}>{r}</Tag>) },
    {
      title: '状态',
      dataIndex: 'is_active',
      render: (v) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '停用'}</Tag>,
    },
    {
      title: '操作',
      render: (_, user) =>
        !user.is_superadmin && (
          <Switch checked={user.is_active} checkedChildren="启用" unCheckedChildren="停用" onChange={() => toggleUser(user)} />
        ),
    },
  ];

  const roleColumns: ColumnsType<RoleRow> = [
    { title: '角色名', dataIndex: 'name' },
    { title: '显示名', dataIndex: 'display_name' },
    { title: '描述', dataIndex: 'description' },
    {
      title: '系统角色',
      dataIndex: 'is_system',
      render: (v) => (v ? <Tag color="blue">系统</Tag> : <Tag>自定义</Tag>),
    },
  ];

  const auditColumns: ColumnsType<AuditRow> = [
    { title: 'ID', dataIndex: 'id', width: 70 },
    { title: '时间', dataIndex: 'timestamp', width: 180 },
    { title: '用户', dataIndex: 'username', width: 120 },
    { title: '动作', dataIndex: 'action', width: 180 },
    { title: '对象', dataIndex: 'resource_type', width: 120 },
    { title: '资源ID', dataIndex: 'resource_id', width: 140 },
    { title: '状态', dataIndex: 'status', width: 90 },
  ];

  return (
    <Card style={{ borderRadius: 12 }} loading={loading}>
      <Tabs
        items={[
          {
            key: 'ux',
            label: '界面功能',
            children: (
              <Card style={{ maxWidth: 640 }}>
                <Space direction="vertical" size={12}>
                  <Space align="center">
                    <Switch checked={showThinking} onChange={changeShowThinking} />
                    <div>
                      <Typography.Text strong>显示 AI 思考过程</Typography.Text>
                      <br />
                      <Typography.Text type="secondary">
                        开启后，智能体模式的每步推理、工具调用与分析过程会在问答下方折叠展示。
                      </Typography.Text>
                    </div>
                  </Space>
                </Space>
              </Card>
            ),
          },
          {
            key: 'config',
            label: '系统配置',
            children: (
              <Table
                rowKey="key"
                size="small"
                dataSource={configs}
                columns={configColumns}
                pagination={false}
              />
            ),
          },
          {
            key: 'users',
            label: '用户管理',
            children: (
              <>
                <Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 12 }} onClick={() => setUserOpen(true)}>
                  新建用户
                </Button>
                <Table rowKey="id" dataSource={users} columns={userColumns} pagination={false} />
              </>
            ),
          },
          {
            key: 'roles',
            label: '角色权限',
            children: <Table rowKey="id" dataSource={roles} columns={roleColumns} pagination={false} />,
          },
          {
            key: 'audit',
            label: '审计日志',
            children: (
              <Table
                rowKey="id"
                dataSource={audits}
                columns={auditColumns}
                pagination={{ total: auditTotal, pageSize: 50 }}
              />
            ),
          },
        ]}
      />

      <Modal
        title="新建用户"
        open={userOpen}
        onCancel={() => setUserOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={saving}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={createUser}>
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, min: 4 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="full_name" label="姓名">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input />
          </Form.Item>
          <Form.Item name="role_ids" label="角色">
            <Select
              mode="multiple"
              options={roles.map((r) => ({ label: r.display_name, value: r.id }))}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
