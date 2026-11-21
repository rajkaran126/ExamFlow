// EXAMFLOW – Re-evaluation Page
import { useState, useEffect } from 'react';
import { RotateCcw, Check, X, Clock, AlertCircle, FileText, CheckCircle2 } from 'lucide-react';
import { Button, Card, Badge, Table, Input, Select, DemoDataBanner, Dialog } from '../../components/ui';
import type { ReEvaluationRequest } from '../../types';
import { reEvaluationApi } from '../../api/client';

const DEMO_REQUESTS: ReEvaluationRequest[] = [
  { id: 'req-1', candidateId: '1', examinationId: '1', reason: 'Discrepancy suspected in Section 2 (Chemistry) Question 14 answer key ambiguity', status: 'PENDING', originalMarks: 272, revisedMarks: null, requestedAt: '2026-04-17T14:20:00Z', resolvedAt: null, resolvedBy: null, remarks: null },
  { id: 'req-2', candidateId: '3', examinationId: '1', reason: 'PwD scribe time allocation was curtailed by 10 minutes at examination center', status: 'IN_PROGRESS', originalMarks: 245, revisedMarks: null, requestedAt: '2026-04-17T15:10:00Z', resolvedAt: null, resolvedBy: 'Examiner_Admin', remarks: 'Center CCTV logs requested for verification' },
  { id: 'req-3', candidateId: '9', examinationId: '1', reason: 'Challenged Question 28 Mathematics standard calculus solution', status: 'COMPLETED', originalMarks: 210, revisedMarks: 214, requestedAt: '2026-04-16T18:00:00Z', resolvedAt: '2026-04-18T09:30:00Z', resolvedBy: 'Subject_Expert_Math', remarks: 'Option C validated as acceptable alternative; +4 marks credited' },
  { id: 'req-4', candidateId: '15', examinationId: '1', reason: 'Proctoring penalty appealed; internet latency mistaken for gaze away', status: 'REJECTED', originalMarks: 180, revisedMarks: null, requestedAt: '2026-04-16T20:15:00Z', resolvedAt: '2026-04-17T11:00:00Z', resolvedBy: 'Proctor_Lead', remarks: 'Webcam telemetry verifies continuous secondary device usage' },
];

const statusMeta: Record<string, { variant: 'warning' | 'info' | 'success' | 'error'; label: string }> = {
  PENDING: { variant: 'warning', label: 'Pending Review' },
  IN_PROGRESS: { variant: 'info', label: 'In Progress' },
  COMPLETED: { variant: 'success', label: 'Completed' },
  REJECTED: { variant: 'error', label: 'Rejected' },
};

