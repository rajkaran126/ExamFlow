// EXAMFLOW – Proctoring Page
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Shield, ShieldAlert, AlertTriangle, Eye, Video, UserX, Clock, Filter } from 'lucide-react';
import { Button, Card, Badge, Table, Input, Select, DemoDataBanner, Dialog } from '../../components/ui';
import type { ProctoringEvent, ProctoringSeverity } from '../../types';
import { proctoringApi } from '../../api/client';

const DEMO_EVENTS: ProctoringEvent[] = [
  { id: 'pe-1', candidateId: '4', examinationId: '1', eventType: 'MULTIPLE_FACES_DETECTED', severity: 'CRITICAL', description: 'Second person entered candidate visual frame for 34 seconds', timestamp: '2026-04-15T09:42:10Z', penalty: 20, evidence: 'frame_capture_094210.jpg' },
  { id: 'pe-2', candidateId: '4', examinationId: '1', eventType: 'BROWSER_TAB_SWITCH', severity: 'HIGH', description: 'Window focus lost; unauthorized tab switch registered', timestamp: '2026-04-15T09:48:05Z', penalty: 10, evidence: 'tab_blur_log_094805' },
  { id: 'pe-3', candidateId: '1', examinationId: '1', eventType: 'LOOKING_AWAY', severity: 'LOW', description: 'Gaze deviation from screen exceeding 5 seconds', timestamp: '2026-04-15T10:14:22Z', penalty: 0 },
  { id: 'pe-4', candidateId: '2', examinationId: '1', eventType: 'AUDIO_ANOMALY', severity: 'MEDIUM', description: 'Secondary speech frequencies detected in audio feed', timestamp: '2026-04-15T10:30:15Z', penalty: 5 },
  { id: 'pe-5', candidateId: '4', examinationId: '1', eventType: 'DISQUALIFICATION_TRIGGER', severity: 'CRITICAL', description: 'Accumulated penalty thresholds exceeded proctoring tolerance limit', timestamp: '2026-04-15T10:55:00Z', penalty: 50 },
];

const severityMeta: Record<ProctoringSeverity, { variant: 'error' | 'warning' | 'info' | 'default'; label: string }> = {
  CRITICAL: { variant: 'error', label: 'Critical' },
  HIGH: { variant: 'error', label: 'High' },
  MEDIUM: { variant: 'warning', label: 'Medium' },
  LOW: { variant: 'info', label: 'Low' },
};

