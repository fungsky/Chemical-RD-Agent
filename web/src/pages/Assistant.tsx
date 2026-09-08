import { useEffect, useRef, useState } from 'react';
import {
  App,
  Button,
  Card,
  Col,
  Collapse,
  Form,
  Input,
  List,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
} from 'antd';
import { DeleteOutlined, PlusOutlined, SendOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

interface Msg {
  role: 'user' | 'assistant';
  content: string;
  thinking?: string | null;
  steps?: any[];
  tools_used?: string[];
  saved_code?: string;
}

interface Conversation {
  id: string;
  title: string;
  messages: Msg[];
  createdAt: number;
  updatedAt: number;
}

const CONVERSATIONS_KEY = 'chem_assistant_conversations';
const ACTIVE_CONVERSATION_KEY = 'chem_assistant_active_conversation';
const WELCOME_CONTENT =
  '你好，我是 ChemAgent 研发助理。告诉我你的产品需求、要调整的配方，或要分析的实验数据，我帮你推进研发。';

function makeWelcome(): Msg {
  return { role: 'assistant', content: WELCOME_CONTENT };
}

function makeConversationId(): string {
  return `c_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function createConversation(title = '新会话', messages: Msg[] = [makeWelcome()]): Conversation {
  const now = Date.now();
  return {
    id: makeConversationId(),
    title,
    messages,
    createdAt: now,
    updatedAt: now,
  };
}

function loadConversations(): { conversations: Conversation[]; activeId: string } {
  try {
    const raw = localStorage.getItem(CONVERSATIONS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length) {
        const list = parsed as Conversation[];
        const savedActive = localStorage.getItem(ACTIVE_CONVERSATION_KEY) || '';
        const activeId = list.some((c) => c.id === savedActive) ? savedActive : list[0].id;
        return { conversations: list, activeId };
      }
    }
  } catch {
    /* 忽略损坏数据 */
  }

  // 迁移旧的单会话缓存
  let history: Msg[] = [];
  try {
    const cached = sessionStorage.getItem('chem_assistant_messages');
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length) history = parsed as Msg[];
    }
  } catch {
    /* ignore */
  }
  const conv = createConversation(history.length ? '历史会话' : '新会话', history.length ? history : [makeWelcome()]);
  return { conversations: [conv], activeId: conv.id };
}

const QUICK = [
  '帮我起草一款耐 120℃ 不黄变的胶粘剂',
  'E-51 降到 22% 会有什么影响',
  '查找相似的水性丙烯酸配方',
];

const CATEGORIES = [
  '涂料',
  '胶粘剂',
  '密封剂',
  '树脂',
  '表面活性剂',
  '催化剂',
  '助剂',
  '塑料',
  '橡胶',
  '油墨',
  '其他',
];

export default function Assistant() {
  const navigate = useNavigate();
  const [thinkingEnabled, setThinkingEnabled] = useState(
    localStorage.getItem('chem_show_thinking') !== '0',
  );
  const [convState, setConvState] = useState(() => loadConversations());
  const conversations = convState.conversations;
  const activeId = convState.activeId;
  const activeConversation =
    conversations.find((c) => c.id === activeId) || conversations[0] || null;
  const messages = activeConversation ? activeConversation.messages : [];
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const [saveOpen, setSaveOpen] = useState(false);
  const [savePayload, setSavePayload] = useState<{
    convId: string;
    index: number;
    requirement: string;
    text: string;
  } | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveForm] = Form.useForm();
  const { message } = App.useApp();
  const scrollRef = useRef<HTMLDivElement>(null);

  const patchConversation = (convId: string, updater: (c: Conversation) => Conversation) => {
    setConvState((prev) => ({
      ...prev,
      conversations: prev.conversations.map((c) => (c.id === convId ? updater(c) : c)),
    }));
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    localStorage.setItem(CONVERSATIONS_KEY, JSON.stringify(conversations));
    if (activeId) {
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, activeId);
    }
  }, [conversations, activeId]);

  const newSession = () => {
    if (loading) return;
    const conv = createConversation();
    setConvState((prev) => ({
      conversations: [conv, ...prev.conversations],
      activeId: conv.id,
    }));
    setInput('');
  };

  const switchSession = (id: string) => {
    if (loading) return;
    setConvState((prev) => (prev.conversations.some((c) => c.id === id) ? { ...prev, activeId: id } : prev));
  };

  const clearCurrentSession = () => {
    if (loading || !activeConversation) return;
    patchConversation(activeConversation.id, (c) => ({
      ...c,
      title: '新会话',
      messages: [makeWelcome()],
      updatedAt: Date.now(),
    }));
    setInput('');
  };

  const deleteSession = (id: string) => {
    if (loading) return;
    setConvState((prev) => {
      const rest = prev.conversations.filter((c) => c.id !== id);
      if (!rest.length) {
        const fresh = createConversation();
        return { conversations: [fresh], activeId: fresh.id };
      }
      const nextActive = prev.activeId === id ? rest[0].id : prev.activeId;
      return { conversations: rest, activeId: nextActive };
    });
  };

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading || !activeConversation) return;
    const convId = activeConversation.id;
    const history = activeConversation.messages
      .filter(
        (m) =>
          m.content &&
          m.content !== WELCOME_CONTENT &&
          !(m.role === 'assistant' && m.content.startsWith('⚠️')),
      )
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));
    patchConversation(convId, (c) => {
      const hasUser = c.messages.some((m) => m.role === 'user');
      return {
        ...c,
        title: c.title === '新会话' && !hasUser ? content.slice(0, 24) : c.title,
        messages: [...c.messages, { role: 'user', content }],
        updatedAt: Date.now(),
      };
    });
    setInput('');
    setLoading(true);
    try {
      const res = await api.post('/chat', {
        message: content,
        history,
        use_agent: agentMode,
        show_thinking: thinkingEnabled,
      });
      patchConversation(convId, (c) => ({
        ...c,
        messages: [
          ...c.messages,
          {
            role: 'assistant',
            content: res.data.reply || '（无回复）',
            thinking: res.data.thinking || null,
            steps: res.data.steps || [],
            tools_used: res.data.tools_used || [],
          },
        ],
        updatedAt: Date.now(),
      }));
    } catch (e: any) {
      const detail = e?.response?.data?.detail || '请求失败，请确认后端已启动';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      patchConversation(convId, (c) => ({
        ...c,
        messages: [...c.messages, { role: 'assistant', content: `⚠️ ${detail}` }],
        updatedAt: Date.now(),
      }));
    } finally {
      setLoading(false);
    }
  };

  const saveAsFormula = (index: number) => {
    if (!activeConversation) return;
    const current = activeConversation.messages[index];
    if (!current) return;
    let requirement = '';
    for (let i = index - 1; i >= 0; i -= 1) {
      if (activeConversation.messages[i].role === 'user') {
        requirement = activeConversation.messages[i].content;
        break;
      }
    }
    setSavePayload({
      convId: activeConversation.id,
      index,
      requirement,
      text: current.content,
    });
    saveForm.resetFields();
    saveForm.setFieldsValue({ name: '', code: '', category: '其他' });
    setSaveOpen(true);
  };

  const confirmSaveFormula = async () => {
    if (!savePayload) return;
    const values = await saveForm.validateFields();
    setSaveLoading(true);
    try {
      const res = await api.post('/formulas/save-from-text', {
        name: values.name,
        code: values.code,
        requirement: savePayload.requirement,
        text: savePayload.text,
        category: values.category,
        target_performance: {},
      });
      patchConversation(savePayload.convId, (c) => ({
        ...c,
        messages: c.messages.map((m, i) =>
          i === savePayload.index ? { ...m, saved_code: res.data.code } : m,
        ),
        updatedAt: Date.now(),
      }));
      setSaveOpen(false);
      setSavePayload(null);
      message.success(`已保存为配方草稿：${res.data.code}`);
    } catch (e: any) {
      const d = e?.response?.data?.detail || e?.response?.data?.message;
      message.error(typeof d === 'string' ? d : '无法从回答中识别可保存配方');
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <Row gutter={16}>
      <Col flex="220px">
        <Card
          title="会话"
          size="small"
          extra={
            <Button type="text" size="small" icon={<PlusOutlined />} onClick={newSession}>
              新建
            </Button>
          }
          style={{ borderRadius: 12 }}
        >
          <List
            size="small"
            dataSource={conversations}
            style={{ maxHeight: 420, overflowY: 'auto' }}
            renderItem={(c) => {
              const isActive = c.id === activeId;
              return (
                <List.Item
                  style={{
                    padding: '4px 6px',
                    borderRadius: 6,
                    background: isActive ? '#e6f0ff' : 'transparent',
                  }}
                  actions={[
                    <Popconfirm
                      key="del"
                      title="删除会话"
                      description={`确定删除“${c.title}”及其全部消息？不可恢复。`}
                      okText="删除"
                      cancelText="取消"
                      okButtonProps={{ danger: true }}
                      onConfirm={() => deleteSession(c.id)}
                    >
                      <DeleteOutlined style={{ color: '#999' }} />
                    </Popconfirm>,
                  ]}
                >
                  <div
                    style={{ flex: 1, cursor: 'pointer', minWidth: 0 }}
                    onClick={() => switchSession(c.id)}
                  >
                    <Typography.Text
                      strong={isActive}
                      style={{ maxWidth: 130 }}
                      ellipsis={{ tooltip: c.title }}
                    >
                      {c.title}
                    </Typography.Text>
                  </div>
                </List.Item>
              );
            }}
          />
          <Popconfirm
            title="清空当前会话？"
            description="当前会话消息会被清空并开始新对话，会话条目保留。"
            okText="清空"
            cancelText="取消"
            onConfirm={clearCurrentSession}
          >
            <Button
              block
              size="small"
              style={{ marginTop: 8 }}
              disabled={loading || !messages.some((m) => m.role === 'user')}
            >
              清空当前会话
            </Button>
          </Popconfirm>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12, marginTop: 10, marginBottom: 0 }}>
            会话保存在本机浏览器，刷新或关闭后仍可继续。
          </Typography.Paragraph>
        </Card>
      </Col>
      <Col flex="auto">
        <Card
          title={
            <Space size={8}>
              <span>AI 研发助理</span>
              {activeConversation && (
                <Typography.Text type="secondary" style={{ fontSize: 13, maxWidth: 220 }} ellipsis={{ tooltip: activeConversation.title }}>
                  {activeConversation.title}
                </Typography.Text>
              )}
            </Space>
          }
          extra={
            <Space>
              <Tag color="blue">Zhipu GLM</Tag>
              <Space size={4}>
                <Switch size="small" checked={agentMode} onChange={setAgentMode} />
                <span style={{ fontSize: 12 }}>智能体模式（读取全系统）</span>
              </Space>
            </Space>
          }
          style={{ borderRadius: 12 }}
        >
          <div className="chat-scroll" ref={scrollRef}>
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              {messages.map((m, i) => (
                <div
                  key={i}
                  style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}
                >
                  <div className={`message ${m.role === 'user' ? 'message-user' : 'message-assistant'}`}>
                    {m.content}
                    {m.role === 'assistant' && i !== 0 && (
                      <div style={{ marginTop: 8 }}>
                        {thinkingEnabled && m.thinking && (
                          <Collapse
                            ghost
                            size="small"
                            style={{ marginBottom: 6, background: 'transparent' }}
                            items={[
                              {
                                key: 'thinking',
                                label: 'AI 思考过程（模型推理）',
                                children: (
                                  <Typography.Paragraph
                                    style={{ whiteSpace: 'pre-wrap', marginBottom: 0, fontSize: 13 }}
                                  >
                                    {m.thinking}
                                  </Typography.Paragraph>
                                ),
                              },
                            ]}
                          />
                        )}
                        {!!m.steps?.length && (
                          <Collapse
                            ghost
                            size="small"
                            style={{ marginBottom: 6, background: 'transparent' }}
                            items={[
                              {
                                key: 'steps',
                                label: `智能体执行过程（${m.steps.length} 步${m.tools_used?.length ? ` · 调用 ${m.tools_used.length} 个工具` : ''}）`,
                                children: (
                                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                                    {m.steps.map((step, si) => (
                                      <div key={si}>
                                        <Tag color={step.type === 'error' ? 'red' : 'blue'} style={{ marginRight: 6 }}>
                                          {step.type || 'step'}
                                        </Tag>
                                        {step.type === 'action' ? (
                                          <Typography.Text code>{step.tool_name || ''}</Typography.Text>
                                        ) : (
                                          <Typography.Text>{String(step.content || '').slice(0, 500)}</Typography.Text>
                                        )}
                                      </div>
                                    ))}
                                  </Space>
                                ),
                              },
                            ]}
                          />
                        )}
                        {thinkingEnabled && !m.thinking && !m.steps?.length && (
                          <Typography.Text type="secondary" style={{ display: 'block', fontSize: 12, marginBottom: 4 }}>
                            当前模型未返回思考内容；如需查看 LLM 推理，请在系统设置选择支持深度思考的模型（如 GLM-4.5 / GLM-5）。
                          </Typography.Text>
                        )}
                        {m.saved_code ? (
                          <Button size="small" type="link" onClick={() => navigate('/formula')}>
                            查看配方库（{m.saved_code}）→
                          </Button>
                        ) : (
                          <Button size="small" type="primary" ghost disabled={loading} onClick={() => saveAsFormula(i)}>
                            保存为配方草稿
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message message-assistant">思考中…</div>
              )}
            </Space>
          </div>
          <Space.Compact style={{ width: '100%', marginTop: 12 }}>
            <Input.TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="描述需求，例如：帮我起草一款耐120℃不黄变的胶粘剂"
              autoSize={{ minRows: 2, maxRows: 6 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={loading}
              onClick={() => send()}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </Space.Compact>
        </Card>
      </Col>
      <Col flex="230px">
        <Card title="常用场景" size="small" style={{ borderRadius: 12 }}>
          <Space direction="vertical" style={{ width: '100%' }} size={8}>
            {QUICK.map((q) => (
              <Button key={q} block onClick={() => send(q)} disabled={loading}>
                {q}
              </Button>
            ))}
          </Space>
          <Typography.Paragraph type="secondary" style={{ marginTop: 18, fontSize: 12 }}>
            常用问题快捷入口。会话按主题分开保存，可在左侧“会话”中切换或删除。
          </Typography.Paragraph>
        </Card>
      </Col>
      <Modal
        title="保存 AI 配方"
        open={saveOpen}
        onOk={confirmSaveFormula}
        confirmLoading={saveLoading}
        onCancel={() => {
          setSaveOpen(false);
          setSavePayload(null);
        }}
        okText="保存"
        cancelText="取消"
        width={520}
        destroyOnClose
      >
        <Form form={saveForm} layout="vertical">
          <Form.Item name="name" label="配方名称" rules={[{ required: true, message: '请填写配方名称' }]}>
            <Input placeholder="如：耐 120℃ 环氧胶（AI）" />
          </Form.Item>
          <Form.Item
            name="code"
            label="配方编号"
            tooltip="留空将自动生成 AI-时间戳编号"
          >
            <Input placeholder="留空自动生成" />
          </Form.Item>
          <Form.Item name="category" label="产品类别" rules={[{ required: true }]}>
            <Select options={CATEGORIES.map((c) => ({ label: c, value: c }))} />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            AI 将按当前回答解析组分与比例后保存为草稿；保存后可在配方库继续补充工艺、性能等字段。
          </Typography.Paragraph>
        </Form>
      </Modal>
    </Row>
  );
}
