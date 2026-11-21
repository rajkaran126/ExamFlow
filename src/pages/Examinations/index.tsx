// EXAMFLOW – Examinations List Page
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, ClipboardList } from 'lucide-react';
import { Button, Badge, Table, Input, Select, EmptyState, DemoDataBanner, Dialog } from '../../components/ui';
import type { Examination } from '../../types';
import { examinationApi } from '../../api/client';

const DEMO_EXAMS: Examination[] = [
  { id: '1', name: 'JEE Main 2026 Session 2', code: 'JEE-MAIN-2026-S2', description: 'Joint Entrance Examination', date: '2026-04-15', duration: 180, totalMarks: 300, passingMarks: 75, sections: [{ id: 's1', name: 'Physics', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25 }, { id: 's2', name: 'Chemistry', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25 }, { id: 's3', name: 'Mathematics', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25 }], shifts: [{ id: 'sh1', examinationId: '1', name: 'Shift A', date: '2026-04-15', startTime: '09:00', endTime: '12:00', totalCandidates: 12500, status: 'COMPLETED' }, { id: 'sh2', examinationId: '1', name: 'Shift B', date: '2026-04-15', startTime: '14:00', endTime: '17:00', totalCandidates: 11800, status: 'COMPLETED' }], negativeMarkingEnabled: true, sectionalCutoffsEnabled: true, normalisationEnabled: true, status: 'COMPLETED', createdAt: '2026-01-10T00:00:00Z', updatedAt: '2026-04-16T00:00:00Z' },
  { id: '2', name: 'NEET UG 2026', code: 'NEET-UG-2026', description: 'National Eligibility cum Entrance Test', date: '2026-05-05', duration: 200, totalMarks: 720, passingMarks: 180, sections: [{ id: 's4', name: 'Physics', totalQuestions: 45, maxMarks: 180, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: null }, { id: 's5', name: 'Chemistry', totalQuestions: 45, maxMarks: 180, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: null }, { id: 's6', name: 'Biology', totalQuestions: 90, maxMarks: 360, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: null }], shifts: [], negativeMarkingEnabled: true, sectionalCutoffsEnabled: false, normalisationEnabled: false, status: 'IN_PROGRESS', createdAt: '2026-02-01T00:00:00Z', updatedAt: '2026-05-05T00:00:00Z' },
  { id: '3', name: 'GATE 2026 CS', code: 'GATE-2026-CS', description: 'Graduate Aptitude Test in Engineering', date: '2026-02-10', duration: 180, totalMarks: 100, passingMarks: 25, sections: [{ id: 's7', name: 'General Aptitude', totalQuestions: 10, maxMarks: 15, marksPerQuestion: 1, negativeMarksPerQuestion: 0.33, cutoff: null }, { id: 's8', name: 'Core CS', totalQuestions: 55, maxMarks: 85, marksPerQuestion: 1, negativeMarksPerQuestion: 0.33, cutoff: null }], shifts: [], negativeMarkingEnabled: true, sectionalCutoffsEnabled: false, normalisationEnabled: true, status: 'RESULTS_DECLARED', createdAt: '2025-09-01T00:00:00Z', updatedAt: '2026-03-15T00:00:00Z' },
];

const statusVariant: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = { DRAFT: 'default', PUBLISHED: 'info', IN_PROGRESS: 'warning', COMPLETED: 'success', RESULTS_DECLARED: 'success' };

export default function Examinations() {
  const navigate = useNavigate();
  const [exams, setExams] = useState<Examination[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  useEffect(() => {
    examinationApi.list().then((res) => { setExams(res.data); }).catch(() => { setExams(DEMO_EXAMS); setIsDemo(true); }).finally(() => setLoading(false));
  }, []);

  const filtered = exams.filter((e) => {
    const matchSearch = e.name.toLowerCase().includes(search.toLowerCase()) || e.code.toLowerCase().includes(search.toLowerCase());
    const matchStatus = !statusFilter || e.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Examinations</h1>
          <p className="text-[var(--ef-fg-muted)] mt-1">Manage examination configurations</p>
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setShowCreate(true)}>Create Examination</Button>
      </div>
      {isDemo && <DemoDataBanner />}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1"><Input placeholder="Search examinations..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
        <Select options={[{ value: '', label: 'All Statuses' }, { value: 'DRAFT', label: 'Draft' }, { value: 'PUBLISHED', label: 'Published' }, { value: 'IN_PROGRESS', label: 'In Progress' }, { value: 'COMPLETED', label: 'Completed' }, { value: 'RESULTS_DECLARED', label: 'Results Declared' }]} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-full sm:w-48" />
      </div>
      {filtered.length === 0 && !loading ? (
        <EmptyState icon={<ClipboardList className="h-12 w-12" />} title="No examinations found" description="Create a new examination or adjust your filters." action={<Button onClick={() => setShowCreate(true)}>Create Examination</Button>} />
      ) : (
        <Table
          columns={[
            { key: 'code', header: 'Code', render: (e: Record<string, unknown>) => <span className="font-mono text-xs">{String(e.code)}</span> },
            { key: 'name', header: 'Examination', render: (e: Record<string, unknown>) => <span className="font-medium">{String(e.name)}</span> },
            { key: 'date', header: 'Date', render: (e: Record<string, unknown>) => new Date(String(e.date)).toLocaleDateString() },
            { key: 'duration', header: 'Duration', render: (e: Record<string, unknown>) => `${e.duration} min` },
            { key: 'totalMarks', header: 'Total Marks' },
            { key: 'sections', header: 'Sections', render: (e: Record<string, unknown>) => (e.sections as unknown[]).length },
            { key: 'status', header: 'Status', render: (e: Record<string, unknown>) => <Badge variant={statusVariant[String(e.status)] || 'default'}>{String(e.status).replace(/_/g, ' ')}</Badge> },
          ]}
          data={filtered as unknown as Record<string, unknown>[]}
          keyField="id"
          isLoading={loading}
          onRowClick={(e) => navigate(`/app/examinations/${e.id}`)}
        />
      )}
      <Dialog open={showCreate} onClose={() => setShowCreate(false)} title="Create New Examination" footer={<><Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button><Button onClick={() => setShowCreate(false)}>Create</Button></>}>
        <div className="space-y-4">
          <Input label="Examination Name" placeholder="e.g. JEE Main 2026 Session 2" />
          <Input label="Examination Code" placeholder="e.g. JEE-MAIN-2026-S2" />
          <Input label="Date" type="date" />
          <div className="grid grid-cols-2 gap-4"><Input label="Duration (min)" type="number" placeholder="180" /><Input label="Total Marks" type="number" placeholder="300" /></div>
          <Input label="Passing Marks" type="number" placeholder="75" />
        </div>
      </Dialog>
    </div>
  );
}
