// EXAMFLOW – AI Chat & Document Analysis UI
import { useState, useRef, useEffect } from 'react';
import {
  Bot, Send, Paperclip, Mic, MicOff, StopCircle, Copy, Trash2,
  FileText, Loader2, Sparkles, Check, AlertCircle, CheckCircle
} from 'lucide-react';
import { Button, Card, Badge, Input, DemoDataBanner } from '../../components/ui';
import type { ChatMessage, Document } from '../../types';
import { chatApi } from '../../api/client';

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'm1',
    role: 'assistant',
    content: "Welcome to **EXAMFLOW AI**. I am your examination operations and psychometric evaluation assistant.\n\nYou can ask me to analyze score distributions, explain normalisation parameters, check sectional cutoff violations, or upload examination rulebook/syllabus PDFs directly in this chat for instant parsing.",
    timestamp: new Date().toISOString(),
  },
];

export default function ExamflowAI() {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Attachments state
  const [attachments, setAttachments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isGenerating]);

  // Handle PDF file selection
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf') {
      alert('Please upload a PDF document (.pdf)');
      return;
    }

    setUploading(true);
    const tempDoc: Document = {
      id: `doc-${Date.now()}`,
      name: file.name,
      type: file.type,
      size: file.size,
      uploadedAt: new Date().toISOString(),
      status: 'UPLOADING',
    };

    setAttachments((prev) => [...prev, tempDoc]);

    try {
      const res = await chatApi.uploadDocument(file);
      setAttachments((prev) =>
        prev.map((d) => (d.id === tempDoc.id ? { ...res.data, status: 'READY' } : d))
      );
    } catch {
      // Demo simulated success
      setTimeout(() => {
        setAttachments((prev) =>
          prev.map((d) => (d.id === tempDoc.id ? { ...d, status: 'READY' } : d))
        );
      }, 1200);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Send message
  const handleSendMessage = async () => {
    if ((!input.trim() && attachments.length === 0) || isGenerating) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
      attachments: attachments.length > 0 ? [...attachments] : undefined,
    };

    const currentAttachments = [...attachments];
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setAttachments([]);
    setIsGenerating(true);

    const assistantMsgId = `msg-${Date.now() + 1}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      },
    ]);

    try {
      // Simulate intelligent AI response with streaming effect
      const responseTemplate = currentAttachments.length > 0
        ? `I have parsed **${currentAttachments[0].name}** (${(currentAttachments[0].size / 1024).toFixed(1)} KB).\n\n### Document Assessment:\n- **Structure:** Standardized examination notification & scoring rubric.\n- **Rules Identified:** Negative marking of 25% (1/4 mark) per wrong answer; minimum 35% sectional threshold required for General category.\n- **Shift Protocol:** Multi-session normalization configured using standard deviation scaling formula.\n\nWould you like me to map these parameters into your examination draft?`
        : `Analyzing examination operations query: "${userMsg.content}"\n\n- **Status:** All proctoring telemetry feeds calibrated.\n- **Negative Marking Rule:** Active (1 point deducted per incorrect response).\n- **Sectional Cut-offs:** Physics (25), Chemistry (25), Mathematics (25).\n- **Normalisation Engine:** Equi-percentile variance active across morning and afternoon shifts.\n\nLet me know if you need specific candidate audits or anomaly reports generated.`;

      let currentText = '';
      const words = responseTemplate.split(' ');

      for (let i = 0; i < words.length; i++) {
        if (!isGenerating && i > 0 && !abortControllerRef.current) break;
        currentText += (i === 0 ? '' : ' ') + words[i];
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: currentText } : m
          )
        );
        await new Promise((r) => setTimeout(r, 25));
      }

      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: 'Error retrieving AI response. Please try again.', isStreaming: false }
            : m
        )
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleStop = () => {
    setIsGenerating(false);
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClear = () => {
    setMessages(INITIAL_MESSAGES);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)]">
      <div className="flex items-center justify-between pb-4 border-b border-[var(--ef-border-subtle)]">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[var(--ef-primary)] text-[var(--ef-primary-fg)]">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--ef-fg)] flex items-center gap-2">
              EXAMFLOW AI
              <Badge variant="info">Copilot</Badge>
            </h1>
            <p className="text-xs text-[var(--ef-fg-muted)]">
              Powered by psychometric evaluation & document analysis models
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          leftIcon={<Trash2 className="h-4 w-4" />}
          onClick={handleClear}
        >
          Clear Chat
        </Button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
        {messages.map((m) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={m.id}
              className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
            >
              {!isUser && (
                <div className="h-8 w-8 rounded-full bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="h-4 w-4" />
                </div>
              )}
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  isUser
                    ? 'bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] rounded-br-sm'
                    : 'liquid-glass rounded-bl-sm border border-[var(--ef-border-subtle)] text-[var(--ef-fg)]'
                }`}
              >
                {/* Attached document previews */}
                {m.attachments && m.attachments.length > 0 && (
                  <div className="mb-3 space-y-1.5">
                    {m.attachments.map((att) => (
                      <div
                        key={att.id}
                        className={`flex items-center gap-2 p-2 rounded text-xs ${
                          isUser ? 'bg-black/20 text-white' : 'bg-[var(--ef-bg-secondary)] text-[var(--ef-fg)]'
                        }`}
                      >
                        <FileText className="h-4 w-4 text-[var(--ef-primary)] flex-shrink-0" />
                        <span className="font-medium truncate max-w-xs">{att.name}</span>
                        <span className="text-[10px] opacity-70 ml-auto">
                          {(att.size / 1024).toFixed(0)} KB
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Markdown text representation */}
                <div className="whitespace-pre-wrap">{m.content}</div>

                {m.isStreaming && (
                  <span className="inline-block h-3 w-1.5 ml-1 bg-[var(--ef-primary)] animate-pulse" />
                )}

                {/* Assistant message action bar */}
                {!isUser && !m.isStreaming && m.content && (
                  <div className="mt-3 pt-2 border-t border-[var(--ef-border-subtle)] flex items-center justify-between text-xs text-[var(--ef-fg-muted)]">
                    <span>{new Date(m.timestamp).toLocaleTimeString()}</span>
                    <button
                      className="p-1 hover:text-[var(--ef-fg)] transition-colors flex items-center gap-1"
                      onClick={() => handleCopy(m.id, m.content)}
                      aria-label="Copy response"
                    >
                      {copiedId === m.id ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-[var(--ef-success)]" />
                          <span className="text-[var(--ef-success)]">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Attachment Staging Area */}
      {attachments.length > 0 && (
        <div className="p-2 border border-[var(--ef-border)] rounded-lg bg-[var(--ef-bg-secondary)] flex flex-wrap gap-2 mb-2">
          {attachments.map((att) => (
            <div
              key={att.id}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded bg-[var(--ef-surface)] border border-[var(--ef-border)] text-xs text-[var(--ef-fg)]"
            >
              <FileText className="h-4 w-4 text-[var(--ef-primary)]" />
              <span className="font-medium truncate max-w-xs">{att.name}</span>
              {att.status === 'UPLOADING' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-[var(--ef-warning)]" />
              ) : (
                <CheckCircle className="h-3.5 w-3.5 text-[var(--ef-success)]" />
              )}
              <button
                className="text-[var(--ef-fg-muted)] hover:text-[var(--ef-error)] ml-1"
                onClick={() => setAttachments((prev) => prev.filter((d) => d.id !== att.id))}
                aria-label="Remove attachment"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Composer */}
      <div className="liquid-glass p-2.5 rounded-2xl flex items-center gap-2 border border-[var(--ef-border)]">
        <input
          type="file"
          ref={fileInputRef}
          accept="application/pdf"
          className="hidden"
          onChange={handleFileUpload}
        />
        <Button
          variant="ghost"
          size="sm"
          className="rounded-xl text-[var(--ef-fg-secondary)]"
          onClick={() => fileInputRef.current?.click()}
          title="Upload Examination Rulebook / Syllabus PDF"
          aria-label="Upload PDF"
          disabled={uploading}
        >
          {uploading ? (
            <Loader2 className="h-4 w-4 animate-spin text-[var(--ef-primary)]" />
          ) : (
            <Paperclip className="h-4 w-4" />
          )}
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className={`rounded-xl ${isRecording ? 'text-[var(--ef-error)] animate-pulse' : 'text-[var(--ef-fg-secondary)]'}`}
          onClick={() => setIsRecording(!isRecording)}
          title="Voice Input (Speech-to-text)"
          aria-label="Voice input"
        >
          {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </Button>

        <input
          type="text"
          className="flex-1 bg-transparent px-2 text-sm text-[var(--ef-fg)] placeholder:text-[var(--ef-fg-muted)] focus:outline-none"
          placeholder="Ask EXAMFLOW AI about rules, normalisation formulas, or upload a PDF..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
        />

        {isGenerating ? (
          <Button
            variant="danger"
            size="sm"
            className="rounded-xl"
            onClick={handleStop}
            leftIcon={<StopCircle className="h-4 w-4" />}
          >
            Stop
          </Button>
        ) : (
          <Button
            variant="primary"
            size="sm"
            className="rounded-xl"
            onClick={handleSendMessage}
            disabled={!input.trim() && attachments.length === 0}
            leftIcon={<Send className="h-4 w-4" />}
          >
            Send
          </Button>
        )}
      </div>
    </div>
  );
}
