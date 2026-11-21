// EXAMFLOW – Candidates Page
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users } from 'lucide-react';
import { Badge, Table, Input, Select, EmptyState, DemoDataBanner } from '../../components/ui';
import type { Candidate } from '../../types';
import { candidateApi } from '../../api/client';

const DEMO: Candidate[] = [
  { id: '1', name: 'Aarav Sharma', email: 'aarav@email.com', rollNumber: 'JEE2026001234', registrationNumber: 'REG001234', category: 'GENERAL', isPwD: false, dateOfBirth: '2004-05-14', gender: 'MALE', examinationId: '1', shiftId: 'sh1', status: 'APPEARED' },
  { id: '2', name: 'Priya Patel', email: 'priya@email.com', rollNumber: 'JEE2026001235', registrationNumber: 'REG001235', category: 'OBC', isPwD: false, dateOfBirth: '2004-08-22', gender: 'FEMALE', examinationId: '1', shiftId: 'sh1', status: 'APPEARED' },
  { id: '3', name: 'Rohan Kumar', email: 'rohan@email.com', rollNumber: 'JEE2026001236', registrationNumber: 'REG001236', category: 'SC', isPwD: true, pwdType: 'Visual Impairment', dateOfBirth: '2003-12-03', gender: 'MALE', examinationId: '1', shiftId: 'sh2', status: 'APPEARED' },
  { id: '4', name: 'Sneha Reddy', email: 'sneha@email.com', rollNumber: 'JEE2026001237', registrationNumber: 'REG001237', category: 'GENERAL', isPwD: false, dateOfBirth: '2004-02-28', gender: 'FEMALE', examinationId: '1', shiftId: 'sh2', status: 'DISQUALIFIED' },
  { id: '5', name: 'Vikram Singh', email: 'vikram@email.com', rollNumber: 'JEE2026001238', registrationNumber: 'REG001238', category: 'ST', isPwD: false, dateOfBirth: '2004-07-11', gender: 'MALE', examinationId: '1', shiftId: 'sh1', status: 'ABSENT' },
];

const sv: Record<string, 'default' | 'success' | 'warning' | 'error'> = { REGISTERED: 'default', APPEARED: 'success', ABSENT: 'warning', DISQUALIFIED: 'error' };

export default function Candidates() {
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => { candidateApi.list().then((r) => { setCandidates(r.data); }).catch(() => { setCandidates(DEMO); setIsDemo(true); }).finally(() => setLoading(false)); }, []);

  const filtered = candidates.filter((c) => {
    const ms = c.name.toLowerCase().includes(search.toLowerCase()) || c.rollNumber.toLowerCase().includes(search.toLowerCase());
    return ms && (!catFilter || c.category === catFilter) && (!statusFilter || c.status === statusFilter);
  });

  return (
    <div className="space-y-6">
      <div><h1 className="text-2xl font-bold text-[var(--ef-fg)]">Candidates</h1><p className="text-[var(--ef-fg-muted)] mt-1">View and manage registered candidates</p></div>
      {isDemo && <DemoDataBanner />}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1"><Input placeholder="Search by name or roll number..." value={search} onChange={(e) => setSearch(e.target.value)} /></div>
        <Select options={[{ value: '', label: 'All Categories' }, { value: 'GENERAL', label: 'General' }, { value: 'OBC', label: 'OBC' }, { value: 'SC', label: 'SC' }, { value: 'ST', label: 'ST' }, { value: 'EWS', label: 'EWS' }]} value={catFilter} onChange={(e) => setCatFilter(e.target.value)} className="w-full sm:w-40" />
        <Select options={[{ value: '', label: 'All Statuses' }, { value: 'REGISTERED', label: 'Registered' }, { value: 'APPEARED', label: 'Appeared' }, { value: 'ABSENT', label: 'Absent' }, { value: 'DISQUALIFIED', label: 'Disqualified' }]} value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-full sm:w-40" />
      </div>
      {filtered.length === 0 && !loading ? (
        <EmptyState icon={<Users className="h-12 w-12" />} title="No candidates found" description="Adjust your search or filters." />
      ) : (
        <Table columns={[
          { key: 'rollNumber', header: 'Roll Number', render: (r: Record<string, unknown>) => <span className="font-mono text-xs">{String(r.rollNumber)}</span> },
          { key: 'name', header: 'Name', render: (r: Record<string, unknown>) => <span className="font-medium">{String(r.name)}</span> },
          { key: 'category', header: 'Category', render: (r: Record<string, unknown>) => <Badge>{String(r.category)}</Badge> },
          { key: 'isPwD', header: 'PwD', render: (r: Record<string, unknown>) => r.isPwD ? <Badge variant="info">Yes</Badge> : <span className="text-[var(--ef-fg-muted)]">No</span> },
          { key: 'gender', header: 'Gender' },
          { key: 'status', header: 'Status', render: (r: Record<string, unknown>) => <Badge variant={sv[String(r.status)] || 'default'}>{String(r.status)}</Badge> },
        ]} data={filtered as unknown as Record<string, unknown>[]} keyField="id" isLoading={loading} onRowClick={(r) => navigate(`/app/candidates/${r.id}`)} emptyMessage="No candidates found" />
      )}
    </div>
  );
}
