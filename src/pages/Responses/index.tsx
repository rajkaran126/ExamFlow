// EXAMFLOW – Response Management Page
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FileText, CheckCircle2, HelpCircle, Bookmark, AlertCircle, Clock, Filter, Eye } from 'lucide-react';
import { Card, Badge, Table, Input, Select, EmptyState, DemoDataBanner, Dialog, Button } from '../../components/ui';
import type { QuestionResponse, CandidateResponses, ResponseStatus } from '../../types';
import { responseApi, candidateApi } from '../../api/client';

const DEMO_RESPONSES: QuestionResponse[] = [
  { id: 'r1', candidateId: '1', examinationId: '1', sectionId: 's1', questionNumber: 1, selectedOption: 'B', status: 'ANSWERED', timestamp: '2026-04-15T09:04:12Z', timeTaken: 68 },
  { id: 'r2', candidateId: '1', examinationId: '1', sectionId: 's1', questionNumber: 2, selectedOption: 'A', status: 'ANSWERED', timestamp: '2026-04-15T09:07:30Z', timeTaken: 112 },
  { id: 'r3', candidateId: '1', examinationId: '1', sectionId: 's1', questionNumber: 3, selectedOption: null, status: 'NOT_ATTEMPTED', timestamp: '2026-04-15T09:08:10Z', timeTaken: 25 },
  { id: 'r4', candidateId: '1', examinationId: '1', sectionId: 's1', questionNumber: 4, selectedOption: 'C', status: 'MARKED_FOR_REVIEW', timestamp: '2026-04-15T09:12:45Z', timeTaken: 140 },
  { id: 'r5', candidateId: '1', examinationId: '1', sectionId: 's1', questionNumber: 5, selectedOption: 'D', status: 'ANSWERED_AND_MARKED_FOR_REVIEW', timestamp: '2026-04-15T09:16:02Z', timeTaken: 95 },
  { id: 'r6', candidateId: '1', examinationId: '1', sectionId: 's2', questionNumber: 6, selectedOption: 'B', status: 'ANSWERED', timestamp: '2026-04-15T09:22:18Z', timeTaken: 82 },
  { id: 'r7', candidateId: '1', examinationId: '1', sectionId: 's2', questionNumber: 7, selectedOption: null, status: 'NOT_ATTEMPTED', timestamp: '2026-04-15T09:23:05Z', timeTaken: 30 },
  { id: 'r8', candidateId: '1', examinationId: '1', sectionId: 's3', questionNumber: 8, selectedOption: 'A', status: 'ANSWERED', timestamp: '2026-04-15T09:35:40Z', timeTaken: 190 },
];

const statusMeta: Record<ResponseStatus, { label: string; variant: 'success' | 'warning' | 'error' | 'info' | 'default'; icon: typeof CheckCircle2 }> = {
  ANSWERED: { label: 'Answered', variant: 'success', icon: CheckCircle2 },
  NOT_ATTEMPTED: { label: 'Not Attempted', variant: 'default', icon: HelpCircle },
  MARKED_FOR_REVIEW: { label: 'Marked for Review', variant: 'warning', icon: Bookmark },
  ANSWERED_AND_MARKED_FOR_REVIEW: { label: 'Answered & Review', variant: 'info', icon: AlertCircle },
};

