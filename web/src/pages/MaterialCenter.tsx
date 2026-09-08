import { useEffect, useState } from 'react';
import { App, Button, Card, Form, Input, Modal, Select, Space, Table, Tag } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';
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

  const columns: ColumnsType<any> = [
    { title: '名称', dataIndex: 'name' },
    { title: 'CAS', dataIndex: 'cas_number', width: 130 },
    { title: '化学名', dataIndex: 'chemical_name' },
    { title: '供应商', dataIndex: 'supplier', width: 120 },
    { title: '功能', dataIndex: 'function', width: 100, render: (v) => <Tag>{v}</Tag> },
  ];

  return (
    <>
      <Card style={{ borderRadius: 12, marginBottom: 16 }}>
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
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新增原材料
          </Button>
        </Space>
      </Card>
      <Card style={{ borderRadius: 12 }}>
        <Table rowKey="name" loading={loading} dataSource={rows} columns={columns} pagination={{ pageSize: 20 }} />
      </Card>

      <Modal title="新增原材料" open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={create}>
          <Form.Item name="name" label="材料名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Space wrap>
            <Form.Item name="cas_number" label="CAS 号">
              <Input style={{ width: 220 }} />
            </Form.Item>
            <Form.Item name="function" label="功能" initialValue="其他">
              <Select style={{ width: 160 }} options={FUNCTIONS.map((f) => ({ label: f, value: f }))} />
            </Form.Item>
          </Space>
          <Form.Item name="chemical_name" label="化学名称">
            <Input />
          </Form.Item>
          <Form.Item name="supplier" label="供应商">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
