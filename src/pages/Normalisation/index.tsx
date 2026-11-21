// EXAMFLOW – Shift Normalisation Page
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BarChart3, TrendingUp, HelpCircle, Layers, SlidersHorizontal } from 'lucide-react';
import { Card, Badge, Table, Input, Select, DemoDataBanner } from '../../components/ui';
import type { ShiftStatistics } from '../../types';
import { normalisationApi } from '../../api/client';

const DEMO_STATS: ShiftStatistics[] = [
  { shiftId: 'sh1', shiftName: 'Shift A (Morning)', totalCandidates: 12500, appeared: 11980, meanScore: 142.60, medianScore: 139.50, standardDeviation: 38.40, highestScore: 292.00, lowestScore: -14.00, normalisationFactor: 1.042 },
  { shiftId: 'sh2', shiftName: 'Shift B (Afternoon)', totalCandidates: 11800, appeared: 11420, meanScore: 154.20, medianScore: 151.00, standardDeviation: 42.10, highestScore: 296.00, lowestScore: -8.00, normalisationFactor: 0.963 },
  { shiftId: 'sh3', shiftName: 'Shift C (Next Day Morning)', totalCandidates: 12200, appeared: 11650, meanScore: 138.80, medianScore: 135.00, standardDeviation: 36.90, highestScore: 288.00, lowestScore: -18.00, normalisationFactor: 1.071 },
];

export default function Normalisation() {
  const [searchParams] = useSearchParams();
  const examId = searchParams.get('examinationId') || '1';

  const [stats, setStats] = useState<ShiftStatistics[]>([]);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    setLoading(true);
    normalisationApi.getShiftStatistics(examId)
      .then((res) => {
        setStats(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setStats(DEMO_STATS);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [examId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Shift Normalisation</h1>
        <p className="text-[var(--ef-fg-muted)] mt-1">
          Statistical distribution across examination shifts. Standard deviation, mean difficulty variance, and backend-calibrated normalisation factors.
        </p>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Total Evaluated Shifts</p>
          <p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{stats.length}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Base Calibration Benchmark</p>
          <p className="text-2xl font-bold text-[var(--ef-primary)] mt-1">Shift B (154.20 Mean)</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-[var(--ef-fg-muted)]">Shift Difficulty Spread</p>
          <p className="text-2xl font-bold text-[var(--ef-info)] mt-1">Δ 15.40 pts</p>
        </Card>
      </div>

      {/* Shift Comparison Table */}
      <Card className="p-5">
        <h3 className="font-semibold text-[var(--ef-fg)] mb-4">Shift Distribution Statistics</h3>
        <Table
          columns={[
            {
              key: 'shiftName',
              header: 'Shift Name',
              render: (s: Record<string, unknown>) => (
                <span className="font-semibold text-[var(--ef-fg)]">{String(s.shiftName)}</span>
              ),
            },
            {
              key: 'appeared',
              header: 'Appeared Candidates',
              render: (s: Record<string, unknown>) => Number(s.appeared).toLocaleString(),
            },
            {
              key: 'meanScore',
              header: 'Mean Score (μ)',
              render: (s: Record<string, unknown>) => (
                <span className="font-mono">{Number(s.meanScore).toFixed(2)}</span>
              ),
            },
            {
              key: 'medianScore',
              header: 'Median',
              render: (s: Record<string, unknown>) => (
                <span className="font-mono">{Number(s.medianScore).toFixed(2)}</span>
              ),
            },
            {
              key: 'standardDeviation',
              header: 'Std Deviation (σ)',
              render: (s: Record<string, unknown>) => (
                <span className="font-mono">{Number(s.standardDeviation).toFixed(2)}</span>
              ),
            },
            {
              key: 'highestScore',
              header: 'Max Raw',
              render: (s: Record<string, unknown>) => (
                <span className="text-[var(--ef-success)] font-medium">{String(s.highestScore)}</span>
              ),
            },
            {
              key: 'lowestScore',
              header: 'Min Raw',
              render: (s: Record<string, unknown>) => (
                <span className="text-[var(--ef-error)] font-medium">{String(s.lowestScore)}</span>
              ),
            },
            {
              key: 'normalisationFactor',
              header: 'Factor Scale',
              render: (s: Record<string, unknown>) => (
                <Badge variant={Number(s.normalisationFactor) > 1 ? 'info' : 'default'}>
                  ×{Number(s.normalisationFactor).toFixed(3)}
                </Badge>
              ),
            },
          ]}
          data={stats as unknown as Record<string, unknown>[]}
          keyField="shiftId"
          isLoading={loading}
        />
        <div className="mt-4 p-4 rounded-lg bg-[var(--ef-bg-secondary)] text-xs text-[var(--ef-fg-secondary)] leading-relaxed">
          <p className="font-semibold text-[var(--ef-fg)] mb-1">Backend Equi-percentile / Mean-SD Normalisation Policy:</p>
          Scores are scaled in multi-shift sessions to counter relative paper difficulty differences. Normalised scores are calculated exclusively on server engines without duplicate arithmetic in UI code.
        </div>
      </Card>
    </div>
  );
}
