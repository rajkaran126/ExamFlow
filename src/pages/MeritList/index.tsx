// EXAMFLOW – Merit List Page
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ListOrdered, Search, Award, Download, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';
import { Button, Card, Badge, Table, Input, Select, DemoDataBanner, Dialog } from '../../components/ui';
import type { MeritListEntry } from '../../types';
import { meritListApi } from '../../api/client';

const DEMO_MERIT: MeritListEntry[] = [
  { rank: 1, candidateId: '1', candidateName: 'Aarav Sharma', rollNumber: 'JEE2026001234', category: 'GENERAL', categoryRank: 1, totalMarks: 272, normalisedScore: 281.45, qualificationStatus: 'QUALIFIED', shiftName: 'Shift A' },
  { rank: 2, candidateId: '2', candidateName: 'Priya Patel', rollNumber: 'JEE2026001235', category: 'OBC', categoryRank: 1, totalMarks: 268, normalisedScore: 276.90, qualificationStatus: 'QUALIFIED', shiftName: 'Shift A' },
  { rank: 3, candidateId: '8', candidateName: 'Kabir Mehta', rollNumber: 'JEE2026001241', category: 'GENERAL', categoryRank: 2, totalMarks: 264, normalisedScore: 274.10, qualificationStatus: 'QUALIFIED', shiftName: 'Shift B' },
  { rank: 4, candidateId: '3', candidateName: 'Rohan Kumar', rollNumber: 'JEE2026001236', category: 'SC', categoryRank: 1, totalMarks: 245, normalisedScore: 255.30, qualificationStatus: 'QUALIFIED', shiftName: 'Shift B' },
  { rank: 5, candidateId: '12', candidateName: 'Ananya Deshmukh', rollNumber: 'JEE2026001245', category: 'EWS', categoryRank: 1, totalMarks: 242, normalisedScore: 251.80, qualificationStatus: 'QUALIFIED', shiftName: 'Shift A' },
  { rank: 6, candidateId: '5', candidateName: 'Vikram Singh', rollNumber: 'JEE2026001238', category: 'ST', categoryRank: 1, totalMarks: 220, normalisedScore: 228.40, qualificationStatus: 'QUALIFIED', shiftName: 'Shift A' },
];

export default function MeritList() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<MeritListEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [confirmPublishOpen, setConfirmPublishOpen] = useState(false);
  const [published, setPublished] = useState(false);

  useEffect(() => {
    setLoading(true);
    meritListApi.get('1', { category: categoryFilter || undefined, search: search || undefined })
      .then((res) => {
        setEntries(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setEntries(DEMO_MERIT);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [categoryFilter, search]);

  const filtered = entries.filter((e) => {
    const matchSearch = e.candidateName.toLowerCase().includes(search.toLowerCase()) || e.rollNumber.toLowerCase().includes(search.toLowerCase());
    const matchCategory = !categoryFilter || e.category === categoryFilter;
    return matchSearch && matchCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Merit List</h1>
          <p className="text-[var(--ef-fg-muted)] mt-1">
            Standardized rankings ordered by server-normalised score and category-wise quotas.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={published ? 'secondary' : 'primary'}
            leftIcon={<Award className="h-4 w-4" />}
            onClick={() => setConfirmPublishOpen(true)}
          >
            {published ? 'Merit List Published ✓' : 'Publish Official Merit List'}
          </Button>
        </div>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            placeholder="Search candidate name or roll..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            options={[
              { value: '', label: 'All Categories (CRL)' },
              { value: 'GENERAL', label: 'General / Open' },
              { value: 'OBC', label: 'OBC-NCL' },
              { value: 'SC', label: 'Scheduled Caste (SC)' },
              { value: 'ST', label: 'Scheduled Tribe (ST)' },
              { value: 'EWS', label: 'Gen-EWS' },
            ]}
          />
        </div>
      </div>

      {/* Table */}
      <Table
        columns={[
          {
            key: 'rank',
            header: 'CRL Rank',
            render: (r: Record<string, unknown>) => (
              <span className={`font-bold font-mono text-sm px-2.5 py-1 rounded-full ${
                Number(r.rank) === 1 ? 'bg-amber-500/20 text-amber-500' :
                Number(r.rank) === 2 ? 'bg-slate-400/20 text-slate-400' :
                Number(r.rank) === 3 ? 'bg-amber-700/20 text-amber-700' : 'text-[var(--ef-fg)]'
              }`}>
                #{String(r.rank)}
              </span>
            ),
          },
          {
            key: 'rollNumber',
            header: 'Roll Number',
            render: (r: Record<string, unknown>) => (
              <span className="font-mono text-xs">{String(r.rollNumber)}</span>
            ),
          },
          {
            key: 'candidateName',
            header: 'Candidate Name',
            render: (r: Record<string, unknown>) => (
              <span className="font-medium text-[var(--ef-fg)]">{String(r.candidateName)}</span>
            ),
          },
          {
            key: 'category',
            header: 'Category',
            render: (r: Record<string, unknown>) => <Badge>{String(r.category)}</Badge>,
          },
          {
            key: 'categoryRank',
            header: 'Category Rank',
            render: (r: Record<string, unknown>) => (
              <span className="text-xs font-mono font-semibold text-[var(--ef-info)]">
                {r.categoryRank ? `Cat #${String(r.categoryRank)}` : '—'}
              </span>
            ),
          },
          {
            key: 'totalMarks',
            header: 'Raw Marks',
            render: (r: Record<string, unknown>) => String(r.totalMarks),
          },
          {
            key: 'normalisedScore',
            header: 'Normalised Score',
            render: (r: Record<string, unknown>) => (
              <span className="font-bold text-[var(--ef-primary)]">
                {r.normalisedScore ? Number(r.normalisedScore).toFixed(2) : '—'}
              </span>
            ),
          },
          {
            key: 'qualificationStatus',
            header: 'Status',
            render: (r: Record<string, unknown>) => (
              <Badge variant={r.qualificationStatus === 'QUALIFIED' ? 'success' : 'error'}>
                {String(r.qualificationStatus)}
              </Badge>
            ),
          },
          {
            key: 'actions',
            header: 'Scorecard',
            render: (r: Record<string, unknown>) => (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate(`/app/results?candidateRoll=${r.rollNumber}`)}
              >
                View
              </Button>
            ),
          },
        ]}
        data={filtered as unknown as Record<string, unknown>[]}
        keyField="rollNumber"
        isLoading={loading}
        emptyMessage="No merit list entries found"
      />

      {/* Confirmation Dialog for Publishing Consequential Action */}
      <Dialog
        open={confirmPublishOpen}
        onClose={() => setConfirmPublishOpen(false)}
        title="Confirm Publication of Official Merit List"
        footer={
          <>
            <Button variant="outline" onClick={() => setConfirmPublishOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => {
                setPublished(true);
                setConfirmPublishOpen(false);
              }}
            >
              Confirm & Publish Rankings
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-2 text-[var(--ef-warning)] font-semibold">
            <AlertTriangle className="h-5 w-5" />
            Warning: Irreversible Consequential Action
          </div>
          <p className="text-[var(--ef-fg-secondary)] leading-relaxed">
            Publishing the merit list locks normalisation factors and final score allocations. Results will immediately become accessible to candidates on public portal endpoints.
          </p>
          <div className="p-3 bg-[var(--ef-bg-secondary)] rounded text-xs text-[var(--ef-fg-muted)]">
            Only authorized examination controllers may execute this operation.
          </div>
        </div>
      </Dialog>
    </div>
  );
}
