import { useEffect, useState } from 'react';
import {
  App,
  Button,
  Card,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Typography,
  Upload,
} from 'antd';
import { DeleteOutlined, RocketOutlined, SearchOutlined, UploadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { api } from '../api';

interface DocRow {
  doc_id: string;
  filename: string;
  source_type?: string;
  num_chunks?: number;
  upload_time?: string;
}

interface WikiPageRow {
  page_id: string;
  title: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

interface WikiHit {
  page_id: string;
  title: string;
  content?: string;
  similarity_score?: number;
}

export default function WikiCenter() {
  const { message } = App.useApp();
  const [docs, setDocs] = useState<DocRow[]>([]);
  const [pages, setPages] = useState<WikiPageRow[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [compiling, setCompiling] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<WikiHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [docOpen, setDocOpen] = useState(false);
  const [docChunks, setDocChunks] = useState<string[]>([]);
  const [pageOpen, setPageOpen] = useState(false);
  const [editingPage, setEditingPage] = useState<WikiPageRow | null>(null);
  const [pageDetail, setPageDetail] = useState<any>(null);
  const [pageSaving, setPageSaving] = useState(false);

  const loadAll = async () => {
    try {
      const [d, p] = await Promise.all([api.get('/kb/documents'), api.get('/kb/wiki/pages')]);
      setDocs(d.data || []);
      setPages(p.data?.pages || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '加载失败');
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const uploadDoc = async () => {
    if (!selected) {
      message.warning('请先选择文件');
      return;
    }
    const fd = new FormData();
    fd.append('file', selected);
    setUploading(true);
    try {
      const res = await api.post('/kb/upload', fd);
      message.success(`上传成功，已分块 ${res.data?.num_chunks || 0} 段`);
      setSelected(null);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const compile = async (doc: DocRow) => {
    setCompiling(doc.doc_id);
    try {
      const res = await api.post('/kb/wiki/compile', { doc_id: doc.doc_id });
      message.success(`Wiki 已生成：${res.data?.title || ''}`);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || 'Wiki 编译失败');
    } finally {
      setCompiling(null);
    }
  };

  const deleteDoc = async (doc: DocRow) => {
    try {
      await api.delete(`/kb/documents/${doc.doc_id}`);
      message.success('文档已删除');
      loadAll();
    } catch (e: any) {
      message.error('删除失败');
    }
  };

  const deletePage = async (page: WikiPageRow) => {
    try {
      await api.delete(`/kb/wiki/pages/${page.page_id}`);
      message.success('Wiki 页面已删除');
      loadAll();
    } catch (e: any) {
      message.error('删除失败');
    }
  };

  const viewDoc = async (doc: DocRow) => {
    try {
      const res = await api.get(`/kb/documents/${doc.doc_id}/chunks`);
      setDocChunks(res.data?.chunks || []);
      setDocOpen(true);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '原文读取失败');
    }
  };

  const openPage = async (page: WikiPageRow) => {
    try {
      const res = await api.get(`/kb/wiki/pages/${page.page_id}`);
      setPageDetail(res.data);
      setEditingPage(page);
      setPageOpen(true);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '页面读取失败');
    }
  };

  const savePage = async () => {
    if (!editingPage) return;
    setPageSaving(true);
    try {
      await api.put(`/kb/wiki/pages/${editingPage.page_id}`, {
        title: pageDetail?.title,
        content: pageDetail?.content,
        status: pageDetail?.status,
      });
      message.success('修正已保存并重新编入检索');
      setPageOpen(false);
      loadAll();
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '保存失败');
    } finally {
      setPageSaving(false);
    }
  };

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const res = await api.post('/kb/wiki/search', { query, top_k: 5 });
      setHits(res.data || []);
    } catch (e: any) {
      message.error(e?.response?.data?.detail || '检索失败');
    } finally {
      setSearching(false);
    }
  };

  const docColumns: ColumnsType<DocRow> = [
    { title: '文件名', dataIndex: 'filename' },
    { title: '来源', dataIndex: 'source_type', width: 90 },
    { title: '分块', dataIndex: 'num_chunks', width: 80 },
    { title: '上传时间', dataIndex: 'upload_time', width: 190 },
    {
      title: '操作',
      width: 220,
      render: (_, doc) => (
        <Space>
          <Button size="small" icon={<SearchOutlined />} onClick={() => viewDoc(doc)}>
            查看原文
          </Button>
          <Button size="small" type="primary" icon={<RocketOutlined />} loading={compiling === doc.doc_id} onClick={() => compile(doc)}>
            编译 Wiki
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteDoc(doc)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const pageColumns: ColumnsType<WikiPageRow> = [
    { title: '页面', dataIndex: 'title' },
    { title: '状态', dataIndex: 'status', width: 100, render: (v) => <Tag color={v === 'approved' ? 'green' : 'orange'}>{v}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', width: 190 },
    {
      title: '操作',
      width: 220,
      render: (_, p) => (
        <Space>
          <Button size="small" onClick={() => openPage(p)}>
            查看/修正
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deletePage(p)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <>
    <Tabs
      items={[
        {
          key: 'docs',
          label: '文档与编译',
          children: (
            <>
              <Card style={{ borderRadius: 12, marginBottom: 16 }}>
                <Space>
                  <Upload
                    maxCount={1}
                    beforeUpload={() => false}
                    onChange={(info) => setSelected(info.fileList[0]?.originFileObj || null)}
                    fileList={selected ? [selected as any] : []}
                    onRemove={() => setSelected(null)}
                  >
                    <Button icon={<UploadOutlined />}>选择文档（PDF/Word/TXT/Excel）</Button>
                  </Upload>
                  <Button type="primary" loading={uploading} onClick={uploadDoc}>
                    上传
                  </Button>
                </Space>
              </Card>
              <Card title="技术文档" style={{ borderRadius: 12 }}>
                <Table rowKey="doc_id" dataSource={docs} columns={docColumns} pagination={{ pageSize: 20 }} />
              </Card>
            </>
          ),
        },
        {
          key: 'pages',
          label: 'Wiki 页面',
          children: (
            <Card style={{ borderRadius: 12 }}>
              <Table rowKey="page_id" dataSource={pages} columns={pageColumns} pagination={false} />
            </Card>
          ),
        },
        {
          key: 'search',
          label: 'Wiki 检索',
          children: (
            <>
              <Space style={{ width: '100%', marginBottom: 16 }}>
                <Input.Search
                  placeholder="检索：如 环氧树脂 施工温度"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onSearch={search}
                  loading={searching}
                  enterButton={<SearchOutlined />}
                  style={{ maxWidth: 520 }}
                />
              </Space>
              {hits.map((h) => (
                <Card key={h.page_id} size="small" style={{ borderRadius: 10, marginBottom: 12 }}>
                  <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                    <Typography.Text strong>{h.title}</Typography.Text>
                    <Tag color="blue">相似度 {(h.similarity_score || 0).toFixed(3)}</Tag>
                  </Space>
                  <Typography.Paragraph
                    style={{ whiteSpace: 'pre-wrap', marginTop: 8, maxHeight: 260, overflow: 'auto' }}
                    type="secondary"
                  >
                    {h.content}
                  </Typography.Paragraph>
                </Card>
              ))}
              {!hits.length && query && (
                <Typography.Text type="secondary">暂无命中，可先上传文档并点击"编译 Wiki"。</Typography.Text>
              )}
            </>
          ),
        },
      ]}
    />
    <Modal
      title="原文分块"
      open={docOpen}
      footer={<Button onClick={() => setDocOpen(false)}>关闭</Button>}
      onCancel={() => setDocOpen(false)}
      width={760}
    >
      {docChunks.map((c, i) => (
        <Card key={i} size="small" title={`分块 ${i + 1}`} style={{ marginBottom: 8 }}>
          <Typography.Paragraph style={{ whiteSpace: 'pre-wrap' }}>{c}</Typography.Paragraph>
        </Card>
      ))}
      {!docChunks.length && <Typography.Text type="secondary">无内容</Typography.Text>}
    </Modal>
    <Modal
      title={`查看 / 修正：${editingPage?.title || ''}`}
      open={pageOpen}
      onCancel={() => setPageOpen(false)}
      onOk={savePage}
      confirmLoading={pageSaving}
      width={860}
      destroyOnClose
    >
      <Input
        value={pageDetail?.title || ''}
        onChange={(e) => setPageDetail((p: any) => ({ ...p, title: e.target.value }))}
        style={{ marginBottom: 10, fontSize: 16, fontWeight: 600 }}
      />
      <Input.TextArea
        rows={16}
        value={pageDetail?.content || ''}
        onChange={(e) => setPageDetail((p: any) => ({ ...p, content: e.target.value }))}
        style={{ fontFamily: 'monospace', fontSize: 13 }}
      />
      <Space style={{ marginTop: 10 }}>
        <span>状态：</span>
        <Select
          value={pageDetail?.status || 'draft'}
          style={{ width: 140 }}
          onChange={(v) => setPageDetail((p: any) => ({ ...p, status: v }))}
          options={[
            { value: 'draft', label: '草稿' },
            { value: 'reviewed', label: '已复核' },
          ]}
        />
      </Space>
    </Modal>
    </>
  );
}
