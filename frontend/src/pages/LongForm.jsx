import PageStub from './PageStub.jsx';

export default function LongForm() {
  return (
    <PageStub
      title="Long-form"
      description="Process a single long-form video end-to-end: color grade, subtitles, chapter detection, and segment-to-short exports."
      todo={[
        'Phase 4: 4-step wizard (Upload → Settings → Processing → Editor)',
        'Phase 4: chapter timeline scrubber + inline chapter rename',
        'Phase 4: subtitle panel + Export segment as short',
      ]}
    />
  );
}
