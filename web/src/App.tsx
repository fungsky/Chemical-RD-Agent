import { HashRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useMemo } from 'react';
import Login from './pages/Login';
import AppLayout from './layouts/AppLayout';
import Assistant from './pages/Assistant';
import FormulaCenter from './pages/FormulaCenter';
import SystemSettings from './pages/SystemSettings';
import Workbench from './pages/Workbench';
import LabCenter from './pages/LabCenter';
import WikiCenter from './pages/WikiCenter';
import MaterialCenter from './pages/MaterialCenter';

function RequireAuth({ children }: { children: JSX.Element }) {
  const token = localStorage.getItem('chem_token');
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/assistant" replace />} />
          <Route path="dashboard" element={<Workbench />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="formula" element={<FormulaCenter />} />
          <Route path="lab" element={<LabCenter />} />
          <Route path="wiki" element={<WikiCenter />} />
          <Route path="materials" element={<MaterialCenter />} />
          <Route path="settings" element={<SystemSettings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </HashRouter>
  );
}
