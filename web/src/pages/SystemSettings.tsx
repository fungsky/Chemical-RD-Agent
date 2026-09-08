import { useEffect, useState, type ReactNode } from 'react';
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
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
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

const AUDIT_STATUS_META: Record<string, { label: string; color: string }> = {
  success: { label: '成功', color: 'green' },
  failed: { label: '失败', color: 'red' },
  error: { label: '错误', color: 'red' },
  warning: { label: '警告', color: 'orange' },
  skipped: { label: '已跳过', color: 'default' },
};

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

const AI_MODELS: Record<string, string[]> = {
  ollama: ['qwen2.5:14b', 'qwen2.5:32b', 'llama3.1:8b', 'glm4:9b'],
  lm_studio: ['qwen2.5-14b-instruct', 'mistral-nemo', 'gemma-2-9b'],
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4.1-mini', 'gpt-4.1'],
  azure_openai: ['gpt-4o', 'gpt-4o-mini'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner'],
  zhipu: ['glm-4-flash', 'glm-4-air', 'glm-4-plus', 'glm-4.5', 'glm-5', 'glm-5-flash'],
  qwen: ['qwen-plus', 'qwen-turbo', 'qwen-max', 'qwen3-coder-plus'],
  moonshot: ['moonshot-v1-8k', 'moonshot-v1-32k', 'kimi-k2'],
  yi: ['yi-lightning', 'yi-large'],
  gemini: ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-7-sonnet', 'claude-sonnet-4'],
  custom_openai: [],
};

function ConfigRow({ label, tip, children }: { label: string; tip?: string; children: ReactNode }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <Typography.Text strong>{label}</Typography.Text>
      {tip && (
        <div>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {tip}
          </Typography.Text>
        </div>
      )}
      <div style={{ marginTop: 6, maxWidth: 720 }}>{children}</div>
    </div>
  );
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
  const [fetchedModels, setFetchedModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [manualModel, setManualModel] = useState(false);
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

  const fetchModels = async () => {
    if (!llm.base_url) {
      message.warning('请先填写 Base URL 再读取模型列表');
      return;
    }
    setLoadingModels(true);
    try {
      const res = await api.post('/admin/llm/models', {
        provider: llm.provider,
        base_url: llm.base_url,
        api_key: llm.api_key_input || llm.api_key || '',
      });
      if (res.data?.success && res.data?.models?.length) {
        setFetchedModels(res.data.models);
        message.success(`已从服务商读取 ${res.data.models.length} 个模型`);
        if (!llm.model) {
          setLlm((prev: any) => ({ ...prev, model: res.data.models[0] }));
        }
      } else {
        message.error(res.data?.error || '读取模型列表失败，请检查 Base URL / API Key');
      }
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : '读取模型列表失败');
    } finally {
      setLoadingModels(false);
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
        reasoning_effort: llm.reasoning_effort || 'medium',
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
        api_key: llm.api_key_input || llm.api_key || '',
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
    {
      title: '状态',
      dataIndex: 'status',
      width: 90,
      render: (v) => {
        if (!v) return '-';
        const meta = AUDIT_STATUS_META[v] || { label: v, color: 'default' };
        return <Tag color={meta.color}>{meta.label}</Tag>;
      },
    },
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
                  <ConfigRow label="服务商" tip="选择后自动带出 Hermes 同款预设地址与推荐模型">
                    <Select
                      style={{ width: 260 }}
                      value={llm.provider}
                      onChange={(v) => {
                        const p = AI_PRESETS[v] || AI_PRESETS.custom_openai;
                        setFetchedModels([]);
                        setManualModel(false);
                        setLlm({ ...llm, provider: v, base_url: p.base_url, model: p.chat_model });
                      }}
                      options={PROVIDERS.map((p) => ({ label: p, value: p }))}
                    />
                  </ConfigRow>
                  <ConfigRow label="Base URL" tip="OpenAI 兼容接口地址，如 https://open.bigmodel.cn/api/paas/v4">
                    <Input
                      style={{ width: 560 }}
                      placeholder="Base URL"
                      value={llm.base_url || ''}
                      onChange={(e) => setLlm({ ...llm, base_url: e.target.value })}
                    />
                  </ConfigRow>
                  <ConfigRow
                    label="模型 / 模型强度"
                    tip="点击“读取模型列表”后从服务商拉取实际可用模型，并在下拉中选择；也可切换为手动输入"
                  >
                    {manualModel ? (
                      <Space.Compact style={{ width: 560 }}>
                        <Input
                          style={{ width: 420 }}
                          value={llm.model || ''}
                          placeholder="输入自定义模型名，如 glm-4-flash"
                          onChange={(e) => setLlm({ ...llm, model: e.target.value })}
                        />
                        <Button onClick={() => setManualModel(false)}>返回列表</Button>
                      </Space.Compact>
                    ) : (
                      <>
                        <Space.Compact style={{ width: 560 }}>
                          <Select
                            showSearch
                            allowClear
                            style={{ width: 400 }}
                            value={llm.model || undefined}
                            placeholder="读取后从下拉选择模型"
                            optionFilterProp="label"
                            onChange={(v) => setLlm({ ...llm, model: v })}
                            options={(fetchedModels.length
                              ? fetchedModels
                              : AI_MODELS[llm.provider] || []
                            ).map((m) => ({ label: m, value: m }))}
                            notFoundContent={
                              loadingModels ? '正在读取模型列表…' : '暂无模型，请点击右侧“读取模型列表”'
                            }
                          />
                          <Button
                            icon={<ReloadOutlined />}
                            loading={loadingModels}
                            onClick={fetchModels}
                          >
                            读取模型列表
                          </Button>
                        </Space.Compact>
                        <div style={{ marginTop: 4 }}>
                          <Button type="link" size="small" style={{ padding: 0 }} onClick={() => setManualModel(true)}>
                            需要手动输入自定义模型？
                          </Button>
                        </div>
                      </>
                    )}
                  </ConfigRow>
                  <ConfigRow label="API Key" tip="留空表示保持当前已保存密钥不变">
                    <Input.Password
                      style={{ width: 560 }}
                      placeholder={llm.api_key ? `已配置：${llm.api_key}（留空保持不变）` : 'API Key'}
                      value={llm.api_key_input || ''}
                      onChange={(e) => setLlm({ ...llm, api_key_input: e.target.value })}
                    />
                  </ConfigRow>
                  {llm.provider === 'azure_openai' && (
                    <>
                      <ConfigRow label="Azure Deployment">
                        <Input
                          style={{ width: 360 }}
                          placeholder="Azure Deployment"
                          value={llm.azure_deployment || ''}
                          onChange={(e) => setLlm({ ...llm, azure_deployment: e.target.value })}
                        />
                      </ConfigRow>
                      <ConfigRow label="API Version">
                        <Input
                          style={{ width: 240 }}
                          placeholder="API Version"
                          value={llm.azure_api_version || '2024-02-01'}
                          onChange={(e) => setLlm({ ...llm, azure_api_version: e.target.value })}
                        />
                      </ConfigRow>
                    </>
                  )}
                  <ConfigRow label="输出上限 Max tokens" tip="单次回复最大生成 token 数">
                    <Input
                      style={{ width: 180 }}
                      type="number"
                      value={llm.max_tokens ?? 4096}
                      onChange={(e) => setLlm({ ...llm, max_tokens: Number(e.target.value) })}
                    />
                  </ConfigRow>
                  <ConfigRow
                    label="temperature（采样随机性）"
                    tip="LLM 采样参数：值越低越严谨稳定，值越高越发散有创意。研发问答建议 0.1-0.3，起草建议 0.5 左右。"
                  >
                    <div style={{ width: 420 }}>
                      <Slider
                        min={0}
                        max={1}
                        step={0.05}
                        value={llm.temperature ?? 0.7}
                        onChange={(v) => setLlm({ ...llm, temperature: v })}
                        marks={{ 0: '0 严谨', 0.5: '0.5 平衡', 1: '1 发散' }}
                      />
                    </div>
                  </ConfigRow>
                  <ConfigRow
                    label="reasoning_effort（推理强度）"
                    tip="官方级别：none / minimal / low / medium / high / xhigh / max / ultra。越高模型思考越久、成本越高；不支持该参数的模型会自动忽略。"
                  >
                    <Select
                      style={{ width: 240 }}
                      value={llm.reasoning_effort || 'medium'}
                      onChange={(v) => setLlm({ ...llm, reasoning_effort: v })}
                      options={['none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'].map((v) => ({
                        label: v,
                        value: v,
                      }))}
                    />
                  </ConfigRow>
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
                  <ConfigRow label="Embedding 服务商" tip="same_as_llm 表示复用上方 LLM 的连接配置">
                    <Select
                      style={{ width: 260 }}
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
                  </ConfigRow>
                  <ConfigRow label="Base URL">
                    <Input
                      style={{ width: 560 }}
                      placeholder="Base URL"
                      value={emb.base_url || ''}
                      onChange={(e) => setEmb({ ...emb, base_url: e.target.value })}
                    />
                  </ConfigRow>
                  <ConfigRow label="Embedding 模型">
                    <Input
                      style={{ width: 320 }}
                      placeholder="Embedding Model"
                      value={emb.model || ''}
                      onChange={(e) => setEmb({ ...emb, model: e.target.value })}
                    />
                  </ConfigRow>
                  <ConfigRow label="API Key" tip="留空表示保持当前已保存密钥不变">
                    <Input.Password
                      style={{ width: 560 }}
                      placeholder={emb.api_key ? `已配置：${emb.api_key}（留空保持不变）` : 'API Key'}
                      value={emb.api_key_input || ''}
                      onChange={(e) => setEmb({ ...emb, api_key_input: e.target.value })}
                    />
                  </ConfigRow>
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
                        开启后，接入支持深度思考的模型（如 GLM-4.5 / GLM-5）时，AI 回答下方会折叠显示 LLM 真实的推理内容；关闭则不请求思考，回答更快。工具调用过程单独展示，不依赖此开关。
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
