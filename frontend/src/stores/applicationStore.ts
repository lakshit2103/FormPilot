/**
 * applicationStore — Zustand store for the active application session state.
 * Tracks messages, status, jobs, questions, and review data.
 */
import { create } from 'zustand';
import type { AgentEvent } from '../hooks/useApplicationSocket';
import type { JobResult, MissingQuestion, ReviewSummary } from '../api/applications';

export interface MessageEntry {
  id: string;
  type: string;
  text: string;
  node?: string;
  timestamp: string;
  data?: AgentEvent;
}

export type ApplicationStatus =
  | 'idle'
  | 'searching'
  | 'selecting_job'
  | 'navigating'
  | 'extracting'
  | 'mapping'
  | 'asking'
  | 'filling'
  | 'validating'
  | 'reviewing'
  | 'paused'
  | 'complete'
  | 'failed';

interface ApplicationState {
  sessionId: string | null;
  status: ApplicationStatus;
  messages: MessageEntry[];
  jobResults: JobResult[];
  selectedJob: JobResult | null;
  manualActionRequired: boolean;
  manualActionReason: string | null;
  manualActionInstructions: string | null;
  questions: MissingQuestion[];
  reviewData: ReviewSummary | null;
  currentNode: string | null;

  // Actions
  setSessionId: (id: string | null) => void;
  setStatus: (status: ApplicationStatus) => void;
  addMessage: (msg: MessageEntry) => void;
  clearMessages: () => void;
  setJobResults: (jobs: JobResult[]) => void;
  selectJob: (job: JobResult) => void;
  setManualAction: (reason: string | null, instructions: string | null) => void;
  clearManualAction: () => void;
  setQuestions: (qs: MissingQuestion[]) => void;
  setReviewData: (data: ReviewSummary) => void;
  setCurrentNode: (node: string) => void;
  reset: () => void;
}

export const useApplicationStore = create<ApplicationState>((set) => ({
  sessionId: null,
  status: 'idle',
  messages: [],
  jobResults: [],
  selectedJob: null,
  manualActionRequired: false,
  manualActionReason: null,
  manualActionInstructions: null,
  questions: [],
  reviewData: null,
  currentNode: null,

  setSessionId: (id) => set({ sessionId: id }),
  setStatus: (status) => set({ status }),
  addMessage: (msg) => set(s => ({ messages: [...s.messages.slice(-99), msg] })),
  clearMessages: () => set({ messages: [] }),
  setJobResults: (jobs) => set({ jobResults: jobs, status: 'selecting_job' }),
  selectJob: (job) => set({ selectedJob: job }),
  setManualAction: (reason, instructions) => set({
    manualActionRequired: true,
    manualActionReason: reason,
    manualActionInstructions: instructions,
    status: 'paused',
  }),
  clearManualAction: () => set({
    manualActionRequired: false,
    manualActionReason: null,
    manualActionInstructions: null,
  }),
  setQuestions: (qs) => set({ questions: qs, status: 'asking' }),
  setReviewData: (data) => set({ reviewData: data, status: 'reviewing' }),
  setCurrentNode: (node) => set({ currentNode: node }),
  reset: () => set({
    sessionId: null, status: 'idle', messages: [], jobResults: [],
    selectedJob: null, manualActionRequired: false, manualActionReason: null,
    manualActionInstructions: null, questions: [], reviewData: null, currentNode: null,
  }),
}));