export default function Responses() {
  const [searchParams] = useSearchParams();
  const initialCandidateId = searchParams.get('candidateId') || '1';
  const initialExamId = searchParams.get('examinationId') || '1';

  const [candidateId, setCandidateId] = useState(initialCandidateId);
  const [examinationId, setExaminationId] = useState(initialExamId);
  const [responses, setResponses] = useState<QuestionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedResponse, setSelectedResponse] = useState<QuestionResponse | null>(null);

  useEffect(() => {
    setLoading(true);
    responseApi.getCandidateResponses(candidateId, examinationId)
      .then((res) => {
        setResponses(res.data.responses);
        setIsDemo(false);
      })
      .catch(() => {
        setResponses(DEMO_RESPONSES);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [candidateId, examinationId]);

  const filteredResponses = responses.filter(
    (r) => !statusFilter || r.status === statusFilter
  );

  const counts = {
    total: responses.length,
    answered: responses.filter((r) => r.status === 'ANSWERED').length,
    notAttempted: responses.filter((r) => r.status === 'NOT_ATTEMPTED').length,
    review: responses.filter((r) => r.status === 'MARKED_FOR_REVIEW' || r.status === 'ANSWERED_AND_MARKED_FOR_REVIEW').length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Response Management</h1>
        <p className="text-[var(--ef-fg-muted)] mt-1">
          Candidate question response audits and timeline logs. Official evaluation marks are rendered strictly from backend calculation.
        </p>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Total Logged</p>
          <p className="text-xl font-bold text-[var(--ef-fg)] mt-1">{counts.total}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Answered</p>
          <p className="text-xl font-bold text-[var(--ef-success)] mt-1">{counts.answered}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Not Attempted</p>
          <p className="text-xl font-bold text-[var(--ef-fg-muted)] mt-1">{counts.notAttempted}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Marked for Review</p>
          <p className="text-xl font-bold text-[var(--ef-warning)] mt-1">{counts.review}</p>
        </Card>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            label="Candidate ID / Roll"
            value={candidateId}
            onChange={(e) => setCandidateId(e.target.value)}
            placeholder="Candidate identifier"
          />
        </div>
        <div className="w-full sm:w-60">
          <Select
            label="Filter Response Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            options={[
              { value: '', label: 'All Statuses' },
              { value: 'ANSWERED', label: 'Answered' },
              { value: 'NOT_ATTEMPTED', label: 'Not Attempted' },
              { value: 'MARKED_FOR_REVIEW', label: 'Marked for Review' },
              { value: 'ANSWERED_AND_MARKED_FOR_REVIEW', label: 'Answered & Review' },
            ]}
          />
        </div>
      </div>

      {/* Table */}
      <Table
        columns={[
          {
            key: 'questionNumber',
            header: 'Q. No.',
            render: (r: Record<string, unknown>) => (
              <span className="font-semibold text-[var(--ef-fg)]">Q{String(r.questionNumber)}</span>
            ),
          },
          {
            key: 'sectionId',
            header: 'Section',
            render: (r: Record<string, unknown>) => (
              <span className="text-xs font-mono uppercase bg-[var(--ef-bg-tertiary)] px-2 py-0.5 rounded">
                {String(r.sectionId)}
              </span>
            ),
          },
          {
            key: 'selectedOption',
            header: 'Option Selected',
            render: (r: Record<string, unknown>) =>
              r.selectedOption ? (
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-[var(--ef-primary)]/15 text-[var(--ef-primary)] font-bold text-xs">
                  {String(r.selectedOption)}
                </span>
              ) : (
                <span className="text-[var(--ef-fg-muted)] italic text-xs">— None —</span>
              ),
          },
          {
            key: 'status',
            header: 'Status',
            render: (r: Record<string, unknown>) => {
              const meta = statusMeta[r.status as ResponseStatus] || { label: String(r.status), variant: 'default' };
              return <Badge variant={meta.variant}>{meta.label}</Badge>;
            },
          },
          {
            key: 'timeTaken',
            header: 'Time Taken',
            render: (r: Record<string, unknown>) => (
              <span className="flex items-center gap-1 text-xs text-[var(--ef-fg-secondary)]">
                <Clock className="h-3 w-3" />
                {String(r.timeTaken)}s
              </span>
            ),
          },
          {
            key: 'timestamp',
            header: 'Timestamp',
            render: (r: Record<string, unknown>) => (
              <span className="text-xs text-[var(--ef-fg-muted)]">
                {new Date(String(r.timestamp)).toLocaleTimeString()}
              </span>
            ),
          },
          {
            key: 'actions',
            header: 'Audit',
            render: (r: Record<string, unknown>) => (
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<Eye className="h-3.5 w-3.5" />}
                onClick={() => setSelectedResponse(r as unknown as QuestionResponse)}
              >
                Inspect
              </Button>
            ),
          },
        ]}
        data={filteredResponses as unknown as Record<string, unknown>[]}
        keyField="id"
        isLoading={loading}
        emptyMessage="No response records found for this candidate"
      />

      {/* Response Audit Dialog */}
      <Dialog
        open={!!selectedResponse}
        onClose={() => setSelectedResponse(null)}
        title={selectedResponse ? `Response Details – Question ${selectedResponse.questionNumber}` : ''}
        footer={<Button onClick={() => setSelectedResponse(null)}>Close</Button>}
      >
        {selectedResponse && (
          <div className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Section</span>
              <span className="font-semibold text-[var(--ef-fg)]">{selectedResponse.sectionId}</span>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Candidate Selection</span>
              <span className="font-bold text-[var(--ef-primary)]">{selectedResponse.selectedOption ?? 'Unanswered'}</span>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Recorded Status</span>
              <Badge variant={statusMeta[selectedResponse.status]?.variant}>
                {statusMeta[selectedResponse.status]?.label}
              </Badge>
            </div>
            <div className="flex justify-between border-b border-[var(--ef-border-subtle)] pb-2">
              <span className="text-[var(--ef-fg-muted)]">Time Spent on Question</span>
              <span>{selectedResponse.timeTaken} seconds</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--ef-fg-muted)]">Submission Timestamp</span>
              <span>{new Date(selectedResponse.timestamp).toLocaleString()}</span>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