export default function Proctoring() {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get('examinationId') || '1';
  const candId = searchParams.get('candidateId') || '';

  const [events, setEvents] = useState<ProctoringEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [severityFilter, setSeverityFilter] = useState('');
  const [candidateFilter, setCandidateFilter] = useState(candId);
  const [selectedEvent, setSelectedEvent] = useState<ProctoringEvent | null>(null);

  useEffect(() => {
    setLoading(true);
    proctoringApi.listEvents(examId, { severity: severityFilter || undefined })
      .then((res) => {
        setEvents(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setEvents(DEMO_EVENTS);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [examId, severityFilter]);

  const filtered = events.filter((e) => {
    const matchCand = !candidateFilter || e.candidateId.includes(candidateFilter);
    const matchSev = !severityFilter || e.severity === severityFilter;
    return matchCand && matchSev;
  });

  const criticalCount = events.filter((e) => e.severity === 'CRITICAL' || e.severity === 'HIGH').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--ef-fg)]">AI Proctoring Audits</h1>
          <p className="text-[var(--ef-fg-muted)] mt-1">
            Real-time anomaly monitoring, audio-visual flags, penalty allocations, and disqualification logs.
          </p>
        </div>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Total Flagged Incidents</p>
          <p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{events.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">High & Critical Severity</p>
          <p className="text-2xl font-bold text-[var(--ef-error)] mt-1">{criticalCount}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Penalty Deduction Total</p>
          <p className="text-2xl font-bold text-[var(--ef-warning)] mt-1">
            {events.reduce((acc, curr) => acc + curr.penalty, 0)} pts
          </p>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Filter by Candidate ID..."
            value={candidateFilter}
            onChange={(e) => setCandidateFilter(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            options={[
              { value: '', label: 'All Severities' },
              { value: 'CRITICAL', label: 'Critical' },
              { value: 'HIGH', label: 'High' },
              { value: 'MEDIUM', label: 'Medium' },
              { value: 'LOW', label: 'Low' },
            ]}
          />
        </div>
      </div>

      {/* Table */}
      <Table
        columns={[
          {
            key: 'timestamp',
            header: 'Time',
            render: (e: Record<string, unknown>) => (
              <span className="text-xs font-mono text-[var(--ef-fg-secondary)]">
                {new Date(String(e.timestamp)).toLocaleTimeString()}
              </span>
            ),
          },
          {
            key: 'candidateId',
            header: 'Candidate ID',
            render: (e: Record<string, unknown>) => (
              <span className="font-semibold text-[var(--ef-fg)]">Candidate #{String(e.candidateId)}</span>
            ),
          },
          {
            key: 'eventType',
            header: 'Anomaly Event',
            render: (e: Record<string, unknown>) => (
              <span className="text-xs font-medium font-mono uppercase bg-[var(--ef-bg-secondary)] px-2 py-1 rounded">
                {String(e.eventType).replace(/_/g, ' ')}
              </span>
            ),
          },
          {
            key: 'severity',
            header: 'Severity',
            render: (e: Record<string, unknown>) => {
              const meta = severityMeta[e.severity as ProctoringSeverity] || { variant: 'default', label: String(e.severity) };
              return <Badge variant={meta.variant}>{meta.label}</Badge>;
            },
          },
          {
            key: 'penalty',
            header: 'Penalty Mark',
            render: (e: Record<string, unknown>) =>
              Number(e.penalty) > 0 ? (
                <span className="font-bold text-[var(--ef-error)]">−{String(e.penalty)}</span>
              ) : (
                <span className="text-xs text-[var(--ef-fg-muted)]">No penalty</span>
              ),
          },
          {
            key: 'description',
            header: 'Description',
            render: (e: Record<string, unknown>) => (
              <span className="text-xs text-[var(--ef-fg)] max-w-xs truncate block">
                {String(e.description)}
              </span>
            ),
          },
          {
            key: 'actions',
            header: 'Details',
            render: (e: Record<string, unknown>) => (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedEvent(e as unknown as ProctoringEvent)}
              >
                Inspect
              </Button>
            ),
          },
        ]}
        data={filtered as unknown as Record<string, unknown>[]}
        keyField="id"
        isLoading={loading}
        emptyMessage="No proctoring violations detected"
      />

      {/* Incident Review Dialog */}
      <Dialog
        open={!!selectedEvent}
        onClose={() => setSelectedEvent(null)}
        title="Proctoring Anomaly Details"
        footer={<Button onClick={() => setSelectedEvent(null)}>Dismiss</Button>}
      >
        {selectedEvent && (
          <div className="space-y-4 text-sm">
            <div className="p-3 bg-[var(--ef-bg-secondary)] rounded-lg">
              <span className="text-xs uppercase font-bold text-[var(--ef-fg-muted)]">Violation Code</span>
              <p className="font-mono text-base font-semibold text-[var(--ef-fg)] mt-0.5">{selectedEvent.eventType}</p>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Severity Level</span>
              <Badge variant={severityMeta[selectedEvent.severity]?.variant}>
                {selectedEvent.severity}
              </Badge>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Assigned Score Penalty</span>
              <span className="font-bold text-[var(--ef-error)]">−{selectedEvent.penalty} Marks</span>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Timestamp</span>
              <span>{new Date(selectedEvent.timestamp).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-[var(--ef-fg-muted)] block mb-1">Detailed Explanation</span>
              <p className="text-[var(--ef-fg)] bg-[var(--ef-bg-tertiary)] p-3 rounded text-xs leading-relaxed">
                {selectedEvent.description}
              </p>
            </div>
            {selectedEvent.evidence && (
              <div>
                <span className="text-[var(--ef-fg-muted)] block mb-1">Attached Evidence Log</span>
                <span className="font-mono text-xs text-[var(--ef-primary)]">{selectedEvent.evidence}</span>
              </div>
            )}
          </div>
        )}
      </Dialog>
    </div>
  );
}
