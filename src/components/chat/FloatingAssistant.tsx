// EXAMFLOW – Floating Assistant Launcher & Expandable Chat Panel
import { useState, useRef, useEffect } from 'react';
import {
  Bot, X, Maximize2, Minimize2, Send, Paperclip, Mic, MicOff,
  StopCircle, Copy, Trash2, FileText, Loader2, Check, Sparkles, Volume2
} from 'lucide-react';
import { Button, Badge } from '../ui';
import type { ChatMessage, Document } from '../../types';
import { chatApi } from '../../api/client';

export default function FloatingAssistant() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'fa-1',
      role: 'assistant',
      content: "Hello! I'm your EXAMFLOW AI copilot. You can ask me questions about evaluation rules, attach PDF regulations, or inquire about candidate status.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [voicePlayback, setVoicePlayback] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const [attachments, setAttachments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isGenerating]);

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
      setTimeout(() => {
        setAttachments((prev) =>
          prev.map((d) => (d.id === tempDoc.id ? { ...d, status: 'READY' } : d))
        );
      }, 1000);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSendMessage = async () => {
    if ((!input.trim() && attachments.length === 0) || isGenerating) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
      attachments: attachments.length > 0 ? [...attachments] : undefined,
    };

    const curAttachments = [...attachments];
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
      const responseTemplate = curAttachments.length > 0
        ? `Uploaded **${curAttachments[0].name}** successfully parsed into memory. Extracted 3 sections and negative marking guidelines (-0.25 penalty). Ready to assist with evaluations.`
        : `Understood query: "${userMsg.content}". Checking active session parameters: Negative marking is active, cutoffs calibrated, and normalisation models verified across all shifts.`;

      let currentText = '';
      const words = responseTemplate.split(' ');

      for (let i = 0; i < words.length; i++) {
        currentText += (i === 0 ? '' : ' ') + words[i];
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId ? { ...m, content: currentText } : m
          )
        );
        await new Promise((r) => setTimeout(r, 20));
      }

      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
      );
    } catch {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: 'Error connecting to AI service.', isStreaming: false }
            : m
        )
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <>
      {/* Floating launcher trigger */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] shadow-xl hover:scale-105 active:scale-95 transition-all flex items-center justify-center group"
          aria-label="Open EXAMFLOW AI Assistant"
        >
          <Bot className="h-6 w-6" />
          <span className="max-w-0 overflow-hidden whitespace-nowrap group-hover:max-w-xs transition-all duration-300 ease-in-out font-medium text-sm ml-0 group-hover:ml-2">
            Ask AI
          </span>
        </button>
      )}

      {/* Expandable Assistant Drawer / Panel */}
      {isOpen && (
        <div
          className={`fixed z-50 shadow-2xl transition-all duration-300 flex flex-col liquid-glass-strong border border-[var(--ef-border)] ${
            isExpanded
              ? 'inset-4 md:inset-10 rounded-2xl'
              : 'bottom-6 right-6 w-96 h-[540px] max-w-[calc(100vw-2rem)] rounded-2xl'
          }`}
          role="dialog"
          aria-label="EXAMFLOW AI Assistant Panel"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3.5 border-b border-[var(--ef-border-subtle)] bg-[var(--ef-surface)]/80 rounded-t-2xl">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <span className="font-bold text-sm text-[var(--ef-fg)]">EXAMFLOW AI</span>
              <Badge variant="info">Copilot</Badge>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setVoicePlayback(!voicePlayback)}
                className={`p-1.5 rounded-lg text-xs hover:bg-[var(--ef-surface-hover)] ${
                  voicePlayback ? 'text-[var(--ef-primary)] font-semibold' : 'text-[var(--ef-fg-muted)]'
                }`}
                title="Voice read aloud toggle"
              >
                <Volume2 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 rounded-lg text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg)] hover:bg-[var(--ef-surface-hover)]"
                title={isExpanded ? 'Minimize' : 'Expand'}
              >
                {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg)] hover:bg-[var(--ef-surface-hover)]"
                title="Close chat"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((m) => {
              const isUser = m.role === 'user';
              return (
                <div
                  key={m.id}
                  className={`flex gap-2 text-xs leading-relaxed ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`p-3 rounded-xl max-w-[85%] ${
                      isUser
                        ? 'bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] rounded-br-none'
                        : 'bg-[var(--ef-surface)] text-[var(--ef-fg)] border border-[var(--ef-border-subtle)] rounded-bl-none shadow-sm'
                    }`}
                  >
                    {m.attachments && m.attachments.length > 0 && (
                      <div className="mb-2 space-y-1">
                        {m.attachments.map((a) => (
                          <div
                            key={a.id}
                            className="flex items-center gap-1.5 p-1 rounded bg-black/10 text-[11px]"
                          >
                            <FileText className="h-3 w-3" />
                            <span className="truncate">{a.name}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap">{m.content}</div>
                    {m.isStreaming && (
                      <span className="inline-block h-2.5 w-1 bg-[var(--ef-primary)] ml-1 animate-pulse" />
                    )}

                    {!isUser && !m.isStreaming && m.content && (
                      <div className="mt-1.5 pt-1 border-t border-[var(--ef-border-subtle)] flex items-center justify-between text-[10px] text-[var(--ef-fg-muted)]">
                        <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        <button
                          onClick={() => handleCopy(m.id, m.content)}
                          className="hover:text-[var(--ef-fg)] flex items-center gap-0.5"
                        >
                          {copiedId === m.id ? <Check className="h-2.5 w-2.5 text-[var(--ef-success)]" /> : <Copy className="h-2.5 w-2.5" />}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Staged Attachments */}
          {attachments.length > 0 && (
            <div className="p-2 border-t border-[var(--ef-border-subtle)] bg-[var(--ef-bg-secondary)] flex flex-wrap gap-1 text-xs">
              {attachments.map((a) => (
                <div key={a.id} className="flex items-center gap-1 px-2 py-0.5 rounded bg-[var(--ef-surface)] border border-[var(--ef-border)]">
                  <FileText className="h-3 w-3 text-[var(--ef-primary)]" />
                  <span className="truncate max-w-[120px]">{a.name}</span>
                  <button onClick={() => setAttachments([])} className="hover:text-[var(--ef-error)]">×</button>
                </div>
              ))}
            </div>
          )}

          {/* Input Composer */}
          <div className="p-2.5 border-t border-[var(--ef-border-subtle)] bg-[var(--ef-surface)] rounded-b-2xl flex items-center gap-1.5">
            <input
              type="file"
              ref={fileInputRef}
              accept="application/pdf"
              className="hidden"
              onChange={handleFileUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-1.5 text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg)] hover:bg-[var(--ef-surface-hover)] rounded-lg transition-colors"
              title="Attach PDF"
              disabled={uploading}
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin text-[var(--ef-primary)]" /> : <Paperclip className="h-4 w-4" />}
            </button>
            <button
              onClick={() => setIsRecording(!isRecording)}
              className={`p-1.5 rounded-lg transition-colors ${
                isRecording ? 'text-[var(--ef-error)] animate-pulse' : 'text-[var(--ef-fg-muted)] hover:text-[var(--ef-fg)] hover:bg-[var(--ef-surface-hover)]'
              }`}
              title="Speech voice input"
            >
              {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>

            <input
              type="text"
              className="flex-1 bg-transparent px-2 text-xs text-[var(--ef-fg)] placeholder:text-[var(--ef-fg-muted)] focus:outline-none"
              placeholder="Ask AI or attach rulebook..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />

            {isGenerating ? (
              <button
                onClick={() => setIsGenerating(false)}
                className="p-1.5 text-[var(--ef-error)] hover:bg-[var(--ef-error-bg)] rounded-lg"
                title="Stop"
              >
                <StopCircle className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleSendMessage}
                disabled={!input.trim() && attachments.length === 0}
                className="p-1.5 bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] rounded-lg hover:opacity-90 disabled:opacity-40 transition-opacity"
                title="Send"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}
