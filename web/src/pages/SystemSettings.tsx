import { useEffect, useState } from 'react';
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Slider,
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

const AI_PRESETS: Record<string, { base_url: string; chat_model: string; emb_model: string }> = {
  ollama: { base_url: 'http://localhost:11434/v1', chat_model: 'qwen2.5:14b', emb_model: '' },
  lm_studio: { base_url: 'http://localhost:1234/v1', chat_model: '', emb_model: '' },
  openai: { base_url: 'https://api.openai.com/v1', chat_model: 'gpt-4o-mini', emb_model: 'text-embedding-3-small' },
  azure_openai: { base_url: 'https://<resource>.openai.azure.com/', chat_model: '', emb_model: '' },
  deepseek: { base_url: 'https://api.deepseek.com/v1', chat_model: 'deepseek-chat', emb_model: '' },
  zhipu: { base_url: 'https://open.bigmodel.cn/api/paas/v4', chat_model: 'glm-4-flash', emb_model: 'embedding-3' },
  qwen: { base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', chat_model: 'qwen-plus', emb_model: 'text-embedding-v3' },
  moonshot: { base_url: 'https://api.moonshot.cn/v1', chat_model: 'moonshot-v1-8k', emb_model: '' },
  yi: { base_url: 'https://api.lingyiwanwu.com/v1', chat_model: 'yi-lightning', emb_model: '' },
  gemini: { base_url: 'https://generativelanguage.googleapis.com/v1beta/openai', chat_model: 'gemini-2.0-flash', emb_model: 'text-embedding-004' },
  anthropic: { base_url: 'https://api.anthropic.com/v1', chat_model: 'claude-3-5-sonnet-20241022', emb_model: '' },
  custom_openai: { base_url: '', chat_model: '', emb_model: '' },
};

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
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(
    localStorage.getItem('chem_theme') === 'dark' ? 'dark' : 'light',
  );
  const [fontScale, setFontScale] = useState(() => {
    const v = Number(localStorage.getItem('chem_font_scale') || '1');
    return Number.isFinite(v) && v >= 0.8 && v <= 1.4 ? v : 1;
  });

  const notifySettings = () => {
    window.dispatchEvent(new Event('chem-ui-settings'));
  };

  const [llm, setLlm] = useState<any>({});
  const [emb, setEmb] = useState<any>({});
  const [testing, setTesting] = useState(false);
  const [savingAi, setSavingAi] = useState(false);

  const PROVIDERS = [
    'ollama',
    'lm_studio',
    'openai',
    'azure_openai',
    'deepseek',
    'zhipu',
    'qwen',
    'moonshot',
    'yi',
    'gemini',
    'anthropic',
    'custom_openai',
  ];

  const changeTheme = (value: 'light' | 'dark') => {
    setThemeMode(value);
    localStorage.setItem('chem_theme', value);
    notifySettings();
  };

  const changeFontScale = (value: number) => {
    setFontScale(value);
    localStorage.setItem('chem_font_scale', String(value));
    notifySettings();
  };

  const changeShowThinking = (checked: boolean) => {
    setShowThinking(checked);
    localStorage.setItem('chem_show_thinking', checked ? '1' : '0');
    message.success(checked ? '已开启：AI 显示思考过程' : '已关闭：AI 不显示思考过程');
  };

  const loadAll = async () => {
    setLoading(true);
    try {
      const [c, u, r, a, l, e] = await Promise.all([
        api.get('/admin/config'),
        api.get('/admin/users'),
        api.get('/admin/roles'),
        api.get('/admin/audit', { params: { page: 1, limit: 100 } }),
        api.get('/admin/llm/config'),
        api.get('/admin/embedding/config'),
      ]);
      setConfigs(c.data || []);
      setUsers(u.data || []);
      setRoles(r.data || []);
      setAudits(a.data?.items || []);
      setAuditTotal(a.data?.total || 0);
      setLlm(l.data || {});
      setEmb(e.data || {});
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '系统设置加载失败');
    } finally {
      setLoading(false);
    }
  };

  const saveLlm = async () => {
    setSavingAi(true);
    try {
      await api.post('/admin/llm/config', {
        provider: llm.provider,
        base_url: llm.base_url,
        model: llm.model,
        api_key: llm.api_key_input || '',
        azure_deployment: llm.azure_deployment || '',
        azure_api_version: llm.azure_api_version || '',
        max_tokens: Number(llm.max_tokens || 4096),
        temperature: Number(llm.temperature || 0.7),
      });
      message.success('LLM 配置已保存并生效');
      loadAll();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : 'LLM 保存失败');
    } finally {
      setSavingAi(false);
    }
  };

  const saveEmb = async () => {
    setSavingAi(true);
    try {
      await api.post('/admin/embedding/config', {
        provider: emb.provider,
        base_url: emb.base_url,
        model: emb.model,
        api_key: emb.api_key_input || '',
      });
      message.success('Embedding 配置已保存并生效');
      loadAll();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : 'Embedding 保存失败');
    } finally {
      setSavingAi(false);
    }
  };

  const testLlm = async () => {
    setTesting(true);
    try {
      const res = await api.post('/admin/llm/test', {
        provider: llm.provider,
        base_url: llm.base_url,
        model: llm.model,
        api_key: llm.api_key_input || '',
        test_type: 'chat',
      });
      if (res.data?.success) {
        message.success(`连接成功，延迟 ${res.data.latency_ms}ms`);
      } else {
        message.error(res.data?.error || '连接失败');
      }
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '测试失败');
    } finally {
      setTesting(false);
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
            key: 'ai',
            label: 'AI 服务接入',
            children: (
              <Space direction="vertical" size={18} style={{ width: '100%' }}>
                <Card title="LLM（对话/推理）" style={{ maxWidth: 860 }}>
                  <Space wrap>
                    <Select
                      style={{ width: 200 }}
                      value={llm.provider}
                      onChange={(v) => {
                        const p = AI_PRESETS[v] || AI_PRESETS.custom_openai;
                        setLlm({ ...llm, provider: v, base_url: p.base_url, model: p.chat_model });
                      }}
                      options={PROVIDERS.map((p) => ({ label: p, value: p }))}
                    />
                    <Input
                      style={{ width: 320 }}
                      placeholder="Base URL"
                      value={llm.base_url || ''}
                      onChange={(e) => setLlm({ ...llm, base_url: e.target.value })}
                    />
                    <Input
                      style={{ width: 220 }}
                      placeholder="Model"
                      value={llm.model || ''}
                      onChange={(e) => setLlm({ ...llm, model: e.target.value })}
                    />
                    <Input.Password
                      style={{ width: 300 }}
                      placeholder={llm.api_key ? `已配置：${llm.api_key}（留空保持不变）` : 'API Key'}
                      value={llm.api_key_input || ''}
                      onChange={(e) => setLlm({ ...llm, api_key_input: e.target.value })}
                    />
                  </Space>
                  {llm.provider === 'azure_openai' && (
                    <Space style={{ marginTop: 10 }}>
                      <Input
                        style={{ width: 260 }}
                        placeholder="Azure Deployment"
                        value={llm.azure_deployment || ''}
                        onChange={(e) => setLlm({ ...llm, azure_deployment: e.target.value })}
                      />
                      <Input
                        style={{ width: 160 }}
                        placeholder="API Version"
                        value={llm.azure_api_version || '2024-02-01'}
                        onChange={(e) => setLlm({ ...llm, azure_api_version: e.target.value })}
                      />
                    </Space>
                  )}
                  <Space style={{ marginTop: 12 }}>
                    <Input
                      style={{ width: 120 }}
                      type="number"
                      addonBefore="Max tokens"
                      value={llm.max_tokens ?? 4096}
                      onChange={(e) => setLlm({ ...llm, max_tokens: Number(e.target.value) })}
                    />
                    <Input
                      style={{ width: 110 }}
                      type="number"
                      step={0.1}
                      addonBefore="温度"
                      value={llm.temperature ?? 0.7}
                      onChange={(e) => setLlm({ ...llm, temperature: Number(e.target.value) })}
                    />
                  </Space>
                  <div style={{ marginTop: 14 }}>
                    <Space>
                      <Button type="primary" loading={savingAi} onClick={saveLlm}>
                        保存 LLM
                      </Button>
                      <Button loading={testing} onClick={testLlm}>
                        测试连接
                      </Button>
                    </Space>
                  </div>
                </Card>
                <Card title="Embedding（知识库向量化）" style={{ maxWidth: 860 }}>
                  <Space wrap>
                    <Select
                      style={{ width: 200 }}
                      value={emb.provider || 'same_as_llm'}
                      onChange={(v) => {
                        const p = v === 'same_as_llm' ? null : AI_PRESETS[v] || null;
                        setEmb({
                          ...emb,
                          provider: v,
                          base_url: v === 'same_as_llm' ? '' : p?.base_url || '',
                          model: v === 'same_as_llm' ? '' : p?.emb_model || '',
                        });
                      }}
                      options={[
                        { label: 'same_as_llm（复用 LLM）', value: 'same_as_llm' },
                        ...PROVIDERS.map((p) => ({ label: p, value: p })),
                      ]}
                    />
                    <Input
                      style={{ width: 320 }}
                      placeholder="Base URL"
                      value={emb.base_url || ''}
                      onChange={(e) => setEmb({ ...emb, base_url: e.target.value })}
                    />
                    <Input
                      style={{ width: 220 }}
                      placeholder="Embedding Model"
                      value={emb.model || ''}
                      onChange={(e) => setEmb({ ...emb, model: e.target.value })}
                    />
                    <Input.Password
                      style={{ width: 300 }}
                      placeholder={emb.api_key ? `已配置：${emb.api_key}（留空保持不变）` : 'API Key'}
                      value={emb.api_key_input || ''}
                      onChange={(e) => setEmb({ ...emb, api_key_input: e.target.value })}
                    />
                  </Space>
                  <div style={{ marginTop: 14 }}>
                    <Button type="primary" loading={savingAi} onClick={saveEmb}>
                      保存 Embedding
                    </Button>
                  </div>
                </Card>
                <Card title="支持的接入方式" size="small" style={{ maxWidth: 860 }}>
                  <Typography.Paragraph type="secondary">
                    Ollama / LM Studio / OpenAI / Azure OpenAI / DeepSeek / Zhipu(智谱) / Qwen(通义) /
                    Moonshot(Kimi) / Yi / Gemini / Anthropic / 自定义 OpenAI 兼容接口。
                    选择厂商会自动带出 Base URL 与推荐模型，再填入 API Key 即可。
                  </Typography.Paragraph>
                </Card>
              </Space>
            ),
          },
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
                  <Space align="center" style={{ width: '100%' }}>
                    <span style={{ width: 90 }}>主题</span>
                    <Select
                      value={themeMode}
                      onChange={changeTheme}
                      style={{ width: 160 }}
                      options={[
                        { value: 'light', label: '浅色' },
                        { value: 'dark', label: '深色' },
                      ]}
                    />
                  </Space>
                  <div style={{ width: 420 }}>
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Typography.Text strong>UI 字号</Typography.Text>
                      <Typography.Text type="secondary">{Math.round(fontScale * 100)}%</Typography.Text>
                    </Space>
                    <Slider
                      min={0.8}
                      max={1.4}
                      step={0.05}
                      value={fontScale}
                      onChange={changeFontScale}
                      marks={{ 0.8: '小', 1: '标准', 1.4: '大' }}
                    />
                  </div>
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
