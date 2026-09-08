import { useEffect, useMemo, useState } from 'react';
import {
  App,
  Button,
  Card,
  Descriptions,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd';
import { DownloadOutlined, PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';

const METHODS = [
  { value: 'full_factorial', label: '全因子设计' },
  { value: '2k_factorial', label: '2k 因子设计' },
  { value: 'plackett_burman', label: 'Plackett-Burman 筛选' },
  { value: 'latin_hypercube', label: '拉丁超立方' },
  { value: 'central_composite', label: '中心复合设计 CCD' },
];

const CATEGORIES = ['涂料', '胶粘剂', '密封剂', '树脂', '塑料', '橡胶', '油墨', '其他'];

interface FactorRow {
  name: string;
  unit: string;
  low: number;
  high: number;
  center?: number;
}

export default function LabCenter() {
  const { message } = App.useApp();
  const [doeRows, setDoeRows] = useState<any[]>([]);
  const [doeMethod, setDoeMethod] = useState('full_factorial');
  const [factors, setFactors] = useState<FactorRow[]>([{ name: '', unit: '', low: 0, high: 100, center: 50 }]);
  const [doeLoading, setDoeLoading] = useState(false);

  const [expStats, setExpStats] = useState<any>(null);
  const [expRows, setExpRows] = useState<any[]>([]);
  const [expLoading, setExpLoading] = useState(false);
  const [expOpen, setExpOpen] = useState(false);
  const [editingExp, setEditingExp] = useState<any>(null);
  const [expForm] = Form.useForm();

  const [predItems, setPredItems] = useState<any[]>([{ name: '', function: '基础树脂', weight_percent: 100 }]);
  const [predCat, setPredCat] = useState('胶粘剂');
  const [predProps, setPredProps] = useState('硬度, 附着力');
  const [predRes, setPredRes] = useState<any[]>([]);
  const [trainRes, setTrainRes] = useState<any>(null);
  const [predLoading, setPredLoading] = useState(false);
  const [trainLoading, setTrainLoading] = useState(false);
  const [planProject, setPlanProject] = useState('胶粘剂项目A');
  const [planFormula, setPlanFormula] = useState('HF-001');
  const [planPrefix, setPlanPrefix] = useState('EXP-001');
  const [planning, setPlanning] = useState(false);

  const loadExperiments = async () => {
    setExpLoading(true);
    try {
      const [statsRes, queryRes] = await Promise.all([
        api.get('/experiments/stats'),
        api.post('/experiments/query', { limit: 100, include_outliers: true }),
      ]);
      setExpStats(statsRes.data);
      setExpRows(queryRes.data?.results || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '实验数据加载失败');
    } finally {
      setExpLoading(false);
    }
  };

  const exportTraining = async () => {
    try {
      const res = await api.get('/experiments/export/training-data', { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `training_data_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '导出失败');
    }
  };

  useEffect(() => {
    loadExperiments();
  }, []);

  const generateDoe = async () => {
    const valid = factors.filter((f) => f.name.trim());
    if (!valid.length) {
      message.warning('请填写至少一个因子');
      return;
    }
    setDoeLoading(true);
    try {
      const res = await api.post('/doe/generate', {
        method: doeMethod,
        factors: valid.map((f) => ({
          name: f.name,
          unit: f.unit,
          low: Number(f.low),
          high: Number(f.high),
          center: f.center === undefined || f.center === null || f.center === 0 ? null : Number(f.center),
          category: 'continuous',
        })),
        replicates: 1,
        center_points: 0,
        randomize: false,
      });
      setDoeRows(res.data?.runs || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || 'DOE 生成失败');
    } finally {
      setDoeLoading(false);
    }
  };

  const addExperiment = async (values: any) => {
    let condition = { items: [], process: {} };
    let measurements: Record<string, number> = {};
    let specTargets: Record<string, any> = {};
    try {
      if (values.condition_text) condition = JSON.parse(values.condition_text);
      if (values.measurements_text) measurements = JSON.parse(values.measurements_text);
      if (values.spec_targets_text) specTargets = JSON.parse(values.spec_targets_text);
    } catch {
      message.warning('条件/测量/目标规格 JSON 格式不正确');
      return;
    }
    const payload: any = {
      experiment_id: values.experiment_id,
      formula_name: values.formula_name,
      project: values.project,
      batch_number: values.batch_number,
      status: values.status,
      operator: values.operator,
      doe_method: values.doe_method,
      condition,
      measurements,
      spec_targets: specTargets,
      notes: values.notes,
    };
    try {
      if (editingExp) {
        await api.patch(`/experiments/results/${editingExp.experiment_id}`, payload);
      } else {
        await api.post('/experiments/results', payload);
      }
      const failed = Object.entries(specTargets).filter(([name, spec]: any) => {
        const v = measurements[name];
        if (v === undefined) return true;
        if (spec.min !== undefined && v < spec.min) return true;
        if (spec.max !== undefined && v > spec.max) return true;
        return false;
      });
      message.success(
        failed.length
          ? `实验已保存，但 ${failed.length} 项未达标：${failed.map(([n]) => n).join(', ')}`
          : '实验已保存，全部指标满足目标规格',
      );
      setExpOpen(false);
      setEditingExp(null);
      loadExperiments();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存失败');
    }
  };

  const planFromDoe = async () => {
    if (!doeRows.length) {
      message.warning('请先生成 DOE 方案');
      return;
    }
    setPlanning(true);
    let ok = 0;
    let skip = 0;
    for (const row of doeRows) {
      try {
        await api.post('/experiments/results', {
          experiment_id: `${planPrefix}-R${String(row.run_order).padStart(2, '0')}`,
          formula_name: planFormula,
          project: planProject,
          batch_number: planPrefix,
          status: 'planned',
          doe_method: doeMethod,
          doe_run_order: row.run_order,
          condition: { items: [], process: row.factor_levels || {} },
          measurements: {},
          spec_targets: {},
        });
        ok += 1;
      } catch {
        skip += 1;
      }
    }
    message.success(`已转实验计划 ${ok} 条${skip ? `（跳过重复 ${skip}）` : ''}`);
    loadExperiments();
    setPlanning(false);
  };

  const runPredict = async () => {
    const items = predItems
      .filter((i) => i.name && i.weight_percent)
      .map((i) => ({
        material: { name: i.name, function: i.function },
        weight_percent: Number(i.weight_percent),
      }));
    if (!items.length) {
      message.warning('请填写组分');
      return;
    }
    setPredLoading(true);
    try {
      const props = predProps.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
      const res = await api.post('/predict', { items, category: predCat, target_properties: props });
      setPredRes(res.data || []);
    } catch (e: any) {
      setPredRes([]);
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : '预测失败（请先训练模型）');
    } finally {
      setPredLoading(false);
    }
  };

  const train = async () => {
    setTrainLoading(true);
    try {
      const props = predProps.split(/[,，]/).map((s) => s.trim()).filter(Boolean);
      const res = await api.post('/predict/train', { target_properties: props });
      setTrainRes(res.data?.results || {});
      message.success('训练完成，请查看可信度');
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : '训练失败');
    } finally {
      setTrainLoading(false);
    }
  };

  const doeColumns: ColumnsType<any> = [
    { title: '运行顺序', dataIndex: 'run_order', width: 100 },
    { title: '标准顺序', dataIndex: 'standard_order', width: 100 },
    {
      title: '因子水平',
      dataIndex: 'factor_levels',
      render: (v) => (v ? JSON.stringify(v) : '-'),
    },
  ];

  const expColumns: ColumnsType<any> = [
    { title: '实验编号', dataIndex: 'experiment_id' },
    { title: '配方', dataIndex: 'formula_name' },
    { title: '项目', dataIndex: 'project' },
    { title: '状态', dataIndex: 'status', render: (v) => <Tag>{v}</Tag> },
    { title: '性能指标', dataIndex: 'measurements', render: (v) => Object.keys(v || {}).join(', ') || '-' },
    {
      title: '目标判定',
      dataIndex: 'spec_targets',
      render: (specs, row) => {
        if (!specs || !Object.keys(specs).length) return <Typography.Text type="secondary">未设目标</Typography.Text>;
        const meas = row.measurements || {};
        const failed = Object.entries(specs).filter(([name, spec]: any) => {
          const v = meas[name];
          if (v === undefined) return true;
          if (spec.min !== undefined && v < spec.min) return true;
          if (spec.max !== undefined && v > spec.max) return true;
          return false;
        });
        return failed.length ? <Tag color="red">未达标 {failed.length}</Tag> : <Tag color="green">全部达标</Tag>;
      },
    },
    { title: '实验员', dataIndex: 'operator' },
    {
      title: '操作',
      width: 130,
      render: (_, row) => (
        <Button size="small" disabled={row.status === 'completed'} onClick={() => openEditExp(row)}>
          填写结果
        </Button>
      ),
    },
  ];

  const openEditExp = (row: any) => {
    setEditingExp(row);
    expForm.setFieldsValue({
      experiment_id: row.experiment_id,
      formula_name: row.formula_name,
      project: row.project,
      batch_number: row.batch_number,
      status: 'completed',
      operator: row.operator,
      doe_method: row.doe_method,
      condition_text: row.condition ? JSON.stringify(row.condition, null, 2) : '',
      measurements_text: row.measurements && Object.keys(row.measurements).length ? JSON.stringify(row.measurements, null, 2) : '',
      spec_targets_text: row.spec_targets && Object.keys(row.spec_targets).length ? JSON.stringify(row.spec_targets, null, 2) : '',
      notes: row.notes,
    });
    setExpOpen(true);
  };

  return (
    <>
    <Tabs
      items={[
        {
          key: 'doe',
          label: 'DOE 实验设计',
          children: (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Card style={{ borderRadius: 12 }}>
                <Space wrap>
                  <Select value={doeMethod} onChange={setDoeMethod} style={{ width: 240 }} options={METHODS} />
                  <Button type="primary" loading={doeLoading} onClick={generateDoe}>
                    生成设计方案
                  </Button>
                </Space>
              </Card>
              <Card title="因子设置" style={{ borderRadius: 12 }}>
                {factors.map((f, idx) => (
                  <Space key={idx} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                    <Input
                      placeholder="因子名，如固化温度"
                      value={f.name}
                      style={{ width: 200 }}
                      onChange={(e) => updateFactors(idx, { name: e.target.value })}
                    />
                    <Input
                      placeholder="单位"
                      value={f.unit}
                      style={{ width: 90 }}
                      onChange={(e) => updateFactors(idx, { unit: e.target.value })}
                    />
                    <Input
                      type="number"
                      placeholder="低值"
                      value={f.low}
                      style={{ width: 110 }}
                      onChange={(e) => updateFactors(idx, { low: Number(e.target.value) })}
                    />
                    <Input
                      type="number"
                      placeholder="高值"
                      value={f.high}
                      style={{ width: 110 }}
                      onChange={(e) => updateFactors(idx, { high: Number(e.target.value) })}
                    />
                    <Input
                      type="number"
                      placeholder="中心点(可空)"
                      value={f.center ?? ''}
                      style={{ width: 130 }}
                      onChange={(e) => updateFactors(idx, { center: e.target.value === '' ? undefined : Number(e.target.value) })}
                    />
                    <Button
                      danger
                      disabled={factors.length <= 1}
                      onClick={() => setFactors(factors.filter((_, i) => i !== idx))}
                    >
                      删除
                    </Button>
                  </Space>
                ))}
                <Button
                  type="dashed"
                  block
                  onClick={() => setFactors([...factors, { name: '', unit: '', low: 0, high: 100 }])}
                >
                  + 添加因子
                </Button>
              </Card>
              {!!doeRows.length && (
                <Card title="设计方案" style={{ borderRadius: 12 }}>
                  <Table rowKey="run_order" dataSource={doeRows} columns={doeColumns} pagination={false} size="small" />
                  <Space style={{ marginTop: 12 }} wrap>
                    <Input style={{ width: 180 }} value={planFormula} onChange={(e) => setPlanFormula(e.target.value)} placeholder="配方名称/编号" addonBefore="配方" />
                    <Input style={{ width: 200 }} value={planProject} onChange={(e) => setPlanProject(e.target.value)} placeholder="所属项目" addonBefore="项目" />
                    <Input style={{ width: 180 }} value={planPrefix} onChange={(e) => setPlanPrefix(e.target.value)} placeholder="批次/编号前缀" addonBefore="前缀" />
                    <Button type="primary" loading={planning} onClick={planFromDoe}>
                      一键转为实验计划
                    </Button>
                  </Space>
                </Card>
              )}
            </Space>
          ),
        },
        {
          key: 'exp',
          label: '实验记录',
          children: (
            <>
              <Space style={{ marginBottom: 12 }}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setEditingExp(null);
                    expForm.resetFields();
                    setExpOpen(true);
                  }}
                >
                  录入实验
                </Button>
                <Button icon={<DownloadOutlined />} onClick={exportTraining}>
                  导出训练数据
                </Button>
                <Button onClick={loadExperiments}>刷新</Button>
              </Space>
              {expStats && Object.keys(expStats).length > 0 && (
                <Descriptions size="small" column={3} style={{ marginBottom: 12 }}>
                  <Descriptions.Item label="实验总数">{expStats.total ?? 0}</Descriptions.Item>
                </Descriptions>
              )}
              <Table rowKey="experiment_id" loading={expLoading} dataSource={expRows} columns={expColumns} />
            </>
          ),
        },
        {
          key: 'pred',
          label: '性能预测',
          children: (
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
              <Card title="输入配方与目标指标" style={{ borderRadius: 12 }}>
                <Space wrap style={{ marginBottom: 10 }}>
                  <Select value={predCat} onChange={setPredCat} style={{ width: 180 }} options={CATEGORIES.map((c) => ({ label: c, value: c }))} />
                  <Input
                    style={{ width: 300 }}
                    value={predProps}
                    onChange={(e) => setPredProps(e.target.value)}
                    placeholder="目标性能，逗号分隔，如：硬度, 附着力"
                  />
                </Space>
                {predItems.map((item, idx) => (
                  <Space key={idx} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                    <Input
                      placeholder="材料名称"
                      value={item.name}
                      style={{ width: 240 }}
                      onChange={(e) => updatePredItems(idx, { name: e.target.value })}
                    />
                    <Select
                      value={item.function}
                      style={{ width: 140 }}
                      onChange={(v) => updatePredItems(idx, { function: v })}
                      options={FUNCTIONS.map((f) => ({ label: f, value: f }))}
                    />
                    <Input
                      type="number"
                      value={item.weight_percent}
                      addonAfter="%"
                      style={{ width: 120 }}
                      onChange={(e) => updatePredItems(idx, { weight_percent: Number(e.target.value) })}
                    />
                    <Button danger disabled={predItems.length <= 1} onClick={() => setPredItems(predItems.filter((_, i) => i !== idx))}>
                      删除
                    </Button>
                  </Space>
                ))}
                <Space>
                  <Button type="dashed" onClick={() => setPredItems([...predItems, { name: '', function: '其他', weight_percent: 0 }])}>
                    + 组分
                  </Button>
                  <Button type="primary" loading={predLoading} onClick={runPredict}>
                    预测
                  </Button>
                  <Button loading={trainLoading} onClick={train}>
                    使用当前指标训练模型
                  </Button>
                </Space>
              </Card>
              {!!predRes.length && (
                <Card title="预测结果" style={{ borderRadius: 12 }}>
                  <Table
                    rowKey="property_name"
                    size="small"
                    pagination={false}
                    dataSource={predRes}
                    columns={[
                      { title: '指标', dataIndex: 'property_name' },
                      { title: '预测值', dataIndex: 'predicted_value' },
                      { title: '置信度', dataIndex: 'confidence', render: (v) => `${(v * 100).toFixed(1)}%` },
                      { title: '说明', dataIndex: 'explanation' },
                    ]}
                  />
                </Card>
              )}
              {trainRes && Object.keys(trainRes).length > 0 && (
                <Card title="训练报告（样本与可信度）" style={{ borderRadius: 12 }}>
                  <Table
                    rowKey="prop"
                    size="small"
                    pagination={false}
                    dataSource={Object.entries(trainRes).map(([prop, info]: any) => ({ prop, ...info }))}
                    columns={[
                      { title: '指标', dataIndex: 'prop' },
                      { title: '状态', dataIndex: 'status', render: (v) => <Tag color={v === 'trained' ? 'green' : 'red'}>{v}</Tag> },
                      { title: '样本数', dataIndex: 'samples' },
                      {
                        title: '数据来源',
                        dataIndex: 'data_sources',
                        render: (v) => (v ? `配方 ${v.knowledge_graph} / 实验 ${v.experiments}` : '-'),
                      },
                      { title: 'R²', dataIndex: 'r2' },
                      { title: 'CV R²', dataIndex: 'cv_r2_mean' },
                      {
                        title: '可信度',
                        dataIndex: 'reliability',
                        render: (v) =>
                          v === 'reliable' ? (
                            <Tag color="green">可靠（样本≥10）</Tag>
                          ) : (
                            <Tag color="orange">样本不足，仅供参考</Tag>
                          ),
                      },
                    ]}
                  />
                </Card>
              )}
            </Space>
          ),
        },
      ]}
      />
      <Modal
        title="录入实验结果"
        open={expOpen}
        onCancel={() => {
          setExpOpen(false);
          setEditingExp(null);
        }}
        onOk={() => expForm.submit()}
        destroyOnClose
      >
        <Form form={expForm} layout="vertical" onFinish={addExperiment}>
          <Space wrap>
            <Form.Item name="experiment_id" label="实验编号" rules={[{ required: true }]}>
              <Input style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="formula_name" label="配方名称" rules={[{ required: true }]}>
              <Input style={{ width: 220 }} />
            </Form.Item>
          </Space>
          <Space wrap>
            <Form.Item name="project" label="项目">
              <Input style={{ width: 200 }} />
            </Form.Item>
            <Form.Item name="batch_number" label="批次号">
              <Input style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="status" label="状态" initialValue="completed">
              <Select
                style={{ width: 130 }}
                options={[
                  { value: 'planned', label: 'planned' },
                  { value: 'running', label: 'running' },
                  { value: 'completed', label: 'completed' },
                  { value: 'failed', label: 'failed' },
                  { value: 'cancelled', label: 'cancelled' },
                ]}
              />
            </Form.Item>
          </Space>
          <Space wrap>
            <Form.Item name="operator" label="实验员">
              <Input style={{ width: 160 }} />
            </Form.Item>
            <Form.Item name="doe_method" label="DOE 方法">
              <Select allowClear style={{ width: 180 }} options={METHODS} />
            </Form.Item>
          </Space>
          <Form.Item
            name="condition_text"
            label="配方条件 JSON（可选）"
            tooltip='格式：{"items":[{"material_name":"环氧树脂E-51","material_function":"基础树脂","weight_percent":40}]}'
          >
            <Input.TextArea rows={3} placeholder='{"items":[...], "process":{}}' />
          </Form.Item>
          <Form.Item name="measurements_text" label="性能实测 JSON（可选）" tooltip='格式：{"硬度": 80, "附着力": 3}'>
            <Input.TextArea rows={3} placeholder='{"硬度": 80, "附着力": 3}' />
          </Form.Item>
          <Form.Item
            name="spec_targets_text"
            label="目标规格 JSON（可选，用于自动判定）"
            tooltip='格式：{"硬度": {"min": 75, "max": 85, "unit": "H"}, "附着力": {"min": 3}}'
          >
            <Input.TextArea rows={3} placeholder='{"硬度": {"min": 75, "max": 85}, "附着力": {"min": 3}}' />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );

  function updateFactors(idx: number, patch: Partial<FactorRow>) {
    setFactors((prev) => prev.map((f, i) => (i === idx ? { ...f, ...patch } : f)));
  }
  function updatePredItems(idx: number, patch: any) {
    setPredItems((prev) => prev.map((f, i) => (i === idx ? { ...f, ...patch } : f)));
  }
}

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
