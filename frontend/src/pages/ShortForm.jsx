import PageStub from './PageStub.jsx';

export default function ShortForm() {
  return (
    <PageStub
      title="Short-form"
      description="Upload up to 5 videos. The wizard categorizes each clip, applies the right layout, and exports to TikTok, Reels, and Shorts."
      todo={[
        'Phase 3: 4-step wizard (Upload → Categorize → Processing → Review)',
        'Phase 3: per-clip progress + Snake mini-game during processing',
        'Phase 3: phone-shaped preview + Before/After toggle + export bar',
        'History tab listing past batches',
      ]}
    />
  );
}
