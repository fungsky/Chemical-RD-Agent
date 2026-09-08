import { useEffect, useState } from 'react';
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
  Tag,
  Typography,
  Upload,
} from 'antd';
import { DownloadOutlined, PlusOutlined, ReloadOutlined, UploadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';

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

export default function MaterialCenter() {
  const { message } = App.useApp();
  const [rows, setRows] = useState<any[]>([]);
  const [keyword, setKeyword] = useState('');
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [form] = Form.useForm();

  const load = async (kw = keyword) => {
    setLoading(true);
    try {
      const res = await api.get('/materials', { params: { keyword: kw, limit: 100 } });
      setRows(res.data || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '材料加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load('');
  }, []);

  const create = async (values: any) => {
    try {
      await api.post('/materials', {
        name: values.name,
        cas_number: values.cas_number,
        chemical_name: values.chemical_name,
        supplier: values.supplier,
        function: values.function,
      });
      message.success('材料已添加');
      setOpen(false);
      load('');
    } catch (e: any) {
      const d = e?.response?.data?.detail;
      message.error(typeof d === 'string' ? d : '添加失败');
    }
  };

  const viewDetail = async (name: string) => {
    try {
      const res = await api.get(`/materials/${encodeURIComponent(name)}/detail`);
      setDetail(res.data);
      setDetailOpen(true);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '详情读取失败');
    }
  };

  const exportMaterials = async () => {
    try {
      const res = await api.get('/materials', { params: { keyword: '', limit: 1000 } });
      const data = { materials: res.data || [] };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `materials_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '导出失败');
    }
  };

  const importMaterials = async (file: File) => {
    setBusy(true);
    let success = 0;
    let failed = 0;
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const list = Array.isArray(parsed) ? parsed : parsed.materials || [];
      for (const item of list) {
        try {
          await api.post('/materials', item);
          success += 1;
        } catch {
          failed += 1;
        }
      }
      message.success(`材料导入完成：成功 ${success}，失败/重复 ${failed}`);
      load('');
    } catch {
      message.error('文件解析失败，请使用 JSON 数组或 {"materials":[...]} 格式');
    } finally {
      setBusy(false);
    }
  };

  const columns: ColumnsType<any> = [
    { title: '名称', dataIndex: 'name' },
    { title: 'CAS', dataIndex: 'cas_number', width: 130 },
    { title: '化学名', dataIndex: 'chemical_name' },
    { title: '供应商', dataIndex: 'supplier', width: 120 },
    { title: '功能', dataIndex: 'function', width: 100, render: (v) => <Tag>{v}</Tag> },
    {
      title: '操作',
      width: 110,
      render: (_, row) => (
        <Button size="small" type="link" onClick={() => viewDetail(row.name)}>
          查看参数
        </Button>
      ),
    },
  ];

  return (
    <>
      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
          原材料字段包括：名称、CAS 号、化学名称、供应商、功能分类、理化性质（如密度/粘度/闪点等）。
        </Typography.Paragraph>
        <Space>
          <Input.Search
            allowClear
            placeholder="搜索名称 / CAS / 化学名"
            style={{ width: 320 }}
            onSearch={(v) => {
              setKeyword(v);
              load(v);
            }}
          />
          <Button icon={<ReloadOutlined />} onClick={() => load('')}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />} onClick={exportMaterials}>
            导出 JSON
          </Button>
          <Upload
            maxCount={1}
            showUploadList={false}
            accept=".json"
            beforeUpload={() => false}
            onChange={(info) => {
              const file = info.fileList[0]?.originFileObj as File | undefined;
              if (file) importMaterials(file);
            }}
          >
            <Button icon={<UploadOutlined />} loading={busy}>
              批量导入
            </Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新增原材料
          </Button>
        </Space>
      </Card>
      <Card style={{ borderRadius: 12 }}>
        <Table rowKey="name" loading={loading} dataSource={rows} columns={columns} pagination={{ pageSize: 20 }} />
      </Card>

      <Modal title="新增原材料" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} destroyOnClose>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
          名称是系统匹配的关键字段，请与原料库/配方中名称保持一致；CAS 如 25068-38-6。
        </Typography.Paragraph>
        <Form form={form} layout="vertical" onFinish={create}>
          <Form.Item name="name" label="材料名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Space wrap>
            <Form.Item name="cas_number" label="CAS 号">
              <Input style={{ width: 220 }} placeholder="如 25068-38-6（可留空）" />
            </Form.Item>
            <Form.Item name="function" label="功能" initialValue="其他">
              <Select style={{ width: 160 }} options={FUNCTIONS.map((f) => ({ label: f, value: f }))} />
            </Form.Item>
          </Space>
          <Form.Item name="chemical_name" label="化学名称">
            <Input placeholder="如 双酚A型环氧树脂（可留空）" />
          </Form.Item>
          <Form.Item name="supplier" label="供应商">
            <Input placeholder="可留空" />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title={`原材料参数：${detail?.name || ''}`}
        open={detailOpen}
        footer={<Button onClick={() => setDetailOpen(false)}>关闭</Button>}
        onCancel={() => setDetailOpen(false)}
        width={680}
      >
        {detail && (
          <>
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="名称">{detail.name}</Descriptions.Item>
              <Descriptions.Item label="CAS 号">{detail.cas_number || '-'}</Descriptions.Item>
              <Descriptions.Item label="化学名称">{detail.chemical_name || '-'}</Descriptions.Item>
              <Descriptions.Item label="功能">{detail.function || '-'}</Descriptions.Item>
              <Descriptions.Item label="供应商">{detail.supplier || '-'}</Descriptions.Item>
            </Descriptions>
            <Typography.Title level={5} style={{ marginTop: 16 }}>
              理化性质参数
            </Typography.Title>
            <Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>
              {detail.properties ? JSON.stringify(detail.properties, null, 2) : '暂无理化性质参数'}
            </Typography.Paragraph>
            {!!detail.related_formulas?.length && (
              <>
                <Typography.Title level={5}>使用该材料的配方</Typography.Title>
                <Typography.Paragraph>
                  {(detail.related_formulas || [])
                    .map((f: any) => `${f.name}（${f.weight_percent}%）`)
                    .join('；')}
                </Typography.Paragraph>
              </>
            )}
          </>
        )}
      </Modal>
    </>
  );
}
