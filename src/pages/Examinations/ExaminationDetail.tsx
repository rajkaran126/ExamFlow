// EXAMFLOW – Examination Detail Page
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, Settings, Clock, CheckCircle } from 'lucide-react';
import { Button, Card, Badge, Tabs, Skeleton, DemoDataBanner } from '../../components/ui';
import type { Examination, Shift } from '../../types';
import { examinationApi } from '../../api/client';

const DEMO: Examination = { id: '1', name: 'JEE Main 2026 Session 2', code: 'JEE-MAIN-2026-S2', description: 'Joint Entrance Examination Main Session 2 for engineering admissions across India.', date: '2026-04-15', duration: 180, totalMarks: 300, passingMarks: 75, sections: [{ id: 's1', name: 'Physics', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25, categoryWiseCutoffs: { GENERAL: 25, OBC: 22, SC: 20, ST: 18, EWS: 22 } }, { id: 's2', name: 'Chemistry', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25, categoryWiseCutoffs: { GENERAL: 25, OBC: 22, SC: 20, ST: 18, EWS: 22 } }, { id: 's3', name: 'Mathematics', totalQuestions: 30, maxMarks: 100, marksPerQuestion: 4, negativeMarksPerQuestion: 1, cutoff: 25, categoryWiseCutoffs: { GENERAL: 25, OBC: 22, SC: 20, ST: 18, EWS: 22 } }], shifts: [{ id: 'sh1', examinationId: '1', name: 'Shift A - Morning', date: '2026-04-15', startTime: '09:00', endTime: '12:00', totalCandidates: 12500, status: 'COMPLETED' }, { id: 'sh2', examinationId: '1', name: 'Shift B - Afternoon', date: '2026-04-15', startTime: '14:00', endTime: '17:00', totalCandidates: 11800, status: 'COMPLETED' }], negativeMarkingEnabled: true, sectionalCutoffsEnabled: true, normalisationEnabled: true, status: 'COMPLETED', createdAt: '2026-01-10T00:00:00Z', updatedAt: '2026-04-16T00:00:00Z' };

