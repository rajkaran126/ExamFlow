// EXAMFLOW – Candidate Detail
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, User, Mail, Calendar } from 'lucide-react';
import { Button, Card, Badge, DemoDataBanner, Skeleton } from '../../components/ui';
import type { Candidate } from '../../types';
import { candidateApi } from '../../api/client';

const DEMO: Candidate = { id: '1', name: 'Aarav Sharma', email: 'aarav@email.com', rollNumber: 'JEE2026001234', registrationNumber: 'REG001234', category: 'GENERAL', isPwD: false, dateOfBirth: '2004-05-14', gender: 'MALE', examinationId: '1', shiftId: 'sh1', status: 'APPEARED' };

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [c, setC] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => { if (!id) return; candidateApi.get(id).then((r) => setC(r.data)).catch(() => { setC(DEMO); setIsDemo(true); }).finally(() => setLoading(false)); }, [id]);

  if (loading) return <div className="space-y-4">{[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20" />)}</div>;
  if (!c) return <p className="text-[var(--ef-fg-muted)]">Candidate not found.</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/app/candidates')} leftIcon={<ArrowLeft className="h-4 w-4" />}>Back</Button>
        <div className="flex-1"><h1 className="text-2xl font-bold text-[var(--ef-fg)]">{c.name}</h1><p className="text-[var(--ef-fg-muted)]">{c.rollNumber}</p></div>
        <Badge variant={c.status === 'APPEARED' ? 'success' : c.status === 'DISQUALIFIED' ? 'error' : 'default'}>{c.status}</Badge>
      </div>
      {isDemo && <DemoDataBanner />}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-5 space-y-3">
          <h3 className="font-semibold text-[var(--ef-fg)]">Personal Information</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2"><User className="h-4 w-4 text-[var(--ef-fg-muted)]" /><span>{c.name}</span></div>
            <div className="flex items-center gap-2"><Mail className="h-4 w-4 text-[var(--ef-fg-muted)]" /><span>{c.email}</span></div>
            <div className="flex items-center gap-2"><Calendar className="h-4 w-4 text-[var(--ef-fg-muted)]" /><span>DOB: {new Date(c.dateOfBirth).toLocaleDateString()}</span></div>
            <div><span className="text-[var(--ef-fg-muted)]">Gender: </span>{c.gender}</div>
          </div>
        </Card>
        <Card className="p-5 space-y-3">
          <h3 className="font-semibold text-[var(--ef-fg)]">Examination Details</h3>
          <div className="space-y-2 text-sm">
            <div><span className="text-[var(--ef-fg-muted)]">Registration: </span><span className="font-mono">{c.registrationNumber}</span></div>
            <div><span className="text-[var(--ef-fg-muted)]">Roll Number: </span><span className="font-mono">{c.rollNumber}</span></div>
            <div className="flex items-center gap-2"><span className="text-[var(--ef-fg-muted)]">Category:</span><Badge>{c.category}</Badge></div>
            <div className="flex items-center gap-2"><span className="text-[var(--ef-fg-muted)]">PwD:</span>{c.isPwD ? <Badge variant="info">{c.pwdType || 'Yes'}</Badge> : 'No'}</div>
          </div>
        </Card>
      </div>
      <div className="flex gap-3">
        <Button variant="outline" onClick={() => navigate(`/app/responses?candidateId=${c.id}`)}>View Responses</Button>
        <Button variant="outline" onClick={() => navigate(`/app/evaluation?candidateId=${c.id}`)}>View Evaluation</Button>
      </div>
    </div>
  );
}
