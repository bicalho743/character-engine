import PageStub from './PageStub.jsx';

export default function Dashboard() {
  return (
    <PageStub
      title="Dashboard"
      description="At-a-glance view of your content pipeline: clips processed, scheduled uploads, and published videos."
      todo={[
        'Phase 4: 3 stat cards (clips processed / scheduled / published)',
        'Phase 4: scheduled-uploads list with platform badges',
      ]}
    />
  );
}
