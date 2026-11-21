// EXAMFLOW – Evaluation Engine Page
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Calculator, Play, AlertTriangle, CheckCircle, XCircle, Award, ShieldAlert, ArrowRight } from 'lucide-react';
import { Button, Card, Badge, Table, Input, Select, DemoDataBanner, Dialog } from '../../components/ui';
import type { EvaluationResult, SectionalResult } from '../../types';
import { evaluationApi } from '../../api/client';

const DEMO_EVALUATION: EvaluationResult = {
  id: 'ev-1',
  candidateId: '1',
  examinationId: '1',
  sectionalResults: [
    { sectionId: 's1', sectionName: 'Physics', attempted: 28, correct: 24, incorrect: 4, notAttempted: 2, markedForReview: 1, rawMarks: 96, negativeMarks: 4, totalMarks: 92, cutoff: 25, cutoffCleared: true },
    { sectionId: 's2', sectionName: 'Chemistry', attempted: 26, correct: 22, incorrect: 4, notAttempted: 4, markedForReview: 0, rawMarks: 88, negativeMarks: 4, totalMarks: 84, cutoff: 25, cutoffCleared: true },
    { sectionId: 's3', sectionName: 'Mathematics', attempted: 29, correct: 25, incorrect: 4, notAttempted: 1, markedForReview: 2, rawMarks: 100, negativeMarks: 4, totalMarks: 96, cutoff: 25, cutoffCleared: true },
  ],
  totalRawMarks: 284,
  totalNegativeMarks: 12,
  totalMarks: 272,
  proctoringPenalty: 0,
  finalMarks: 272,
  normalisedScore: 281.45,
  qualificationStatus: 'QUALIFIED',
  failureReasons: [],
  evaluatedAt: '2026-04-16T11:20:00Z',
};

