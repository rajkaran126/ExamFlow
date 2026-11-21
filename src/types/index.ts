// ============================================================
// EXAMFLOW – Shared TypeScript Interfaces
// ============================================================

// ── Examination ──────────────────────────────────────────────

export interface Section {
  id: string;
  name: string;
  totalQuestions: number;
  maxMarks: number;
  marksPerQuestion: number;
  negativeMarksPerQuestion: number;
  cutoff: number | null;
  categoryWiseCutoffs?: Record<string, number>;
}

export interface Shift {
  id: string;
  examinationId: string;
  name: string;
  date: string;
  startTime: string;
  endTime: string;
  totalCandidates: number;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
}

export interface Examination {
  id: string;
  name: string;
  code: string;
  description: string;
  date: string;
  duration: number; // minutes
  totalMarks: number;
  passingMarks: number;
  sections: Section[];
  shifts: Shift[];
  negativeMarkingEnabled: boolean;
  sectionalCutoffsEnabled: boolean;
  normalisationEnabled: boolean;
  status: 'DRAFT' | 'PUBLISHED' | 'IN_PROGRESS' | 'COMPLETED' | 'RESULTS_DECLARED';
  createdAt: string;
  updatedAt: string;
}

// ── Candidate ────────────────────────────────────────────────

export interface Candidate {
  id: string;
  name: string;
  email: string;
  rollNumber: string;
  registrationNumber: string;
  category: 'GENERAL' | 'OBC' | 'SC' | 'ST' | 'EWS';
  isPwD: boolean;
  pwdType?: string;
  dateOfBirth: string;
  gender: 'MALE' | 'FEMALE' | 'OTHER';
  photoUrl?: string;
  examinationId: string;
  shiftId: string;
  status: 'REGISTERED' | 'APPEARED' | 'ABSENT' | 'DISQUALIFIED';
}

// ── Response ─────────────────────────────────────────────────

export type ResponseStatus =
  | 'ANSWERED'
  | 'NOT_ATTEMPTED'
  | 'MARKED_FOR_REVIEW'
  | 'ANSWERED_AND_MARKED_FOR_REVIEW';

export interface QuestionResponse {
  id: string;
  candidateId: string;
  examinationId: string;
  sectionId: string;
  questionNumber: number;
  selectedOption: string | null;
  status: ResponseStatus;
  timestamp: string;
  timeTaken: number; // seconds
}

export interface CandidateResponses {
  candidateId: string;
  examinationId: string;
  responses: QuestionResponse[];
  submittedAt: string;
}

// ── Evaluation ───────────────────────────────────────────────

export interface SectionalResult {
  sectionId: string;
  sectionName: string;
  attempted: number;
  correct: number;
  incorrect: number;
  notAttempted: number;
  markedForReview: number;
  rawMarks: number;
  negativeMarks: number;
  totalMarks: number;
  cutoff: number | null;
  cutoffCleared: boolean;
}

export interface EvaluationResult {
  id: string;
  candidateId: string;
  examinationId: string;
  sectionalResults: SectionalResult[];
  totalRawMarks: number;
  totalNegativeMarks: number;
  totalMarks: number;
  proctoringPenalty: number;
  finalMarks: number;
  normalisedScore: number | null;
  qualificationStatus: 'QUALIFIED' | 'NOT_QUALIFIED' | 'UNDER_REVIEW';
  failureReasons: string[];
  evaluatedAt: string;
}

// ── Proctoring ───────────────────────────────────────────────

export type ProctoringSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface ProctoringEvent {
  id: string;
  candidateId: string;
  examinationId: string;
  eventType: string;
  severity: ProctoringSeverity;
  description: string;
  timestamp: string;
  penalty: number;
  evidence?: string;
}

// ── Normalisation ────────────────────────────────────────────

export interface ShiftStatistics {
  shiftId: string;
  shiftName: string;
  totalCandidates: number;
  appeared: number;
  meanScore: number;
  medianScore: number;
  standardDeviation: number;
  highestScore: number;
  lowestScore: number;
  normalisationFactor: number;
}

// ── Merit List ───────────────────────────────────────────────

export interface MeritListEntry {
  rank: number;
  candidateId: string;
  candidateName: string;
  rollNumber: string;
  category: string;
  categoryRank: number | null;
  totalMarks: number;
  normalisedScore: number | null;
  qualificationStatus: string;
  shiftName: string;
}

// ── AI / Chat ────────────────────────────────────────────────

export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: string;
  status: 'UPLOADING' | 'PROCESSING' | 'READY' | 'FAILED';
  url?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  attachments?: Document[];
  isStreaming?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

// ── Re-evaluation ────────────────────────────────────────────

export interface ReEvaluationRequest {
  id: string;
  candidateId: string;
  examinationId: string;
  reason: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  originalMarks: number;
  revisedMarks: number | null;
  requestedAt: string;
  resolvedAt: string | null;
  resolvedBy: string | null;
  remarks: string | null;
}

// ── Dashboard ────────────────────────────────────────────────

export interface DashboardStats {
  totalExaminations: number;
  registeredCandidates: number;
  evaluatedCandidates: number;
  qualifiedCandidates: number;
  disqualifiedCandidates: number;
  proctoringFlags: number;
  evaluationProgress: number; // 0-100
  recentActivity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  type: 'EXAMINATION' | 'EVALUATION' | 'PROCTORING' | 'RESULT' | 'SYSTEM';
  message: string;
  timestamp: string;
}

// ── API ──────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, string[]>;
}

// ── User / Auth ──────────────────────────────────────────────

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'EXAMINER' | 'MODERATOR' | 'VIEWER';
  avatarUrl?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// ── Notifications ────────────────────────────────────────────

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  read: boolean;
  timestamp: string;
}
