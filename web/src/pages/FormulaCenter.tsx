import { useCallback, useEffect, useState } from 'react';
import {
  App,
  Button,
  Card,
  Descriptions,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import { DeleteOutlined, EditOutlined, EyeOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';

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

const FUNCTIONS = [
  '基础树脂',
  '溶剂',
  '填料',
  '颜料',
  '固化剂',
  '催化剂',
  '分散剂',
  '流平剂',
  '消泡剂',
  '增稠剂',
  '增塑剂',
  '抗氧化剂',
  '紫外稳定剂',
  '阻燃剂',
  '偶联剂',
  '润湿剂',
  '其他',
];

const STATUS_COLOR: Record<string, string> = {
  draft: 'default',
  review: 'orange',
  approved: 'green',
  archived: 'gray',
};

interface FormulaItem {
  material?: { name?: string; function?: string };
  weight_percent?: number;
}

interface Formula {
  code?: string;
  name?: string;
  category?: string;
  version?: string;
  status?: string;
  description?: string;
  target_application?: string;
  items?: FormulaItem[];
  performance?: Array<{ test_name?: string; value?: number; unit?: string }>;
}

export default function FormulaCenter() {
  const [keyword, setKeyword] = useState('');
  const [category, setCategory] = useState<string | undefined>();
  const [rows, setRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<Formula | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<Formula | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { keyword, limit: 100 };
      if (category) params.category = category;
      const res = await api.get('/formulas', { params });
      setRows(res.data || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '配方加载失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, category, message]);

  useEffect(() => {
    load();
  }, [load]);

  const showDetail = async (code: string) => {
    try {
      const res = await api.get(`/formulas/${encodeURIComponent(code)}`);
      setDetail(res.data);
      setDetailOpen(true);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '详情加载失败');
    }
  };

  const showVersions = async (code: string) => {
    try {
      const res = await api.get(`/formula-versions/${encodeURIComponent(code)}`);
      const data = res.data?.versions || [];
      setVersions(data);
      setDetailOpen(false);
      Modal.info({
        title: `${code} 版本历史`,
        width: 760,
        content: (
          <Table
            rowKey="id"
            size="small"
            dataSource={data}
            pagination={false}
            columns={[
              { title: '版本号', dataIndex: 'version_number', width: 90 },
              { title: '变更说明', dataIndex: 'change_summary' },
              { title: '操作人', dataIndex: 'changed_by', width: 120 },
              { title: '保存时间', dataIndex: 'created_at', width: 170 },
            ]}
          />
        ),
      });
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '版本加载失败');
    }
  };

  const openCreate = () => {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({
      name: '',
      code: '',
      category: '胶粘剂',
      items: [{ name: '', function: '基础树脂', weight_percent: 100 }],
      performance: [],
    });
    setEditOpen(true);
  };

  const openEdit = (f: Formula) => {
    setEditing(f);
    form.setFieldsValue({
      name: f.name,
      code: f.code,
      category: f.category,
      description: f.description,
      target_application: f.target_application,
      items: (f.items || []).map((i) => ({
        name: i.material?.name || '',
        function: i.material?.function || '其他',
        weight_percent: i.weight_percent,
      })),
      performance: (f.performance || []).map((p) => ({
        test_name: p.test_name,
        value: p.value,
        unit: p.unit,
      })),
    });
    setEditOpen(true);
  };

  const save = async () => {
    const values = await form.validateFields();
    const items = (values.items || [])
      .filter((i: any) => i.name && i.weight_percent)
      .map((i: any) => ({
        material: { name: i.name, function: i.function },
        weight_percent: Number(i.weight_percent),
      }));
    if (!items.length) {
      message.warning('请至少填写一行有效组分');
      return;
    }
    const performance = (values.performance || [])
      .filter((p: any) => p.test_name)
      .map((p: any) => ({
        test_name: p.test_name,
        value: Number(p.value || 0),
        unit: p.unit || '',
      }));
    setSaving(true);
    try {
      await api.post('/formulas', {
        name: values.name,
        code: values.code || values.name,
        category: values.category,
        description: values.description,
        target_application: values.target_application,
        items,
        performance,
        status: 'draft',
      });
      message.success(editing ? '修改已保存，已生成新版本' : '配方草稿已保存');
      setEditOpen(false);
      load();
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  const columns: ColumnsType<any> = [
    { title: '编号', dataIndex: ['formula', 'code'], width: 130 },
    { title: '名称', dataIndex: ['formula', 'name'] },
    { title: '类别', dataIndex: ['formula', 'category'], width: 100 },
    { title: '版本', dataIndex: ['formula', 'version'], width: 80 },
    {
      title: '状态',
      dataIndex: ['formula', 'status'],
      width: 100,
      render: (v) => <Tag color={STATUS_COLOR[v] || 'default'}>{v}</Tag>,
    },
    { title: '相似度', dataIndex: 'similarity_score', width: 90, render: (v) => (v ?? '').toFixed?.(2) ?? '-' },
    {
      title: '操作',
      width: 260,
      render: (_, row) => {
        const code = row.formula?.code;
        return (
          <Space>
            <Button size="small" icon={<EyeOutlined />} onClick={() => showDetail(code)}>
              详情
            </Button>
            <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(row.formula)}>
              编辑
            </Button>
            <Button size="small" onClick={() => showVersions(code)}>
              版本
            </Button>
          </Space>
        );
      },
    },
  ];

  const componentColumns: ColumnsType<FormulaItem> = [
    { title: '材料名称', dataIndex: ['material', 'name'] },
    { title: '功能', dataIndex: ['material', 'function'], width: 130 },
    { title: '配比(%)', dataIndex: 'weight_percent', width: 120 },
  ];

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card style={{ borderRadius: 12 }}>
        <Space wrap>
          <Input.Search
            allowClear
            placeholder="搜索配方名称 / 编号 / 材料"
            style={{ width: 320 }}
            onSearch={(v) => {
              setKeyword(v);
              load();
            }}
          />
          <Select
            allowClear
            placeholder="产品类别"
            style={{ width: 180 }}
            options={CATEGORIES.map((c) => ({ label: c, value: c }))}
            onChange={(v) => setCategory(v)}
          />
          <Button icon={<ReloadOutlined />} onClick={load}>
            刷新
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建配方
          </Button>
        </Space>
      </Card>

      <Card style={{ borderRadius: 12 }}>
        <Table
          rowKey={(r) => r.formula?.code || r.formula?.name}
          loading={loading}
          dataSource={rows}
          columns={columns}
          pagination={{ pageSize: 20, showTotal: (t) => `共 ${t} 条` }}
        />
      </Card>

      <Drawer
        title={detail?.name || '配方详情'}
        width={640}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      >
        {detail && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="编号">{detail.code}</Descriptions.Item>
              <Descriptions.Item label="版本">{detail.version}</Descriptions.Item>
              <Descriptions.Item label="类别">{detail.category}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={STATUS_COLOR[detail.status || '']}>{detail.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="目标应用" span={2}>
                {detail.target_application || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>
                {detail.description || '-'}
              </Descriptions.Item>
            </Descriptions>
            <Typography.Title level={5} style={{ marginTop: 20 }}>
              组分
            </Typography.Title>
            <Table
              rowKey={(_, i) => String(i)}
              size="small"
              columns={componentColumns}
              dataSource={detail.items || []}
              pagination={false}
            />
            {!!detail.performance?.length && (
              <>
                <Typography.Title level={5}>性能</Typography.Title>
                <Table
                  rowKey={(_, i) => String(i)}
                  size="small"
                  pagination={false}
                  dataSource={detail.performance as any}
                  columns={[
                    { title: '测试项', dataIndex: 'test_name' },
                    { title: '值', dataIndex: 'value' },
                    { title: '单位', dataIndex: 'unit' },
                  ]}
                />
              </>
            )}
            <Space style={{ marginTop: 20 }}>
              <Button type="primary" icon={<EditOutlined />} onClick={() => openEdit(detail)}>
                编辑此配方
              </Button>
              <Button onClick={() => showVersions(detail.code || '')}>版本历史</Button>
            </Space>
          </>
        )}
      </Drawer>

      <Modal
        title={editing ? `编辑配方 ${editing.code}` : '新建配方草稿'}
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={save}
        confirmLoading={saving}
        width={900}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Space wrap>
            <Form.Item name="name" label="配方名称" rules={[{ required: true }]}>
              <Input style={{ width: 280 }} />
            </Form.Item>
            <Form.Item name="code" label="配方编号">
              <Input style={{ width: 180 }} placeholder="留空用名称" disabled={!!editing} />
            </Form.Item>
            <Form.Item name="category" label="产品类别" rules={[{ required: true }]}>
              <Select
                style={{ width: 160 }}
                options={CATEGORIES.map((c) => ({ label: c, value: c }))}
              />
            </Form.Item>
          </Space>
          <Form.Item name="target_application" label="目标应用">
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>

          <Typography.Title level={5}>组分（比例需合计 95–105%）</Typography.Title>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex' }}>
                    <Form.Item name={[field.name, 'name']} rules={[{ required: true }]}>
                      <Input placeholder="材料名称" style={{ width: 260 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'function']}>
                      <Select
                        style={{ width: 150 }}
                        options={FUNCTIONS.map((f) => ({ label: f, value: f }))}
                      />
                    </Form.Item>
                    <Form.Item
                      name={[field.name, 'weight_percent']}
                      rules={[{ required: true, message: '配比' }]}
                    >
                      <Input type="number" style={{ width: 110 }} addonAfter="%" />
                    </Form.Item>
                    <DeleteOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" block onClick={() => add({ function: '基础树脂', weight_percent: 0 })}>
                  + 添加组分
                </Button>
              </>
            )}
          </Form.List>

          <Typography.Title level={5} style={{ marginTop: 16 }}>
            性能测试（可选）
          </Typography.Title>
          <Form.List name="performance">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex' }}>
                    <Form.Item name={[field.name, 'test_name']}>
                      <Input placeholder="测试项" style={{ width: 220 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'value']}>
                      <Input type="number" style={{ width: 140 }} placeholder="值" />
                    </Form.Item>
                    <Form.Item name={[field.name, 'unit']}>
                      <Input style={{ width: 120 }} placeholder="单位" />
                    </Form.Item>
                    <DeleteOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" block onClick={() => add({})}>
                  + 添加性能项
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Modal>
    </Space>
  );
}