export default function Evaluation() {
  const [searchParams] = useSearchParams();
  const initialCandidate = searchParams.get('candidateId') || '1';
  const initialExam = searchParams.get('examinationId') || '1';

  const [candidateId, setCandidateId] = useState(initialCandidate);
  const [examinationId, setExaminationId] = useState(initialExam);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDemo, setIsDemo] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [triggerSuccess, setTriggerSuccess] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    evaluationApi.getResult(candidateId, examinationId)
      .then((res) => {
        setResult(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setResult(DEMO_EVALUATION);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  }, [candidateId, examinationId]);

  const handleTriggerEvaluation = async () => {
    setEvaluating(true);
    try {
      const res = await evaluationApi.triggerEvaluation(examinationId);
      setTriggerSuccess(`Evaluation engine batch job queued (Job ID: ${res.data.jobId})`);
    } catch {
      setTriggerSuccess('Batch evaluation job queued across cluster [Demonstration Simulation]');
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Evaluation Engine</h1>
          <p className="text-[var(--ef-fg-muted)] mt-1">
            Official backend-computed scores with negative marking, sectional cut-offs, and proctoring penalties.
          </p>
        </div>
        <Button
          leftIcon={<Play className="h-4 w-4" />}
          isLoading={evaluating}
          onClick={handleTriggerEvaluation}
        >
          Run Batch Evaluation
        </Button>
      </div>

      {isDemo && <DemoDataBanner />}

      {triggerSuccess && (
        <div className="p-3 bg-[var(--ef-success-bg)] text-[var(--ef-success)] rounded-lg text-sm flex items-center justify-between">
          <span>{triggerSuccess}</span>
          <Button variant="ghost" size="sm" onClick={() => setTriggerSuccess(null)}>Dismiss</Button>
        </div>
      )}

      {/* Candidate lookup controls */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Input
          label="Candidate ID"
          value={candidateId}
          onChange={(e) => setCandidateId(e.target.value)}
          placeholder="e.g. 1"
          className="w-full sm:w-48"
        />
        <Input
          label="Examination ID"
          value={examinationId}
          onChange={(e) => setExaminationId(e.target.value)}
          placeholder="e.g. 1"
          className="w-full sm:w-48"
        />
      </div>

      {result && (
        <>
          {/* Key Score Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Total Raw Marks</p>
              <p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">{result.totalRawMarks}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Negative Marking</p>
              <p className="text-2xl font-bold text-[var(--ef-error)] mt-1">−{result.totalNegativeMarks}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Proctoring Penalty</p>
              <p className="text-2xl font-bold text-[var(--ef-warning)] mt-1">
                {result.proctoringPenalty > 0 ? `−${result.proctoringPenalty}` : '0'}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Final Raw Score</p>
              <p className="text-2xl font-bold text-[var(--ef-primary)] mt-1">{result.finalMarks}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Normalised Score</p>
              <p className="text-2xl font-bold text-[var(--ef-fg)] mt-1">
                {result.normalisedScore !== null ? result.normalisedScore.toFixed(2) : 'N/A'}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs text-[var(--ef-fg-muted)]">Outcome</p>
              <div className="mt-1">
                <Badge variant={result.qualificationStatus === 'QUALIFIED' ? 'success' : 'error'}>
                  {result.qualificationStatus}
                </Badge>
              </div>
            </Card>
          </div>

          {/* Failure Reasons if any */}
          {result.failureReasons.length > 0 && (
            <div className="p-4 bg-[var(--ef-error-bg)] border border-[var(--ef-error)]/30 rounded-lg text-sm">
              <div className="flex items-center gap-2 font-semibold text-[var(--ef-error)] mb-1">
                <AlertTriangle className="h-4 w-4" />
                Qualification Failure Factors
              </div>
              <ul className="list-disc list-inside space-y-1 text-[var(--ef-fg)]">
                {result.failureReasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Section-Wise Breakdown Table */}
          <Card className="p-5">
            <h3 className="font-semibold text-[var(--ef-fg)] mb-4">Sectional Evaluation Breakdown</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--ef-border)] text-left text-[var(--ef-fg-secondary)]">
                    <th className="py-2.5 px-3">Section</th>
                    <th className="py-2.5 px-3">Attempted</th>
                    <th className="py-2.5 px-3">Correct</th>
                    <th className="py-2.5 px-3">Incorrect</th>
                    <th className="py-2.5 px-3">Unanswered</th>
                    <th className="py-2.5 px-3">Raw Marks</th>
                    <th className="py-2.5 px-3">Negative</th>
                    <th className="py-2.5 px-3">Total Marks</th>
                    <th className="py-2.5 px-3">Section Cut-off</th>
                    <th className="py-2.5 px-3">Cut-off Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.sectionalResults.map((sec) => (
                    <tr key={sec.sectionId} className="border-b border-[var(--ef-border-subtle)] hover:bg-[var(--ef-surface-hover)]">
                      <td className="py-3 px-3 font-medium text-[var(--ef-fg)]">{sec.sectionName}</td>
                      <td className="py-3 px-3 text-[var(--ef-fg)]">{sec.attempted}</td>
                      <td className="py-3 px-3 text-[var(--ef-success)] font-medium">+{sec.correct}</td>
                      <td className="py-3 px-3 text-[var(--ef-error)] font-medium">−{sec.incorrect}</td>
                      <td className="py-3 px-3 text-[var(--ef-fg-muted)]">{sec.notAttempted}</td>
                      <td className="py-3 px-3 text-[var(--ef-fg)]">{sec.rawMarks}</td>
                      <td className="py-3 px-3 text-[var(--ef-error)]">−{sec.negativeMarks}</td>
                      <td className="py-3 px-3 font-bold text-[var(--ef-fg)]">{sec.totalMarks}</td>
                      <td className="py-3 px-3 text-[var(--ef-fg-muted)]">{sec.cutoff ?? 'None'}</td>
                      <td className="py-3 px-3">
                        {sec.cutoff !== null ? (
                          <Badge variant={sec.cutoffCleared ? 'success' : 'error'}>
                            {sec.cutoffCleared ? 'Cleared' : 'Failed Cut-off'}
                          </Badge>
                        ) : (
                          <span className="text-xs text-[var(--ef-fg-muted)]">N/A</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-[var(--ef-fg-muted)] mt-4">
              * Note: Marks calculated per examination parameters on server: positive credits per right answer, deductions per wrong answer, sectional threshold check.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}
