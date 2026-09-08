import { useEffect, useState } from 'react';
import { Button, Card, Col, Row, Space, Statistic, Typography } from 'antd';
import { ExperimentOutlined, DatabaseOutlined, MessageOutlined, ReadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';

export default function Workbench() {
  const [stats, setStats] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get('/health')
      .then((res) => setStats(res.data?.knowledge_graph))
      .catch(() => setStats(null));
  }, []);

  const cards = [
    { title: 'AI 研发助理', desc: '用一句话描述需求，让 AI 起草/调整/分析配方', icon: <MessageOutlined />, to: '/assistant' },
    { title: '配方中心', desc: '检索、新建、编辑配方，查看版本历史', icon: <DatabaseOutlined />, to: '/formula' },
    { title: '实验与预测', desc: 'DOE 设计、实验记录、性能预测与训练', icon: <ExperimentOutlined />, to: '/lab' },
    { title: '知识 Wiki', desc: '上传技术文档，自动编译成可检索知识页', icon: <ReadOutlined />, to: '/wiki' },
  ];

  return (
    <Space direction="vertical" size={18} style={{ width: '100%' }}>
      <Card style={{ borderRadius: 14, background: 'linear-gradient(135deg,#2563eb,#4f46e5)' }}>
        <Typography.Title level={3} style={{ color: '#fff', marginTop: 0 }}>
          ChemAgent 研发工作台
        </Typography.Title>
        <Typography.Paragraph style={{ color: 'rgba(255,255,255,0.9)', marginBottom: 4 }}>
          把需求变成配方、把实验变成洞察、把资料变成文档。
        </Typography.Paragraph>
      </Card>

      <Row gutter={16}>
        <Col span={6}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="配方" value={stats?.formulas ?? '-'} />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="材料" value={stats?.materials ?? '-'} />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="关系" value={stats?.contains_rels ?? '-'} />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ borderRadius: 12 }}>
            <Statistic title="知识图谱" value={stats?.connected ? '已连接' : '未连接'} />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        {cards.map((c) => (
          <Col span={6} key={c.to}>
            <Card hoverable style={{ borderRadius: 12, height: '100%' }} onClick={() => navigate(c.to)}>
              <Space direction="vertical" size={8}>
                <span style={{ fontSize: 28, color: '#2563eb' }}>{c.icon}</span>
                <Typography.Text strong>{c.title}</Typography.Text>
                <Typography.Text type="secondary">{c.desc}</Typography.Text>
                <Button size="small" type="link" style={{ padding: 0 }}>
                  进入 →
                </Button>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </Space>
  );
}
