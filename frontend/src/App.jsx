import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './layouts/AppShell.jsx';
import Dashboard from './pages/Dashboard.jsx';
import ShortForm from './pages/ShortForm.jsx';
import LongForm from './pages/LongForm.jsx';
import ClipGenerator from './pages/ClipGenerator.jsx';
import Settings from './pages/Settings.jsx';
import LegacySaaSShorts from './pages/Legacy/SaaSShorts.jsx';
import LegacyThumbnails from './pages/Legacy/Thumbnails.jsx';
import LegacyUGCGallery from './pages/Legacy/UGCGalleryPage.jsx';
import LegacyAIAgent from './pages/Legacy/AIAgent.jsx';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="short-form/*" element={<ShortForm />} />
        <Route path="long-form/*" element={<LongForm />} />
        <Route path="clip-generator" element={<ClipGenerator />} />
        <Route path="settings/*" element={<Settings />} />
        <Route path="legacy/saasshorts" element={<LegacySaaSShorts />} />
        <Route path="legacy/thumbnails" element={<LegacyThumbnails />} />
        <Route path="legacy/ugc" element={<LegacyUGCGallery />} />
        <Route path="legacy/ai-agent" element={<LegacyAIAgent />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}
