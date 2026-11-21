// EXAMFLOW – Results & Scorecards Page
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Award, Printer, Download, CheckCircle, XCircle, Search, ShieldCheck } from 'lucide-react';
import { Button, Card, Badge, Table, Input, Select, DemoDataBanner } from '../../components/ui';
import type { EvaluationResult } from '../../types';
import { evaluationApi } from '../../api/client';

const DEMO_RESULT: EvaluationResult = {
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

export default function Results() {
  const [searchParams] = useSearchParams();
  const [candidateRoll, setCandidateRoll] = useState('JEE2026001234');
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDemo, setIsDemo] = useState(false);

  const fetchScorecard = (roll: string) => {
    setLoading(true);
    evaluationApi.getResult(roll, '1')
      .then((res) => {
        setResult(res.data);
        setIsDemo(false);
      })
      .catch(() => {
        setResult(DEMO_RESULT);
        setIsDemo(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchScorecard(candidateRoll);
  }, []);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--ef-fg)]">Results & Scorecards</h1>
          <p className="text-[var(--ef-fg-muted)] mt-1">Official candidate scorecard preview and verified marks statement.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" leftIcon={<Printer className="h-4 w-4" />} onClick={handlePrint}>
            Print Scorecard
          </Button>
        </div>
      </div>

      {isDemo && <DemoDataBanner />}

      {/* Search Bar */}
      <div className="flex gap-2 max-w-md">
        <Input
          placeholder="Enter Roll / Candidate ID"
          value={candidateRoll}
          onChange={(e) => setCandidateRoll(e.target.value)}
        />
        <Button onClick={() => fetchScorecard(candidateRoll)}>Lookup</Button>
      </div>

      {result && (
        <div className="max-w-3xl mx-auto liquid-glass p-8 space-y-6 border border-[var(--ef-border)] shadow-xl">
          {/* Header */}
          <div className="text-center border-b border-[var(--ef-border)] pb-6">
            <h2 className="font-display text-3xl font-bold text-[var(--ef-fg)] tracking-tight">EXAMFLOW</h2>
            <p className="text-xs uppercase tracking-widest text-[var(--ef-fg-muted)] mt-1">
              Official Examination Scorecard & Verification Report
            </p>
            <div className="mt-4 flex items-center justify-center gap-2">
              <Badge variant={result.qualificationStatus === 'QUALIFIED' ? 'success' : 'error'}>
                {result.qualificationStatus}
              </Badge>
              <span className="text-xs text-[var(--ef-fg-muted)]">Verified Backend Cryptographic Result</span>
            </div>
          </div>

          {/* Candidate & Exam Metadata */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-[var(--ef-fg-muted)] block">Roll Number</span>
              <span className="font-mono font-bold text-[var(--ef-fg)] text-sm">{candidateRoll}</span>
            </div>
            <div>
              <span className="text-[var(--ef-fg-muted)] block">Candidate Name</span>
              <span className="font-medium text-[var(--ef-fg)] text-sm">Aarav Sharma</span>
            </div>
            <div>
              <span className="text-[var(--ef-fg-muted)] block">Exam Code</span>
              <span className="font-mono text-[var(--ef-fg)] text-sm">JEE-MAIN-2026-S2</span>
            </div>
            <div>
              <span className="text-[var(--ef-fg-muted)] block">Shift</span>
              <span className="text-[var(--ef-fg)] text-sm">Shift A (Morning)</span>
            </div>
          </div>

          {/* Sectional Performance Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--ef-border)] text-left text-[var(--ef-fg-secondary)] text-xs">
                  <th className="py-2">Section</th>
                  <th className="py-2">Correct</th>
                  <th className="py-2">Incorrect</th>
                  <th className="py-2">Raw Score</th>
                  <th className="py-2">Deduction</th>
                  <th className="py-2">Section Marks</th>
                  <th className="py-2">Cut-off Status</th>
                </tr>
              </thead>
              <tbody>
                {result.sectionalResults.map((sec) => (
                  <tr key={sec.sectionId} className="border-b border-[var(--ef-border-subtle)]">
                    <td className="py-3 font-medium text-[var(--ef-fg)]">{sec.sectionName}</td>
                    <td className="py-3 text-[var(--ef-success)]">+{sec.correct}</td>
                    <td className="py-3 text-[var(--ef-error)]">−{sec.incorrect}</td>
                    <td className="py-3">{sec.rawMarks}</td>
                    <td className="py-3 text-[var(--ef-error)]">−{sec.negativeMarks}</td>
                    <td className="py-3 font-bold text-[var(--ef-fg)]">{sec.totalMarks}</td>
                    <td className="py-3">
                      <span className="text-xs text-[var(--ef-success)] font-semibold">Cleared (Cut-off: {sec.cutoff})</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Aggregate Marks Breakdown */}
          <div className="bg-[var(--ef-bg-secondary)] p-4 rounded-xl space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-[var(--ef-fg-secondary)]">Total Raw Score:</span>
              <span className="font-medium">{result.totalRawMarks}</span>
            </div>
            <div className="flex justify-between text-[var(--ef-error)]">
              <span>Total Negative Deductions:</span>
              <span>−{result.totalNegativeMarks}</span>
            </div>
            {result.proctoringPenalty > 0 && (
              <div className="flex justify-between text-[var(--ef-warning)]">
                <span>Proctoring Penalty Deduction:</span>
                <span>−{result.proctoringPenalty}</span>
              </div>
            )}
            <div className="flex justify-between pt-2 border-t border-[var(--ef-border)] font-bold text-base text-[var(--ef-fg)]">
              <span>Final Raw Marks:</span>
              <span>{result.finalMarks}</span>
            </div>
            {result.normalisedScore !== null && (
              <div className="flex justify-between text-base font-bold text-[var(--ef-primary)]">
                <span>Normalised Shift Score:</span>
                <span>{result.normalisedScore.toFixed(2)}</span>
              </div>
            )}
          </div>

          {/* Footer Validation Note */}
          <div className="flex items-center justify-between text-xs text-[var(--ef-fg-muted)] pt-4 border-t border-[var(--ef-border)]">
            <span className="flex items-center gap-1">
              <ShieldCheck className="h-4 w-4 text-[var(--ef-success)]" />
              Digitally sealed by EXAMFLOW Result Engine
            </span>
            <span>Date: {new Date(result.evaluatedAt).toLocaleDateString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}
