// Settings — Phase 1 wraps the existing settings panels (Gemini key,
// Brand Kit, Upload-Post, ElevenLabs, fal.ai) under a single scrollable
// page so configuration keeps working through the restructure.
// Phase 2 rebuilds this with a VS Code-style left nav + per-section
// content panel.

import { useEffect, useState } from 'react';
import { Shield } from 'lucide-react';
import KeyInput from '../components/KeyInput';
import BrandKit from '../components/BrandKit';
import { fetchUploadProfiles, setKey, useKeys } from '../state/keysStore.js';

export default function Settings() {
  const keys = useKeys();
  const [profiles, setProfiles] = useState([]);
  const [connectStatus, setConnectStatus] = useState('idle'); // idle | loading | error

  useEffect(() => {
    if (keys.uploadPost && profiles.length === 0) {
      handleFetchProfiles();
    }
  }, [keys.uploadPost]);

  async function handleFetchProfiles() {
    if (!keys.uploadPost) return;
    setConnectStatus('loading');
    try {
      const data = await fetchUploadProfiles(keys.uploadPost);
      if (data.profiles?.length) {
        setProfiles(data.profiles);
        if (!keys.uploadUserId) setKey('uploadUser', data.profiles[0].username);
        setConnectStatus('idle');
      } else {
        setConnectStatus('error');
      }
    } catch {
      setConnectStatus('error');
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-[20px] font-semibold text-white">Settings</h1>
        <div className="px-3 py-1 bg-success/10 border border-success/30 rounded-full text-[10px] text-success font-medium flex items-center gap-2">
          <Shield size={12} /> Keys live only in your browser
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface p-1">
        <KeyInput onKeySet={(v) => setKey('gemini', v)} savedKey={keys.gemini} />
      </div>

      <BrandKit />

      <SettingsPanel
        title="Social Integration"
        badge="Required"
        badgeTone="amber"
        description="Required to publish your clips to TikTok, Instagram Reels, and YouTube Shorts via Upload-Post. Includes a free tier."
      >
        <div className="space-y-3">
          <label className="block text-[13px] text-zinc-400">Upload-Post API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={keys.uploadPost}
              onChange={(e) => setKey('uploadPost', e.target.value)}
              className="input-field"
              placeholder="ey..."
            />
            <button onClick={handleFetchProfiles} className="btn-primary py-2 px-4 text-sm">
              Connect
            </button>
          </div>
          {connectStatus === 'error' && (
            <p className="text-[12px] text-red-400">No profiles found. Check your key.</p>
          )}
          {profiles.length > 0 && (
            <div className="text-[12px] text-zinc-400">
              Connected as <span className="text-white font-medium">{profiles.find(p => p.username === keys.uploadUserId)?.username || profiles[0].username}</span>
              {profiles.length > 1 && (
                <select
                  value={keys.uploadUserId || profiles[0].username}
                  onChange={(e) => setKey('uploadUser', e.target.value)}
                  className="ml-3 bg-surface border border-border rounded-md px-2 py-1 text-[12px]"
                >
                  {profiles.map((p) => <option key={p.username} value={p.username}>{p.username}</option>)}
                </select>
              )}
            </div>
          )}
        </div>
      </SettingsPanel>

      <SettingsPanel
        title="Video Translation"
        badge="Optional"
        description="Translate your clips to different languages using ElevenLabs AI dubbing."
      >
        <div className="space-y-3">
          <label className="block text-[13px] text-zinc-400">ElevenLabs API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={keys.elevenLabs}
              onChange={(e) => setKey('elevenLabs', e.target.value)}
              className="input-field"
              placeholder="sk_..."
            />
          </div>
        </div>
      </SettingsPanel>

      <SettingsPanel
        title="AI Shorts (fal.ai)"
        badge="Optional"
        description="Used by the legacy SaaS UGC generator. Generates AI actors and b-roll."
      >
        <div className="space-y-3">
          <label className="block text-[13px] text-zinc-400">fal.ai API Key</label>
          <div className="flex gap-2">
            <input
              type="password"
              value={keys.fal}
              onChange={(e) => setKey('fal', e.target.value)}
              className="input-field"
              placeholder="fal_..."
            />
          </div>
        </div>
      </SettingsPanel>

      <div className="rounded-lg border border-border bg-surface p-5">
        <div className="text-[11px] uppercase tracking-wider text-zinc-500 mb-2">Phase 2</div>
        <p className="text-[13px] text-zinc-400">
          This page will be rebuilt with a VS Code-style left nav (General / Platforms / System) and per-section content. The Brand Kit will move under <span className="text-zinc-200">General</span>.
        </p>
      </div>
    </div>
  );
}

function SettingsPanel({ title, badge, badgeTone, description, children }) {
  const toneClass = badgeTone === 'amber'
    ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
    : 'bg-white/5 border-border text-zinc-500';
  return (
    <div className="rounded-xl border border-border bg-surface p-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-[15px] font-semibold text-white">{title}</h2>
        {badge && (
          <span className={`text-[10px] px-2 py-0.5 rounded uppercase tracking-wider border ${toneClass}`}>
            {badge}
          </span>
        )}
      </div>
      {description && <p className="text-[12px] text-zinc-500 mb-5 leading-relaxed">{description}</p>}
      {children}
    </div>
  );
}
