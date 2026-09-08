import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import { App as AntApp, ConfigProvider, theme as antdTheme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import App from './App';
import './styles.css';

dayjs.locale('zh-cn');

function readTheme(): 'light' | 'dark' {
  return localStorage.getItem('chem_theme') === 'dark' ? 'dark' : 'light';
}

function readFontScale(): number {
  const v = Number(localStorage.getItem('chem_font_scale') || '1');
  return Number.isFinite(v) && v >= 0.8 && v <= 1.4 ? v : 1;
}

function ChemAgentApp() {
  const [mode, setMode] = useState<'light' | 'dark'>(readTheme);
  const [fontScale, setFontScale] = useState(readFontScale);

  useEffect(() => {
    const apply = () => {
      setMode(readTheme());
      setFontScale(readFontScale());
    };
    window.addEventListener('chem-ui-settings', apply);
    return () => window.removeEventListener('chem-ui-settings', apply);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.setProperty('--chem-font-scale', String(fontScale));
  }, [mode, fontScale]);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: mode === 'dark' ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
          colorPrimary: '#2563eb',
          borderRadius: 8,
          colorBgLayout: mode === 'dark' ? '#0f141d' : '#f6f8fb',
          fontSize: Math.round(14 * fontScale),
        },
      }}
    >
      <AntApp>
        <App />
      </AntApp>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ChemAgentApp />
  </React.StrictMode>,
);
