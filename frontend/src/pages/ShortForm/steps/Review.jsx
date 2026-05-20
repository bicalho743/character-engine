// Step 4: Review. Split view — clip list (left) + phone preview + export bar.
//
// Export wiring:
//   - Download: opens the generated clip URL (existing /api/status results).
//   - Publish:  pushes a notification + would call POST /api/social/post.
//               Backend doesn't queue these yet (plan TODO #9), so we
//               surface the intent locally via the bell.
//   - Schedule: same path as Publish with status='scheduled'.
//   - Send to CapCut: placeholder — backend integration TODO.

import { useEffect, useMemo, useState } from 'react';
import { Download, Eye, Scissors } from 'lucide-react';
import PhoneFrame from '../../../components/ui/PhoneFrame.jsx';
import PlatformBadge from '../../../components/ui/PlatformBadge.jsx';
import { getApiUrl } from '../../../config';
import { pushNotification } from '../../../state/notificationsStore.js';

const PLATFORMS = ['youtube', 'tiktok', 'instagram', 'snapchat', 'facebook'];

function flattenClips(jobs, files) {
  const out = [];
  for (const f of files) {
    const j = jobs[f.id];
    if (!j?.result?.clips) continue;
    j.result.clips.forEach((clip, i) => {
      out.push({
        jobId: j.jobId,
        fileId: f.id,
        sourceName: f.name,
        sourceFile: f.file instanceof File ? f.file : null,
        clipIndex: i,
        clip,
      });
    });
  }
  return out;
}

export default function Review({ wizard }) {
  const files = wizard.data.files || [];
  const jobs = wizard.data.jobs || {};
  const clips = useMemo(() => flattenClips(jobs, files), [jobs, files]);
  const [selected, setSelected] = useState(0);
  const [showOriginal, setShowOriginal] = useState(false);
  const [sourceUrl, setSourceUrl] = useState(null);

  const current = clips[Math.min(selected, clips.length - 1)] || null;
  const clipUrl = current?.clip?.video_url ? getApiUrl(current.clip.video_url) : null;

  // Build a blob URL for the original source file — only available when
  // the wizard has the in-memory File (lost after reload).
  useEffect(() => {
    if (!current?.sourceFile) { setSourceUrl(null); return; }
    const url = URL.createObjectURL(current.sourceFile);
    setSourceUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [current?.sourceFile]);

  if (clips.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-12 text-center text-zinc-500">
        <p className="text-[14px] text-white font-medium">No finished clips yet.</p>
        <p className="text-[12px] mt-1">Go back to Processing and wait, or restart the wizard.</p>
        <button onClick={wizard.reset} className="mt-4 btn-primary px-4 py-2 text-[13px]">
          Start over
        </button>
      </div>
    );
  }

  function publish(platform, scheduled) {
    if (!current) return;
    pushNotification({
      type: 'publish',
      platform,
      status: scheduled ? 'scheduled' : 'submitted',
      jobId: current.jobId,
      message: scheduled
        ? `Clip ${current.clipIndex + 1} scheduled to ${platform}`
        : `Clip ${current.clipIndex + 1} sent to ${platform}`,
    });
    // TODO(backend): plan TODO #9 — wire to /api/social/post once the
    // publish_jobs queue + status endpoint land.
  }

  const title = current?.clip?.video_title_for_youtube_short || current?.clip?.title || '';
  const description =
    current?.clip?.video_description_for_instagram ||
    current?.clip?.video_description_for_tiktok ||
    current?.clip?.description ||
    '';

  return (
    <div className="h-full flex">
      <aside className="w-[230px] shrink-0 border-r border-border bg-background overflow-y-auto custom-scrollbar p-3 space-y-1">
        <div className="text-[11px] uppercase tracking-wider text-zinc-500 px-2 mb-2">
          {clips.length} clip{clips.length === 1 ? '' : 's'}
        </div>
        {clips.map((c, i) => {
          const active = i === selected;
          const clipTitle = c.clip?.video_title_for_youtube_short || c.clip?.title;
          return (
            <button
              key={`${c.jobId}-${c.clipIndex}`}
              onClick={() => { setSelected(i); setShowOriginal(false); }}
              className={`w-full text-left rounded-lg p-2 transition-colors ${
                active ? 'bg-primary/15 border border-primary/30' : 'border border-transparent hover:bg-white/5'
              }`}
            >
              <div className={`text-[12px] font-medium truncate ${active ? 'text-white' : 'text-zinc-300'}`}>
                Clip {i + 1}
              </div>
              <div className="text-[10px] text-zinc-500 truncate mt-0.5">{c.sourceName}</div>
              {clipTitle && (
                <div className="text-[10px] text-zinc-400 truncate mt-1 italic">"{clipTitle}"</div>
              )}
            </button>
          );
        })}
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 flex flex-col items-center gap-4">
          <div className="flex items-center gap-2 text-[12px]">
            <button
              onClick={() => setShowOriginal(false)}
              className={`px-3 py-1.5 rounded-md ${!showOriginal ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              After
            </button>
            <button
              onClick={() => setShowOriginal(true)}
              disabled={!sourceUrl}
              className={`px-3 py-1.5 rounded-md disabled:opacity-30 disabled:cursor-not-allowed ${showOriginal ? 'bg-white/10 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              <Eye size={12} className="inline mr-1" /> Before
            </button>
          </div>

          <PhoneFrame size="md">
            {showOriginal && sourceUrl ? (
              <video key={`src-${selected}`} src={sourceUrl} controls className="w-full h-full object-contain" />
            ) : clipUrl ? (
              <video key={`clip-${selected}`} src={clipUrl} controls className="w-full h-full object-cover" />
            ) : (
              <div className="text-zinc-600 text-[12px] p-4 text-center">No preview available.</div>
            )}
          </PhoneFrame>

          {title && (
            <div className="text-center max-w-md">
              <div className="text-[13px] text-white font-medium">{title}</div>
              {description && (
                <p className="text-[11px] text-zinc-500 mt-1 leading-snug whitespace-pre-line">{description}</p>
              )}
            </div>
          )}
        </div>

        <div className="border-t border-border bg-surface px-4 py-3 flex flex-wrap items-center gap-3 shrink-0">
          <a
            href={clipUrl || '#'}
            download
            className={`btn-primary px-3 py-2 text-[12px] flex items-center gap-2 ${!clipUrl ? 'opacity-40 pointer-events-none' : ''}`}
          >
            <Download size={12} /> Download
          </a>
          <div className="flex items-center gap-1">
            <span className="text-[11px] text-zinc-500 mr-1">Publish:</span>
            {PLATFORMS.map((p) => (
              <button key={p} onClick={() => publish(p, false)} className="hover:opacity-80 transition-opacity" title={`Publish to ${p}`}>
                <PlatformBadge platform={p} withLabel={false} size="sm" />
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[11px] text-zinc-500 mr-1">Schedule:</span>
            {PLATFORMS.map((p) => (
              <button key={p} onClick={() => publish(p, true)} className="hover:opacity-80 transition-opacity" title={`Schedule to ${p}`}>
                <PlatformBadge platform={p} withLabel={false} size="sm" />
              </button>
            ))}
          </div>
          <button
            disabled
            title="CapCut export — coming soon"
            className="ml-auto px-3 py-2 text-[12px] flex items-center gap-2 rounded-md border border-border text-zinc-500 cursor-not-allowed"
          >
            <Scissors size={12} /> Send to CapCut
          </button>
        </div>
      </div>
    </div>
  );
}
