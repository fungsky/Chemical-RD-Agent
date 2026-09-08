import { useMemo } from 'react';
import { Avatar, Dropdown, Layout, Menu, Space, Typography } from 'antd';
import {
  ExperimentOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  LogoutOutlined,
  MessageOutlined,
  ReadOutlined,
  RobotOutlined,
  ShoppingOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../api';

const { Sider, Content, Header } = Layout;

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('chem_user') || '{}');
    } catch {
      return {};
    }
  }, []);

  const selectedKey = location.pathname.startsWith('/formula')
    ? '/formula'
    : location.pathname.startsWith('/settings')
      ? '/settings'
      : location.pathname.startsWith('/assistant')
        ? '/assistant'
        : '/';

  const menuItems: any[] = [
    {
      key: 'assist',
      label: '研发助手',
      type: 'group' as const,
      children: [
        { key: '/dashboard', icon: <DashboardOutlined />, label: '研发工作台' },
        { key: '/assistant', icon: <RobotOutlined />, label: 'AI 研发助理' },
      ],
    },
    {
      key: 'formula',
      label: '配方中心',
      type: 'group' as const,
      children: [
        { key: '/formula', icon: <DatabaseOutlined />, label: '配方管理' },
      ],
    },
    {
      key: 'lab',
      label: '实验/材料/知识',
      type: 'group' as const,
      children: [
        { key: '/lab', icon: <ExperimentOutlined />, label: '实验与预测' },
        { key: '/materials', icon: <ShoppingOutlined />, label: '原材料库' },
        { key: '/wiki', icon: <ReadOutlined />, label: '知识 Wiki' },
      ],
    },
  ];
  if (user.is_superadmin || user.permissions?.includes('user:read')) {
    menuItems.push({
      key: 'sys',
      label: '系统管理',
      type: 'group' as const,
      children: [{ key: '/settings', icon: <SettingOutlined />, label: '系统设置' }],
    });
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} style={{ background: '#fff', borderRight: '1px solid #eef1f6' }}>
        <div style={{ padding: 18 }}>
          <Space>
            <span style={{ fontSize: 22 }}>🧪</span>
            <div>
              <Typography.Text strong style={{ fontSize: 15 }}>
                ChemAgent
              </Typography.Text>
              <br />
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                AI 研发助理
              </Typography.Text>
            </div>
          </Space>
        </div>
        <Menu
          mode="inline"
          items={menuItems}
          selectedKeys={[selectedKey]}
          onClick={({ key }) => {
            if (key !== '/') navigate(key);
          }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            borderBottom: '1px solid #eef1f6',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingInline: 24,
          }}
        >
          <Space>
            <MessageOutlined style={{ color: '#2563eb' }} />
            <Typography.Text strong>研发工作台</Typography.Text>
          </Space>
          <Dropdown
            menu={{
              items: [{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录' }],
              onClick: async ({ key }) => {
                if (key === 'logout') {
                  await logout();
                  navigate('/login', { replace: true });
                }
              },
            }}
          >
            <Space style={{ cursor: 'pointer' }}>
              <Avatar size="small" style={{ background: '#2563eb' }}>
                {(user.username || 'A').slice(0, 1).toUpperCase()}
              </Avatar>
              <span>{user.full_name || user.username || '用户'}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ padding: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
