import { useEffect, useState } from 'react';
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  List,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Tag,
  Timeline,
  Typography,
} from 'antd';
import {
  ExperimentOutlined,
  MessageOutlined,
  PlusOutlined,
  RocketOutlined,
  SendOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

interface Rq {
  id: string;
  customer?: string;
  title?: string;
  requirement?: string;
  status?: string;
  formula_codes?: string[];
  created_at?: string;
}

const REQUEST_STATUS_META: Record<string, { label: string; color: string }> = {
  open: { label: '待处理', color: 'orange' },
  sampling: { label: '打样中', color: 'blue' },
  review: { label: '评审中', color: 'purple' },
  done: { label: '已完成', color: 'green' },
};

export default function Workbench() {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [requests, setRequests] = useState<Rq[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [dashboard, setDashboard] = useState<any>(null);
  const [formulaOptions, setFormulaOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm] = Form.useForm();
  const [sampleForm] = Form.useForm();
  const [nextStep, setNextStep] = useState('');
  const [suggesting, setSuggesting] = useState(false);
  const [reportText, setReportText] = useState('');
  const [reportOpen, setReportOpen] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [health, setHealth] = useState<any>(null);

  const loadRequests = async () => {
    const res = await api.get('/rd/requests');
    const list = res.data?.requests || [];
    setRequests(list);
    if (!selectedId && list.length) {
      setSelectedId(list[0].id);
    }
    return list;
  };

  const loadDashboard = async (id: string) => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await api.get('/rd/dashboard', { params: { request_id: id } });
      setDashboard(res.data);
      if (sampleForm) {
        sampleForm.setFieldsValue({ request_id: id });
      }
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '工作台加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    api.get('/health').then((res) => setHealth(res.data?.knowledge_graph)).catch(() => setHealth(null));
    loadRequests();
    api
      .get('/formulas', { params: { keyword: '', limit: 200 } })
      .then((res) => setFormulaOptions(res.data || []))
      .catch(() => setFormulaOptions([]));
  }, []);

  useEffect(() => {
    if (selectedId) loadDashboard(selectedId);
  }, [selectedId]);

  const createRequest = async () => {
    const values = await createForm.validateFields();
    const res = await api.post('/rd/requests', values);
    const req = res.data?.request;
    setSelectedId(req.id);
    setCreateOpen(false);
    createForm.resetFields();
    await loadRequests();
    await loadDashboard(req.id);
    message.success(`已创建需求 ${req.id}`);
  };

  const sendSample = async () => {
    const values = await sampleForm.validateFields();
    const res = await api.post('/rd/samples', values);
    sampleForm.resetFields();
    sampleForm.setFieldsValue({ request_id: selectedId });
    message.success(`样品 ${res.data?.sample?.sample_id} 已记录`);
    loadDashboard(selectedId);
  };

  const suggest = async () => {
    setSuggesting(true);
    setNextStep('');
    try {
      const res = await api.post('/rd/next-step', { request_id: selectedId });
      setNextStep(res.data?.suggestion || '');
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '建议生成失败');
    } finally {
      setSuggesting(false);
    }
  };

  const generateReport = async () => {
    if (!selectedId) return;
    setReportLoading(true);
    try {
      const res = await api.get('/rd/report', { params: { request_id: selectedId } });
      setReportText(res.data?.report || '');
      setReportOpen(true);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '报告生成失败');
    } finally {
      setReportLoading(false);
    }
  };

  const markFeedback = async (sampleId: string, feedback: string) => {
    await api.patch(`/rd/samples/${sampleId}`, { feedback_status: 'received', feedback });
    message.success('反馈已记录');
    loadDashboard(selectedId);
  };

  const selected = requests.find((r) => r.id === selectedId) || null;
  const selectedStatus = selected
    ? REQUEST_STATUS_META[selected.status || 'open'] || { label: selected.status || '', color: 'default' }
    : null;

  return (
    <Row gutter={16}>
      <Col span={5}>
        <Card title="进行中的项目/需求" size="small" style={{ borderRadius: 12 }}>
          <List
            size="small"
            dataSource={requests}
            renderItem={(r) => {
              const meta = REQUEST_STATUS_META[r.status || 'open'] || {
                label: r.status || '',
                color: 'default',
              };
              return (
                <List.Item
                  style={{ cursor: 'pointer', padding: '6px 4px' }}
                  onClick={() => setSelectedId(r.id)}
                >
                  <Space direction="vertical" size={0}>
                    <Typography.Text strong={r.id === selectedId}>
                      {r.customer} · {r.title}
                    </Typography.Text>
                    <Space size={6}>
                      <Tag color={meta.color} style={{ margin: 0 }}>{meta.label}</Tag>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>{r.id}</Typography.Text>
                    </Space>
                  </Space>
                </List.Item>
              );
            }}
          />
          <Button type="dashed" block icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新建需求
          </Button>
        </Card>
      </Col>

      <Col span={13}>
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          {selected && (
            <Card
              title={`${selected.customer} | ${selected.title}`}
              extra={
                <Tag color={selectedStatus?.color || 'default'}>
                  {selectedStatus?.label || selected.status}
                </Tag>
              }
              style={{ borderRadius: 12 }}
            >
              <Typography.Paragraph type="secondary">{selected.requirement || '暂无需求描述'}</Typography.Paragraph>
              <Row gutter={12}>
                <Col span={8}>
                  <Statistic title="关联配方" value={dashboard?.request?.formula_codes?.length || 0} />
                </Col>
                <Col span={8}>
                  <Statistic title="打样记录" value={dashboard?.samples?.length || 0} />
                </Col>
                <Col span={8}>
                  <Statistic title="待处理" value={dashboard?.todos?.length || 0} />
                </Col>
              </Row>
            </Card>
          )}

          <Card title="待办清单" size="small" style={{ borderRadius: 12 }} loading={loading}>
            {dashboard?.todos?.length ? (
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                {dashboard.todos.map((t: any, i: number) => (
                  <Alert key={i} type={t.type === 'formula_review' ? 'warning' : 'info'} message={t.title} showIcon />
                ))}
              </Space>
            ) : (
              <Typography.Text type="secondary">暂无待办</Typography.Text>
            )}
          </Card>

          <Card title="历史时间线" size="small" style={{ borderRadius: 12 }}>
            <Timeline
              items={(dashboard?.timeline || []).slice(0, 15).map((ev: any) => ({
                color: ev.event_type === 'feedback' ? 'green' : ev.event_type === 'sample' ? 'blue' : 'gray',
                children: (
                  <Space direction="vertical" size={0}>
                    <Typography.Text>{ev.summary}</Typography.Text>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>{ev.created_at}</Typography.Text>
                  </Space>
                ),
              }))}
            />
          </Card>

          <Card title="AI 下一步建议" size="small" style={{ borderRadius: 12 }}>
            <Button icon={<RocketOutlined />} loading={suggesting} onClick={suggest} disabled={!selectedId}>
              生成下一步建议
            </Button>
            {nextStep && (
              <Typography.Paragraph style={{ marginTop: 12, whiteSpace: 'pre-wrap' }}>{nextStep}</Typography.Paragraph>
            )}
            <Button style={{ marginTop: 10 }} block loading={reportLoading} onClick={generateReport}>
              生成项目研发报告
            </Button>
          </Card>
        </Space>
      </Col>

      <Col span={6}>
        <Space direction="vertical" size={14} style={{ width: '100%' }}>
          <Card title="快捷动作" size="small" style={{ borderRadius: 12 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button block icon={<ExperimentOutlined />} onClick={() => navigate('/lab')}>
                记录一次实验
              </Button>
              <Button block icon={<MessageOutlined />} onClick={() => navigate('/assistant')}>
                与 AI 助理对话
              </Button>
              <Button block onClick={() => navigate('/formula')}>
                查看配方库
              </Button>
            </Space>
          </Card>

          <Card title="发起打样" size="small" style={{ borderRadius: 12 }}>
            <Form form={sampleForm} layout="vertical" onFinish={sendSample}>
              <Form.Item name="request_id" label="需求" rules={[{ required: true }]}>
                <Select
                  options={requests.map((r) => ({ label: `${r.customer} · ${r.title}`, value: r.id }))}
                  onChange={(v) => setSelectedId(v)}
                />
              </Form.Item>
              <Form.Item name="formula_code" label="配方编号">
                <Select
                  showSearch
                  optionFilterProp="label"
                  placeholder="搜索并选择配方"
                  onChange={(code) => {
                    const hit = formulaOptions.find((r: any) => r.formula?.code === code);
                    sampleForm.setFieldsValue({ formula_name: hit?.formula?.name || '' });
                  }}
                  options={formulaOptions.map((r: any) => ({
                    label: `${r.formula?.code} | ${r.formula?.name}`,
                    value: r.formula?.code,
                  }))}
                />
              </Form.Item>
              <Form.Item name="formula_name" label="配方名称">
                <Input />
              </Form.Item>
              <Button type="primary" htmlType="submit" block icon={<SendOutlined />}>
                记录寄样
              </Button>
            </Form>
          </Card>

          {!!dashboard?.samples?.length && (
            <Card title="最近样品反馈" size="small" style={{ borderRadius: 12 }}>
              <Space direction="vertical" size={6} style={{ width: '100%' }}>
                {dashboard.samples.slice(0, 5).map((s: any) => (
                  <Space key={s.sample_id} direction="vertical" size={2} style={{ width: '100%' }}>
                    <Typography.Text strong>{s.sample_id}</Typography.Text>
                    {s.feedback_status === 'received' ? (
                      <Typography.Paragraph style={{ margin: 0 }} type="secondary">{s.feedback}</Typography.Paragraph>
                    ) : (
                      <Button size="small" onClick={() => markFeedback(s.sample_id, window.prompt('输入客户反馈') || '已收到')}>
                        记录反馈
                      </Button>
                    )}
                  </Space>
                ))}
              </Space>
            </Card>
          )}
        </Space>
      </Col>

      <Modal title="新建客户/项目需求" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={createRequest} destroyOnClose>
        <Form form={createForm} layout="vertical">
          <Form.Item name="customer" label="客户/项目" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ marginTop: -14 }}>
            示例：某胶粘剂客户 / 内部新配方项目
          </Typography.Paragraph>
          <Form.Item name="title" label="需求标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ marginTop: -14 }}>
            一句话说明要解决什么，如：开发耐 120℃ 不黄变的环氧胶。
          </Typography.Paragraph>
          <Form.Item name="requirement" label="需求描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="项目研发报告"
        open={reportOpen}
        width={820}
        footer={<Button onClick={() => setReportOpen(false)}>关闭</Button>}
        onCancel={() => setReportOpen(false)}
      >
        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 12 }}>
          {reportText || '生成中...'}
        </Typography.Paragraph>
      </Modal>
    </Row>
  );
}
