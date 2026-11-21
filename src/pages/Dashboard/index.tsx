// EXAMFLOW – Dashboard Page
import { useState, useEffect } from 'react';
import {
  ClipboardList, Users, CheckCircle, XCircle, Shield, TrendingUp,
  Activity, BarChart3, Clock, Award,
} from 'lucide-react';
import { Card, Badge, DemoDataBanner, Skeleton } from '../../components/ui';
import type { DashboardStats, ActivityItem } from '../../types';
import { dashboardApi } from '../../api/client';

const DEMO_STATS: DashboardStats = {
  totalExaminations: 12,
  registeredCandidates: 45820,
  evaluatedCandidates: 38450,
  qualifiedCandidates: 29180,
  disqualifiedCandidates: 342,
  proctoringFlags: 1247,
  evaluationProgress: 84,
  recentActivity: [
    { id: '1', type: 'EXAMINATION', message: 'JEE Main 2026 Session 2 — Evaluation completed for Shift A', timestamp: '2026-11-21T10:30:00Z' },
    { id: '2', type: 'RESULT', message: 'NEET UG 2026 — Merit list generated successfully', timestamp: '2026-11-21T09:15:00Z' },
    { id: '3', type: 'PROCTORING', message: '23 new proctoring flags raised in CAT 2026 Shift B', timestamp: '2026-11-21T08:45:00Z' },
    { id: '4', type: 'EVALUATION', message: 'GATE 2026 CS — Sectional cut-offs applied', timestamp: '2026-11-21T07:30:00Z' },
    { id: '5', type: 'SYSTEM', message: 'Normalisation engine calibrated for multi-shift exams', timestamp: '2026-11-20T18:00:00Z' },
  ],
};

function StatCard({ icon: Icon, label, value, trend, color }: {
  icon: typeof ClipboardList;
  label: string;
  value: string | number;
  trend?: string;
  color: string;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--ef-fg-muted)] mb-1">{label}</p>
          <p className="text-2xl font-bold text-[var(--ef-fg)]">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend && (
            <p className="text-xs text-[var(--ef-success)] mt-1 flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              {trend}
            </p>
          )}
        </div>
        <div className={`p-2.5 rounded-xl ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}

function ActivityTypeIcon({ type }: { type: ActivityItem['type'] }) {
  const icons: Record<string, React.ReactNode> = {
    EXAMINATION: <ClipboardList className="h-4 w-4 text-[var(--ef-primary)]" />,
    EVALUATION: <CheckCircle className="h-4 w-4 text-[var(--ef-success)]" />,
    PROCTORING: <Shield className="h-4 w-4 text-[var(--ef-warning)]" />,
    RESULT: <Award className="h-4 w-4 text-[var(--ef-info)]" />,
    SYSTEM: <Activity className="h-4 w-4 text-[var(--ef-fg-muted)]" />,
  };
  return <>{icons[type] || null}</>;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi.getStats()
      .then((res) => { setStats(res.data); setIsDemo(false); })
      .catch(() => { setStats(DEMO_STATS); setIsDemo(true); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Dashboard</h1>
        <p className="text-[var(--ef-fg-muted)] mt-1">Examination operations overview</p>
      </div>

      {isDemo && <DemoDataBanner />}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={ClipboardList} label="Total Examinations" value={stats.totalExaminations} color="bg-[var(--ef-info-bg)] text-[var(--ef-info)]" />
        <StatCard icon={Users} label="Registered Candidates" value={stats.registeredCandidates} trend="+2.4% from last month" color="bg-[var(--ef-primary)]/10 text-[var(--ef-primary)]" />
        <StatCard icon={CheckCircle} label="Evaluated" value={stats.evaluatedCandidates} color="bg-[var(--ef-success-bg)] text-[var(--ef-success)]" />
        <StatCard icon={Award} label="Qualified" value={stats.qualifiedCandidates} color="bg-[var(--ef-success-bg)] text-[var(--ef-success)]" />
        <StatCard icon={XCircle} label="Disqualified" value={stats.disqualifiedCandidates} color="bg-[var(--ef-error-bg)] text-[var(--ef-error)]" />
        <StatCard icon={Shield} label="Proctoring Flags" value={stats.proctoringFlags} color="bg-[var(--ef-warning-bg)] text-[var(--ef-warning)]" />
        <StatCard icon={BarChart3} label="Evaluation Progress" value={`${stats.evaluationProgress}%`} color="bg-[var(--ef-info-bg)] text-[var(--ef-info)]" />
        <StatCard icon={Clock} label="Pending Evaluation" value={stats.registeredCandidates - stats.evaluatedCandidates} color="bg-[var(--ef-warning-bg)] text-[var(--ef-warning)]" />
      </div>

      <Card className="p-5">
        <h3 className="font-semibold text-[var(--ef-fg)] mb-3">Evaluation Progress</h3>
        <div className="w-full h-3 bg-[var(--ef-bg-tertiary)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--ef-primary)] rounded-full transition-all duration-500"
            style={{ width: `${stats.evaluationProgress}%` }}
            role="progressbar"
            aria-valuenow={stats.evaluationProgress}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
        <p className="text-sm text-[var(--ef-fg-muted)] mt-2">
          {stats.evaluatedCandidates.toLocaleString()} of {stats.registeredCandidates.toLocaleString()} candidates evaluated
        </p>
      </Card>

      <Card className="p-5">
        <h3 className="font-semibold text-[var(--ef-fg)] mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {stats.recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3 p-3 rounded-lg hover:bg-[var(--ef-surface-hover)] transition-colors">
              <div className="mt-0.5"><ActivityTypeIcon type={activity.type} /></div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[var(--ef-fg)]">{activity.message}</p>
                <p className="text-xs text-[var(--ef-fg-muted)] mt-0.5">{new Date(activity.timestamp).toLocaleString()}</p>
              </div>
              <Badge variant={activity.type === 'PROCTORING' ? 'warning' : 'default'}>{activity.type}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
