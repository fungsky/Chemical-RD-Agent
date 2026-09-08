import { useEffect, useMemo, useRef, useState } from 'react';
import { App, Button, Card, Col, Input, Row, Space, Switch, Tag, Typography } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

interface Msg {
  role: 'user' | 'assistant';
  content: string;
}

const QUICK = [
  '帮我起草一款耐 120℃ 不黄变的胶粘剂',
  'E-51 降到 22% 会有什么影响',
  '查找相似的水性丙烯酸配方',
];

export default function Assistant() {
  const navigate = useNavigate();
  const welcome: Msg = {
    role: 'assistant',
    content:
      '你好，我是 ChemAgent 研发助理。告诉我你的产品需求、要调整的配方，或要分析的实验数据，我帮你推进研发。',
  };
  const initialMessages = useMemo(() => {
    try {
      const cached = sessionStorage.getItem('chem_assistant_messages');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length) return parsed as Msg[];
      }
    } catch {
      /* ignore */
    }
    return [welcome];
  }, []);
  const [messages, setMessages] = useState<Msg[]>(initialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const [savedMap, setSavedMap] = useState<Record<number, string>>({});
  const { message } = App.useApp();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    sessionStorage.setItem('chem_assistant_messages', JSON.stringify(messages));
  }, [messages]);

  const send = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || loading) return;
    setMessages((m) => [...m, { role: 'user', content }]);
    setInput('');
    setLoading(true);
    try {
      const res = await api.post('/chat', {
        message: content,
        history: [],
        use_agent: agentMode,
      });
      setMessages((m) => [...m, { role: 'assistant', content: res.data.reply || '（无回复）' }]);
    } catch (e: any) {
      const detail = e?.response?.data?.detail || '请求失败，请确认后端已启动';
      message.error(typeof detail === 'string' ? detail : JSON.stringify(detail));
      setMessages((m) => [...m, { role: 'assistant', content: `⚠️ ${detail}` }]);
    } finally {
      setLoading(false);
    }
  };

  const saveAsFormula = async (index: number) => {
    const current = messages[index];
    let requirement = '';
    for (let i = index - 1; i >= 0; i -= 1) {
      if (messages[i].role === 'user') {
        requirement = messages[i].content;
        break;
      }
    }
    try {
      const res = await api.post('/formulas/save-from-text', {
        requirement,
        text: current.content,
        category: '其他',
        target_performance: {},
      });
      setSavedMap((m) => ({ ...m, [index]: res.data.code }));
      message.success(`已保存为配方草稿：${res.data.code}`);
    } catch (e: any) {
      const d = e?.response?.data?.detail || e?.response?.data?.message;
      message.error(typeof d === 'string' ? d : '无法从回答中识别可保存配方');
    }
  };

  return (
    <Row gutter={16}>
      <Col flex="auto">
        <Card
          title="AI 研发助理"
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
                        {savedMap[i] ? (
                          <Button size="small" type="link" onClick={() => navigate('/formula')}>
                            查看配方库（{savedMap[i]}）→
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
              autoSize={{ minRows: 1, maxRows: 4 }}
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
      <Col flex="320px">
        <Card title="常用场景" size="small" style={{ borderRadius: 12 }}>
          <Space direction="vertical" style={{ width: '100%' }} size={8}>
            {QUICK.map((q) => (
              <Button key={q} block onClick={() => send(q)} disabled={loading}>
                {q}
              </Button>
            ))}
          </Space>
          <Typography.Paragraph type="secondary" style={{ marginTop: 18, fontSize: 12 }}>
            当前为界面样板。配方、实验、知识库等功能将按模块接入现有 FastAPI 后端。
          </Typography.Paragraph>
        </Card>
      </Col>
    </Row>
  );
}
