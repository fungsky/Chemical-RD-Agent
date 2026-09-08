import { useEffect, useMemo, useState } from 'react';
import {
  App,
  AutoComplete,
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
import { DeleteOutlined, DownloadOutlined, PlusOutlined } from '@ant-design/icons';
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
  const [formulaOptions, setFormulaOptions] = useState<any[]>([]);
  const [metricRows, setMetricRows] = useState<any[]>([
    { name: '', value: undefined, unit: '', min: undefined, max: undefined, target: undefined },
  ]);
  const [availableProps, setAvailableProps] = useState<any[]>([]);
  const [materialOptions, setMaterialOptions] = useState<any[]>([]);

  const [predItems, setPredItems] = useState<any[]>([{ name: '', function: '基础树脂', weight_percent: 100 }]);
  const [predCat, setPredCat] = useState('胶粘剂');
  const [predFormulaCode, setPredFormulaCode] = useState('');
  const [predProps, setPredProps] = useState<any[]>([]);
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
    api
      .get('/formulas', { params: { keyword: '', limit: 200 } })
      .then((res) => {
        const list = res.data || [];
        setFormulaOptions(list);
        const counts: Record<string, number> = {};
        for (const row of list) {
          for (const p of row.formula?.performance || []) {
            counts[p.test_name] = (counts[p.test_name] || 0) + 1;
          }
        }
        setAvailableProps(
          Object.entries(counts).map(([name, samples]) => ({ name, samples })),
        );
      })
      .catch(() => setFormulaOptions([]));
    api
      .get('/materials', { params: { keyword: '', limit: 200 } })
      .then((res) => setMaterialOptions(res.data || []))
      .catch(() => setMaterialOptions([]));
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
    let measurements: Record<string, number> = {};
    let specTargets: Record<string, any> = {};
    let measurement_units: Record<string, string> = {};
    for (const row of values.metric_rows || []) {
      const name = (row.name || '').trim();
      if (!name) continue;
      measurements[name] = Number(row.value ?? 0);
      if (row.unit) measurement_units[name] = row.unit;
      const spec: any = { unit: row.unit || '' };
      if (row.min !== undefined && row.min !== null && row.min !== '') spec.min = Number(row.min);
      if (row.max !== undefined && row.max !== null && row.max !== '') spec.max = Number(row.max);
      if (row.target !== undefined && row.target !== null && row.target !== '') spec.target = Number(row.target);
      specTargets[name] = spec;
    }
    const payload: any = {
      experiment_id: values.experiment_id,
      formula_name: values.formula_name,
      formula_code: values.formula_code,
      formula_version: values.formula_version,
      project: values.project,
      batch_number: values.batch_number,
      status: values.status,
      operator: values.operator,
      doe_method: values.doe_method,
      condition: values.condition || { items: [], process: {} },
      measurements,
      measurement_units,
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
      const props = predProps;
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
      const props = predProps;
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
    const specs = row.spec_targets || {};
    const metricRows = Object.keys(row.measurements || {}).map((name) => ({
      name,
      value: row.measurements[name],
      unit: row.measurement_units?.[name] || specs[name]?.unit || '',
      min: specs[name]?.min,
      max: specs[name]?.max,
      target: specs[name]?.target,
    }));
    expForm.setFieldsValue({
      experiment_id: row.experiment_id,
      formula_code: row.formula_code || '',
      formula_version: row.formula_version || '',
      formula_name: row.formula_name,
      project: row.project,
      batch_number: row.batch_number,
      status: 'completed',
      operator: row.operator,
      doe_method: row.doe_method,
      metric_rows: metricRows.length
        ? metricRows
        : [{ name: '', value: undefined, unit: '', min: undefined, max: undefined, target: undefined }],
      notes: row.notes,
    });
    setExpOpen(true);
  };

  const openNewExp = () => {
    setEditingExp(null);
    expForm.resetFields();
    expForm.setFieldsValue({
      status: 'completed',
      metric_rows: [{ name: '', value: undefined, unit: '', min: undefined, max: undefined, target: undefined }],
    });
    setExpOpen(true);
  };

  return (
    <>
    <Tabs
      items={[
        {
          key: 'doe',
          label: '实验设计（DOE）',
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
                    <AutoComplete
                      placeholder="因子名，如固化温度"
                      value={f.name}
                      style={{ width: 220 }}
                      onChange={(v) => {
                        const known: Record<string, string> = {
                          固化温度: '℃', 反应温度: '℃', 温度: '℃',
                          固化时间: 'h', 搅拌时间: 'min',
                          搅拌速度: 'rpm', 压力: 'MPa',
                        };
                        updateFactors(idx, { name: v, unit: f.unit || known[v] || '' });
                      }}
                      options={[
                        ...materialOptions.map((m) => ({ label: m.name, value: m.name })),
                        ...['固化温度', '固化时间', '搅拌速度', '搅拌时间', '反应温度', '压力'].map((x) => ({
                          label: x,
                          value: x,
                        })),
                      ]}
                      filterOption={(input, option) =>
                        (option?.value || '').toLowerCase().includes(input.toLowerCase())
                      }
                    />
                    <AutoComplete
                      placeholder="单位"
                      value={f.unit}
                      style={{ width: 100 }}
                      options={['℃', 'min', 'h', 'rpm', 'MPa', '%', 'g', 'L', 'mPa·s'].map((u) => ({
                        label: u,
                        value: u,
                      }))}
                      onChange={(v) => updateFactors(idx, { unit: v })}
                      filterOption={(input, option) =>
                        (option?.value || '').toLowerCase().includes(input.toLowerCase())
                      }
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
                    <Select
                      showSearch
                      style={{ width: 220 }}
                      value={planFormula || undefined}
                      placeholder="选择配方"
                      optionFilterProp="label"
                      onChange={(v) => setPlanFormula(v)}
                      options={formulaOptions.map((r: any) => ({
                        label: `${r.formula?.code} | ${r.formula?.name}`,
                        value: r.formula?.code,
                      }))}
                    />
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
                  onClick={openNewExp}
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
                  <Select
                    value={predCat}
                    onChange={(v) => {
                      setPredCat(v);
                      setPredFormulaCode('');
                      setPredItems([{ name: '', function: '其他', weight_percent: 0 }]);
                    }}
                    style={{ width: 160 }}
                    options={CATEGORIES.map((c) => ({ label: c, value: c }))}
                  />
                  <Select
                    showSearch
                    value={predFormulaCode || undefined}
                    placeholder="选择配方（联动带出组分）"
                    style={{ minWidth: 260 }}
                    optionFilterProp="label"
                    options={formulaOptions
                      .filter((r: any) => r.formula?.category === predCat)
                      .map((r: any) => ({
                        label: `${r.formula?.code} | ${r.formula?.name}`,
                        value: r.formula?.code,
                      }))}
                    onChange={(code) => {
                      setPredFormulaCode(code);
                      const hit = formulaOptions.find((r: any) => r.formula?.code === code);
                      if (!hit) return;
                      const f = hit.formula || {};
                      setPredItems(
                        (f.items || []).map((it: any) => ({
                          name: it.material?.name || '',
                          function: it.material?.function || '其他',
                          weight_percent: it.weight_percent || 0,
                        })),
                      );
                      const perfNames = (f.performance || []).map((p: any) => p.test_name);
                      setPredProps(perfNames.filter((n: string) => availableProps.some((p) => p.name === n)));
                    }}
                  />
                  <Select
                    mode="multiple"
                    allowClear
                    style={{ minWidth: 420 }}
                    value={predProps}
                    onChange={(v) => setPredProps(v)}
                    placeholder="选择目标性能（下方为可用指标与样本数）"
                    options={availableProps.map((p) => ({
                      label: `${p.name}（${p.samples} 条）`,
                      value: p.name,
                    }))}
                  />
                </Space>
                {predItems.map((item, idx) => (
                  <Space key={idx} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                    <AutoComplete
                      placeholder="材料名称"
                      value={item.name}
                      style={{ width: 260 }}
                      options={materialOptions.map((m) => ({ label: m.name, value: m.name }))}
                      onChange={(name) => {
                        const hit = materialOptions.find((m) => m.name === name);
                        updatePredItems(idx, {
                          name,
                          function: item.function || hit?.function || '其他',
                        });
                      }}
                      filterOption={(input, option) =>
                        (option?.value || '').toLowerCase().includes(input.toLowerCase())
                      }
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
            <Form.Item name="formula_code" hidden>
              <Input />
            </Form.Item>
            <Form.Item name="formula_version" hidden>
              <Input />
            </Form.Item>
            <Form.Item name="formula_name" label="关联配方" rules={[{ required: true }]}>
              <Select
                showSearch
                style={{ width: 280 }}
                placeholder="选择配方"
                optionFilterProp="label"
                options={formulaOptions.map((r: any) => ({
                  label: `${r.formula?.code} | ${r.formula?.name}`,
                  value: r.formula?.code,
                }))}
                onChange={(code) => {
                  const hit = formulaOptions.find((r: any) => r.formula?.code === code);
                  expForm.setFieldsValue({
                    formula_code: code,
                    formula_version: hit?.formula?.version || '1.0',
                    formula_name: hit?.formula?.name || code,
                  });
                }}
              />
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
          <Typography.Title level={5}>检测结果（指标/实测值/单位/目标范围）</Typography.Title>
          <Form.List name="metric_rows">
            {(fields, { add, remove }) => (
              <>
                {fields.map((field) => (
                  <Space key={field.key} align="baseline" style={{ display: 'flex', marginBottom: 6 }}>
                    <Form.Item name={[field.name, 'name']} rules={[{ required: true, message: '指标' }]}>
                      <AutoComplete
                        placeholder="指标名（如 硬度）"
                        style={{ width: 180 }}
                        options={availableProps.map((p) => ({
                          label: `${p.name}（${p.samples} 条）`,
                          value: p.name,
                        }))}
                        filterOption={(input, option) =>
                          (option?.value || '').toLowerCase().includes(input.toLowerCase())
                        }
                      />
                    </Form.Item>
                    <Form.Item name={[field.name, 'value']}>
                      <Input type="number" placeholder="实测值" style={{ width: 100 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'unit']}>
                      <Input placeholder="单位" style={{ width: 80 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'min']}>
                      <Input type="number" placeholder="目标≥" style={{ width: 100 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'max']}>
                      <Input type="number" placeholder="目标≤" style={{ width: 100 }} />
                    </Form.Item>
                    <Form.Item name={[field.name, 'target']}>
                      <Input type="number" placeholder="目标值" style={{ width: 100 }} />
                    </Form.Item>
                    <DeleteOutlined onClick={() => remove(field.name)} />
                  </Space>
                ))}
                <Button type="dashed" block onClick={() => add({ name: '', value: undefined, unit: '', min: undefined, max: undefined })}>
                  + 添加检测指标
                </Button>
              </>
            )}
          </Form.List>
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
