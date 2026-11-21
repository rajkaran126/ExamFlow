// EXAMFLOW – Login & Administrative Authentication Page
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { LogIn, Shield, ArrowLeft, KeyRound, Mail, AlertCircle } from 'lucide-react';
import { Button, Card, Input } from '../../components/ui';
import { authApi } from '../../api/client';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@examflow.internal');
  const [password, setPassword] = useState('••••••••••••');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await authApi.login(email, password);
      localStorage.setItem('examflow_token', 'demo-token-examflow-controller');
      navigate('/app');
    } catch {
      // In demo mode, bypass gracefully so user can access all screens
      localStorage.setItem('examflow_token', 'demo-token-examflow-controller');
      navigate('/app');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--ef-bg)] flex flex-col justify-center items-center px-4 relative overflow-hidden">
      {/* Background Glass Orb */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[var(--ef-primary)]/10 rounded-full blur-3xl pointer-events-none" />

      <Link
        to="/"
        className="absolute top-8 left-8 flex items-center gap-2 text-sm text-[var(--ef-fg-secondary)] hover:text-[var(--ef-fg)] transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Landing
      </Link>

      <div className="w-full max-w-md liquid-glass p-8 space-y-6 border border-[var(--ef-border)] shadow-2xl relative z-10">
        <div className="text-center">
          <div className="inline-flex h-12 w-12 rounded-2xl bg-[var(--ef-primary)] text-[var(--ef-primary-fg)] items-center justify-center font-bold text-xl mb-3 shadow-lg shadow-[var(--ef-primary)]/20">
            EF
          </div>
          <h1 className="font-display text-3xl font-bold text-[var(--ef-fg)] tracking-tight">EXAMFLOW</h1>
          <p className="text-xs uppercase tracking-widest text-[var(--ef-fg-muted)] mt-1">
            Controller Administration Portal
          </p>
        </div>

        {error && (
          <div className="p-3 bg-[var(--ef-error-bg)] text-[var(--ef-error)] rounded-lg text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <Input
            label="Examination Controller Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />

          <Input
            label="Security Passkey"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={loading}
              leftIcon={<LogIn className="h-4 w-4" />}
            >
              Sign In to Workspace
            </Button>
          </div>
        </form>

        <div className="p-3 bg-[var(--ef-bg-secondary)] rounded-lg text-xs text-[var(--ef-fg-muted)] text-center leading-relaxed">
          Demo mode pre-authorized. Sign in provides full access to examination operations, evaluation graphs, and AI copilot.
        </div>
      </div>
    </div>
  );
}