export default function ReEvaluation() {
  const [requests, setRequests] = useState<ReEvaluationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [activeDialog, setActiveDialog] = useState<{ req: ReEvaluationRequest; action: 'APPROVE' | 'REJECT' } | null>(null);
  const [remarks, setRemarks] = useState('');

  useEffect(() => {
    setLoading(true);
    reEvaluationApi.list('1', { status: statusFilter || undefined })
      .then((res) => {
        setRequests(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setRequests(DEMO_REQUESTS);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const handleAction = async () => {
    if (!activeDialog) return;
    const { req, action } = activeDialog;
    try {
      if (action === 'APPROVE') {
        await reEvaluationApi.approve(req.id, remarks);
      } else {
        await reEvaluationApi.reject(req.id, remarks);
      }
    } catch {
      // Local demo update
      setRequests((prev) =>
        prev.map((r) =>
          r.id === req.id
            ? {
                ...r,
                status: action === 'APPROVE' ? 'COMPLETED' : 'REJECTED',
                remarks: remarks || (action === 'APPROVE' ? 'Approved by moderator' : 'Rejected by moderator'),
                resolvedAt: new Date().toISOString(),
                resolvedBy: 'Admin_User',
              }
            : r
        )
      );
    } finally {
      setActiveDialog(null);
      setRemarks('');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Re-Evaluation & Grievance</h1>
        <p className="text-[var(--ef-fg-muted)] mt-1">
          Candidate question challenge requests, scoring discrepancies, and administrative review approvals.
        </p>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* Filter Bar */}
      <div className="flex gap-3">
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          options={[
            { value: '', label: 'All Review Statuses' },
            { value: 'PENDING', label: 'Pending Review' },
            { value: 'IN_PROGRESS', label: 'In Progress' },
            { value: 'COMPLETED', label: 'Completed' },
            { value: 'REJECTED', label: 'Rejected' },
          ]}
          className="w-full sm:w-60"
        />
      </div>

      {/* Table */}
      <Table
        columns={[
          {
            key: 'id',
            header: 'Grievance ID',
            render: (r: Record<string, unknown>) => (
              <span className="font-mono text-xs font-semibold">{String(r.id)}</span>
            ),
          },
          {
            key: 'candidateId',
            header: 'Candidate',
            render: (r: Record<string, unknown>) => (
              <span className="font-medium text-[var(--ef-fg)]">Cand #{String(r.candidateId)}</span>
            ),
          },
          {
            key: 'reason',
            header: 'Candidate Challenge / Reason',
            render: (r: Record<string, unknown>) => (
              <span className="text-xs text-[var(--ef-fg)] max-w-sm truncate block" title={String(r.reason)}>
                {String(r.reason)}
              </span>
            ),
          },
          {
            key: 'originalMarks',
            header: 'Original Score',
            render: (r: Record<string, unknown>) => String(r.originalMarks),
          },
          {
            key: 'revisedMarks',
            header: 'Revised Score',
            render: (r: Record<string, unknown>) =>
              r.revisedMarks !== null ? (
                <span className="font-bold text-[var(--ef-success)]">{String(r.revisedMarks)}</span>
              ) : (
                <span className="text-xs text-[var(--ef-fg-muted)]">—</span>
              ),
          },
          {
            key: 'status',
            header: 'Status',
            render: (r: Record<string, unknown>) => {
              const meta = statusMeta[String(r.status)] || { variant: 'default', label: String(r.status) };
              return <Badge variant={meta.variant}>{meta.label}</Badge>;
            },
          },
          {
            key: 'actions',
            header: 'Resolution',
            render: (r: Record<string, unknown>) => {
              const req = r as unknown as ReEvaluationRequest;
              if (req.status === 'PENDING' || req.status === 'IN_PROGRESS') {
                return (
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => setActiveDialog({ req, action: 'APPROVE' })}
                    >
                      Resolve
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => setActiveDialog({ req, action: 'REJECT' })}
                    >
                      Reject
                    </Button>
                  </div>
                );
              }
              return (
                <span className="text-xs text-[var(--ef-fg-muted)]">
                  {req.resolvedBy ? `Resolved by ${req.resolvedBy}` : 'Closed'}
                </span>
              );
            },
          },
        ]}
        data={requests as unknown as Record<string, unknown>[]}
        keyField="id"
        isLoading={loading}
        emptyMessage="No re-evaluation requests found"
      />

      {/* Resolution Confirmation Modal */}
      <Dialog
        open={!!activeDialog}
        onClose={() => setActiveDialog(null)}
        title={activeDialog?.action === 'APPROVE' ? 'Approve Re-Evaluation Grievance' : 'Reject Re-Evaluation Grievance'}
        footer={
          <>
            <Button variant="outline" onClick={() => setActiveDialog(null)}>Cancel</Button>
            <Button
              variant={activeDialog?.action === 'APPROVE' ? 'primary' : 'danger'}
              onClick={handleAction}
            >
              Confirm Resolution
            </Button>
          </>
        }
      >
        {activeDialog && (
          <div className="space-y-3 text-sm">
            <p className="text-[var(--ef-fg-secondary)]">
              <strong>Candidate Reason:</strong> {activeDialog.req.reason}
            </p>
            <Input
              label="Administrative Moderator Remarks"
              placeholder="Provide justification or marks revision details..."
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
            />
          </div>
        )}
      </Dialog>
    </div>
  );
}