export default function ExaminationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [exam, setExam] = useState<Examination | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => { if (!id) return; examinationApi.get(id).then((r) => { setExam(r.data); }).catch(() => { setExam(DEMO); setIsDemo(true); }).finally(() => setLoading(false)); }, [id]);

  if (loading) return <div className="space-y-4">{[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24" />)}</div>;
  if (!exam) return <p className="text-[var(--ef-fg-muted)]">Examination not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/app/examinations')} leftIcon={<ArrowLeft className="h-4 w-4" />}>Back</Button>
        <div className="flex-1"><h1 className="text-2xl font-bold text-[var(--ef-fg)]">{exam.name}</h1><p className="text-[var(--ef-fg-muted)]">{exam.code}</p></div>
        <Badge variant={exam.status === 'COMPLETED' ? 'success' : 'info'}>{exam.status.replace(/_/g, ' ')}</Badge>
      </div>
      {isDemo && <DemoDataBanner />}
      <Tabs tabs={[{ id: 'overview', label: 'Overview', icon: <FileText className="h-4 w-4" /> }, { id: 'sections', label: 'Sections', icon: <Settings className="h-4 w-4" /> }, { id: 'shifts', label: 'Shifts', icon: <Clock className="h-4 w-4" /> }, { id: 'marking', label: 'Marking Scheme', icon: <CheckCircle className="h-4 w-4" /> }]} activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Total Marks</p><p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{exam.totalMarks}</p></Card>
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Duration</p><p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{exam.duration} min</p></Card>
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Passing Marks</p><p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{exam.passingMarks}</p></Card>
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Sections</p><p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{exam.sections.length}</p></Card>
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Shifts</p><p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{exam.shifts.length}</p></Card>
          <Card className="p-5"><p className="text-sm text-[var(--ef-fg-muted)]">Features</p><div className="flex flex-wrap gap-2 mt-2">{exam.negativeMarkingEnabled && <Badge variant="warning">Negative Marking</Badge>}{exam.sectionalCutoffsEnabled && <Badge variant="info">Sectional Cut-offs</Badge>}{exam.normalisationEnabled && <Badge variant="success">Normalisation</Badge>}</div></Card>
          <Card className="p-5 md:col-span-2 lg:col-span-3"><p className="text-sm text-[var(--ef-fg-muted)]">Description</p><p className="text-[var(--ef-fg)] mt-1">{exam.description}</p></Card>
        </div>
      )}

      {activeTab === 'sections' && (
        <div className="space-y-4">{exam.sections.map((s) => (
          <Card key={s.id} className="p-5">
            <div className="flex items-center justify-between mb-3"><h3 className="font-semibold text-[var(--ef-fg)]">{s.name}</h3><Badge>{s.totalQuestions} questions</Badge></div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div><span className="text-[var(--ef-fg-muted)]">Max Marks:</span> <span className="font-medium text-[var(--ef-fg)] ml-1">{s.maxMarks}</span></div>
              <div><span className="text-[var(--ef-fg-muted)]">Per Question:</span> <span className="font-medium text-[var(--ef-success)] ml-1">+{s.marksPerQuestion}</span></div>
              <div><span className="text-[var(--ef-fg-muted)]">Negative:</span> <span className="font-medium text-[var(--ef-error)] ml-1">−{s.negativeMarksPerQuestion}</span></div>
              <div><span className="text-[var(--ef-fg-muted)]">Cutoff:</span> <span className="font-medium text-[var(--ef-fg)] ml-1">{s.cutoff ?? 'N/A'}</span></div>
            </div>
            {s.categoryWiseCutoffs && Object.keys(s.categoryWiseCutoffs).length > 0 && (
              <div className="mt-3 pt-3 border-t border-[var(--ef-border-subtle)]">
                <p className="text-xs text-[var(--ef-fg-muted)] mb-2">Category-wise Cutoffs</p>
                <div className="flex flex-wrap gap-2">{Object.entries(s.categoryWiseCutoffs).map(([cat, val]) => <span key={cat} className="text-xs px-2 py-1 rounded bg-[var(--ef-bg-tertiary)] text-[var(--ef-fg-secondary)]">{cat}: {val}</span>)}</div>
              </div>
            )}
          </Card>
        ))}</div>
      )}

      {activeTab === 'shifts' && (
        <div className="overflow-x-auto rounded-[var(--ef-radius-lg)] border border-[var(--ef-border-subtle)]">
          <table className="w-full text-sm">
            <thead><tr className="bg-[var(--ef-bg-secondary)] border-b border-[var(--ef-border)]"><th className="px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)]">Shift</th><th className="px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)]">Date</th><th className="px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)]">Time</th><th className="px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)]">Candidates</th><th className="px-4 py-3 text-left font-semibold text-[var(--ef-fg-secondary)]">Status</th></tr></thead>
            <tbody>{exam.shifts.map((s) => <tr key={s.id} className="border-b border-[var(--ef-border-subtle)]"><td className="px-4 py-3 text-[var(--ef-fg)]">{s.name}</td><td className="px-4 py-3">{new Date(s.date).toLocaleDateString()}</td><td className="px-4 py-3">{s.startTime} – {s.endTime}</td><td className="px-4 py-3">{s.totalCandidates.toLocaleString()}</td><td className="px-4 py-3"><Badge variant={s.status === 'COMPLETED' ? 'success' : 'warning'}>{s.status}</Badge></td></tr>)}</tbody>
          </table>
        </div>
      )}

      {activeTab === 'marking' && (
        <Card className="p-5">
          <h3 className="font-semibold text-[var(--ef-fg)] mb-4">Marking Scheme</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm"><thead><tr className="border-b border-[var(--ef-border)]"><th className="text-left py-2 text-[var(--ef-fg-secondary)]">Section</th><th className="text-left py-2">Questions</th><th className="text-left py-2">Correct</th><th className="text-left py-2">Incorrect</th><th className="text-left py-2">Max</th></tr></thead>
              <tbody>{exam.sections.map((s) => <tr key={s.id} className="border-b border-[var(--ef-border-subtle)]"><td className="py-2 font-medium text-[var(--ef-fg)]">{s.name}</td><td className="py-2">{s.totalQuestions}</td><td className="py-2 text-[var(--ef-success)]">+{s.marksPerQuestion}</td><td className="py-2 text-[var(--ef-error)]">−{s.negativeMarksPerQuestion}</td><td className="py-2">{s.maxMarks}</td></tr>)}</tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
