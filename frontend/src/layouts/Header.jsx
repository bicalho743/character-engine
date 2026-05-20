import { useLocation, matchPath } from 'react-router-dom';
import { Bell } from 'lucide-react';

const TITLE_RULES = [
  { pattern: '/dashboard',         title: 'Dashboard' },
  { pattern: '/short-form/*',      title: 'Short-form' },
  { pattern: '/short-form',        title: 'Short-form' },
  { pattern: '/long-form/*',       title: 'Long-form' },
  { pattern: '/long-form',         title: 'Long-form' },
  { pattern: '/clip-generator',    title: 'Clip Generator' },
  { pattern: '/settings/*',        title: 'Settings' },
  { pattern: '/settings',          title: 'Settings' },
  { pattern: '/legacy/saasshorts', title: 'Legacy · SaaS Shorts' },
  { pattern: '/legacy/thumbnails', title: 'Legacy · YouTube Studio' },
  { pattern: '/legacy/ugc',        title: 'Legacy · UGC Gallery' },
  { pattern: '/legacy/ai-agent',   title: 'Legacy · AI Agent' },
];

function resolveTitle(pathname) {
  for (const rule of TITLE_RULES) {
    if (matchPath({ path: rule.pattern, end: rule.pattern.endsWith('*') ? false : true }, pathname)) {
      return rule.title;
    }
  }
  return 'OpenShorts';
}

export default function Header() {
  const location = useLocation();
  const title = resolveTitle(location.pathname);

  // Phase 2 wires real notifications; for now show the bell with no badge.
  const unread = 0;

  return (
    <header className="h-[50px] shrink-0 bg-background border-b border-border flex items-center justify-between px-6">
      <h1 className="text-[14px] font-medium text-white tracking-tight">{title}</h1>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="relative w-8 h-8 flex items-center justify-center rounded-md text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Notifications"
        >
          <Bell size={16} />
          {unread > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-primary" />
          )}
        </button>
      </div>
    </header>
  );
}
