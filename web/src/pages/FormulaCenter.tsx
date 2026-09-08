import { useCallback, useEffect, useState } from 'react';
import {
  App,
  AutoComplete,
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
import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';
import { Upload } from 'antd';

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

const FORMULA_STATUS_META: Record<string, { label: string; color: string }> = {
  draft: { label: '草稿', color: 'default' },
  review: { label: '审核中', color: 'orange' },
  approved: { label: '已通过', color: 'green' },
  archived: { label: '已归档', color: 'gray' },
};

interface FormulaItem {
  material?: { name?: string; function?: string };
  weight_percent?: number;
}

interface FormulaProcess {
  mixing_speed?: number;
  mixing_time?: number;
  temperature?: number;
  pressure?: number;
  curing_temperature?: number;
  curing_time?: number;
  notes?: string;
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
  process?: FormulaProcess | null;
}

export default function FormulaCenter() {
  const [keyword, setKeyword] = useState('');
  const [category, setCategory] = useState<string | undefined>();
  const [rows, setRows] = useState<any[]>([]);
  const [materialNames, setMaterialNames] = useState<string[]>([]);
  const [propertyNames, setPropertyNames] = useState<string[]>([
    '硬度', '光泽度', '附着力', '耐冲击性', '粘度', '固含',
    '干燥时间', '盐雾时间', '耐老化时间', '拉伸强度', '断裂伸长率', '外观',
  ]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<Formula | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [versions, setVersions] = useState<any[]>([]);
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<Formula | null>(null);
  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
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

  const exportFormulas = async () => {
    try {
      const res = await api.get('/formulas/export', {
        params: { format: 'json' },
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `formulas_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '导出失败');
    }
  };

  const doImport = async (file: File) => {
    setImporting(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await api.post('/formulas/import', fd);
      const s = res.data?.summary;
      message.success(`导入完成：成功 ${s?.success || 0}，跳过 ${s?.skipped || 0}，失败 ${s?.failed || 0}`);
      load();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '导入失败');
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api
      .get('/materials', { params: { keyword: '', limit: 300 } })
      .then((res) =>
        setMaterialNames((res.data || []).map((m: any) => String(m.name || '')).filter(Boolean)),
      )
      .catch(() => setMaterialNames([]));
  }, []);

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
      process: {},
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
      process: {
        mixing_speed: f.process?.mixing_speed,
        mixing_time: f.process?.mixing_time,
        temperature: f.process?.temperature,
        pressure: f.process?.pressure,
        curing_temperature: f.process?.curing_temperature,
        curing_time: f.process?.curing_time,
        notes: f.process?.notes,
      },
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
    const processRaw = values.process || {};
    const process: Record<string, number | string> = {};
    const processNumbers = [
      'mixing_speed',
      'mixing_time',
      'temperature',
      'pressure',
      'curing_temperature',
      'curing_time',
    ];
    for (const key of processNumbers) {
      const v = processRaw[key];
      if (v !== undefined && v !== null && v !== '') {
        process[key] = Number(v);
      }
    }
    if (processRaw.notes && String(processRaw.notes).trim()) {
      process.notes = String(processRaw.notes).trim();
    }
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
        process: Object.keys(process).length ? process : undefined,
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
      render: (v) => {
        const meta = FORMULA_STATUS_META[v] || { label: v, color: 'default' };
        return <Tag color={meta.color}>{meta.label}</Tag>;
      },
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
          <Button icon={<DownloadOutlined />} onClick={exportFormulas}>
            导出 JSON
          </Button>
          <Upload
            maxCount={1}
            showUploadList={false}
            accept=".json,.xlsx"
            beforeUpload={() => false}
            onChange={(info) => {
              const file = info.fileList[0]?.originFileObj as File | undefined;
              if (file) doImport(file);
            }}
          >
            <Button icon={<UploadOutlined />} loading={importing}>
              批量导入
            </Button>
          </Upload>
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
                {(() => {
                  const meta = FORMULA_STATUS_META[detail.status || ''] || {
                    label: detail.status || '',
                    color: 'default',
                  };
                  return <Tag color={meta.color}>{meta.label}</Tag>;
                })()}
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
            <Typography.Title level={5} style={{ marginTop: 20 }}>
              工艺制程
            </Typography.Title>
            {detail.process && Object.keys(detail.process).length ? (
              <Descriptions column={2} bordered size="small">
                {detail.process.temperature !== undefined && detail.process.temperature !== null && (
                  <Descriptions.Item label="反应温度">
                    {detail.process.temperature} ℃
                  </Descriptions.Item>
                )}
                {detail.process.mixing_speed !== undefined && detail.process.mixing_speed !== null && (
                  <Descriptions.Item label="搅拌速度">
                    {detail.process.mixing_speed} rpm
                  </Descriptions.Item>
                )}
                {detail.process.mixing_time !== undefined && detail.process.mixing_time !== null && (
                  <Descriptions.Item label="搅拌时间">
                    {detail.process.mixing_time} min
                  </Descriptions.Item>
                )}
                {detail.process.pressure !== undefined && detail.process.pressure !== null && (
                  <Descriptions.Item label="压力">
                    {detail.process.pressure} MPa
                  </Descriptions.Item>
                )}
                {detail.process.curing_temperature !== undefined && detail.process.curing_temperature !== null && (
                  <Descriptions.Item label="固化温度">
                    {detail.process.curing_temperature} ℃
                  </Descriptions.Item>
                )}
                {detail.process.curing_time !== undefined && detail.process.curing_time !== null && (
                  <Descriptions.Item label="固化时间">
                    {detail.process.curing_time} h
                  </Descriptions.Item>
                )}
                {detail.process.notes && (
                  <Descriptions.Item label="工艺备注/步骤" span={2}>
                    <span style={{ whiteSpace: 'pre-wrap' }}>{detail.process.notes}</span>
                  </Descriptions.Item>
                )}
              </Descriptions>
            ) : (
              <Typography.Text type="secondary">未填写工艺制程</Typography.Text>
            )}
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
          <Typography.Paragraph type="secondary" style={{ marginTop: -4 }}>
            材料从原料库模糊选择；功能分类会自动可改；配比是占配方总量的质量百分比。
          </Typography.Paragraph>
          <div style={{ display: 'flex', gap: 8, color: '#888', fontSize: 12, marginBottom: 4 }}>
            <span style={{ width: 280 }}>材料名称</span>
            <span style={{ width: 150 }}>功能分类</span>
            <span style={{ width: 110 }}>配比（%）</span>
            <span>操作</span>
          </div>
          <Form.List name="items">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex' }}>
                    <Form.Item name={[field.name, 'name']} rules={[{ required: true }]}>
                      <AutoComplete
                        placeholder="材料名称（模糊搜索已有材料）"
                        style={{ width: 280 }}
                        options={materialNames.map((n) => ({ label: n, value: n }))}
                        filterOption={(input, option) =>
                          (option?.value || '').toLowerCase().includes(input.toLowerCase())
                        }
                      />
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
          <Typography.Paragraph type="secondary" style={{ marginTop: -4 }}>
            测试项可模糊选择已有指标；值填写该配方实际检测结果，单位如 H/MPa/h。
          </Typography.Paragraph>
          <div style={{ display: 'flex', gap: 8, color: '#888', fontSize: 12, marginBottom: 4 }}>
            <span style={{ width: 220 }}>测试项</span>
            <span style={{ width: 140 }}>值</span>
            <span style={{ width: 120 }}>单位</span>
            <span>操作</span>
          </div>
          <Form.List name="performance">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex' }}>
                    <Form.Item name={[field.name, 'test_name']}>
                      <AutoComplete
                        placeholder="测试项（模糊搜索）"
                        style={{ width: 220 }}
                        options={propertyNames.map((n) => ({ label: n, value: n }))}
                        filterOption={(input, option) =>
                          (option?.value || '').toLowerCase().includes(input.toLowerCase())
                        }
                      />
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

          <Typography.Title level={5} style={{ marginTop: 16 }}>
            工艺制程（可选）
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginTop: -4 }}>
            填写反应/搅拌/固化等关键参数；公开来源没有工艺时留空，不要凭经验编造。加料顺序与完整操作步骤可写在“工艺备注/步骤”。
          </Typography.Paragraph>
          <Space wrap style={{ marginBottom: 12 }}>
            <Form.Item name={['process', 'temperature']} label="反应温度">
              <Input type="number" style={{ width: 140 }} placeholder="如 70" addonAfter="℃" />
            </Form.Item>
            <Form.Item name={['process', 'mixing_speed']} label="搅拌速度">
              <Input type="number" style={{ width: 140 }} placeholder="如 600" addonAfter="rpm" />
            </Form.Item>
            <Form.Item name={['process', 'mixing_time']} label="搅拌时间">
              <Input type="number" style={{ width: 140 }} placeholder="如 30" addonAfter="min" />
            </Form.Item>
            <Form.Item name={['process', 'pressure']} label="压力">
              <Input type="number" style={{ width: 140 }} placeholder="如 0.1" addonAfter="MPa" />
            </Form.Item>
            <Form.Item name={['process', 'curing_temperature']} label="固化温度">
              <Input type="number" style={{ width: 140 }} placeholder="如 80" addonAfter="℃" />
            </Form.Item>
            <Form.Item name={['process', 'curing_time']} label="固化时间">
              <Input type="number" style={{ width: 140 }} placeholder="如 2" addonAfter="h" />
            </Form.Item>
          </Space>
          <Form.Item name={['process', 'notes']} label="工艺备注/步骤">
            <Input.TextArea
              rows={3}
              placeholder="按顺序填写：投料、加热、搅拌、pH/粘度控制、稀释、固化等。"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
