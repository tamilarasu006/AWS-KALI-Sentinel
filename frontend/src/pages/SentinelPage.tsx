import { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Shield,
  Cpu,
  Sparkles,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Play,
  RotateCcw,
  Network,
  Globe,
  Terminal,
  FileCode,
  AlertTriangle,
  Send,
  Loader2,
} from 'lucide-react';
import {
  executeSentinel,
  fetchSentinelHealth,
  SentinelAgentResponse,
  SentinelHealth,
} from '../lib/sentinelApi';

const DEMO_PRESETS = [
  {
    label: 'Port Scan (Lab Server)',
    prompt: 'Check open ports on my authorized lab server 127.0.0.1',
    icon: Network,
    badge: 'PORT_SCAN',
    color: 'var(--color-accent, #38bdf8)',
  },
  {
    label: 'DNS Audit (Test Domain)',
    prompt: 'Verify the DNS configuration and SPF/DMARC records for our authorized test domain test.local',
    icon: Globe,
    badge: 'DNS_CHECK',
    color: '#34d399',
  },
  {
    label: 'Web Security Scan',
    prompt: 'Audit HTTP security headers and CSP policy on our staging web server localhost:8080',
    icon: Shield,
    badge: 'WEB_SCAN',
    color: '#a78bfa',
  },
  {
    label: 'Passive Recon',
    prompt: 'Perform passive OSINT reconnaissance on authorized lab infrastructure lab.local',
    icon: Terminal,
    badge: 'RECON',
    color: '#f472b6',
  },
  {
    label: 'Conversational (No Tool)',
    prompt: 'What is defense in depth and why is least privilege important in cybersecurity?',
    icon: Sparkles,
    badge: 'NO_TOOL',
    color: '#fbbf24',
  },
  {
    label: 'Unauthorized Target (Guardrail Block)',
    prompt: 'Scan open ports on victim-external-target.com',
    icon: ShieldAlert,
    badge: 'GUARDRAIL REJECT',
    color: '#f87171',
  },
];

export function SentinelPage() {
  const [prompt, setPrompt] = useState('Check open ports on my authorized lab server 127.0.0.1');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SentinelAgentResponse | null>(null);
  const [health, setHealth] = useState<SentinelHealth | null>(null);
  const [rawJsonOpen, setRawJsonOpen] = useState(false);

  useEffect(() => {
    fetchSentinelHealth().then(setHealth).catch(() => {});
    // Auto-run first preset for instant visual demo
    handleRun('Check open ports on my authorized lab server 127.0.0.1');
  }, []);

  const handleRun = async (promptToRun?: string) => {
    const targetPrompt = promptToRun || prompt;
    if (!targetPrompt.trim() || loading) return;

    setLoading(true);
    try {
      const res = await executeSentinel(targetPrompt);
      setResponse(res);
    } catch (err) {
      console.error('Sentinel execution failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const getToolBadgeColor = (toolName: string) => {
    switch (toolName.toLowerCase()) {
      case 'port_scan':
        return '#0284c7';
      case 'dns_check':
        return '#059669';
      case 'web_scan':
        return '#7c3aed';
      case 'recon':
        return '#db2777';
      case 'no_tool':
        return '#d97706';
      default:
        return '#4b5563';
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto px-6 py-6 max-w-6xl mx-auto w-full space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-6 rounded-2xl border border-sky-500/20 bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-sky-950/40 backdrop-blur-xl shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-500/30 text-white font-bold">
            <ShieldCheck size={32} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                KALI SENTINEL
              </h1>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-sky-500/20 border border-sky-400/40 text-sky-300 font-mono font-semibold">
                AWS Strands Decider
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Autonomous Cybersecurity Decision Agent • Amazon Bedrock + Strands Decider 2B
            </p>
          </div>
        </div>

        {/* Live Status Indicators */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Cpu size={14} className="text-cyan-400" />
            <span>Decider 2B:</span>
            <span className="text-emerald-400 font-semibold font-mono">Active (Pointer Head)</span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Sparkles size={14} className="text-amber-400" />
            <span>Bedrock:</span>
            <span className="text-amber-300 font-semibold font-mono">
              {health?.bedrock_live ? 'AWS Bedrock Live' : 'Converse Engine'}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-xs text-emerald-300">
            <ShieldCheck size={14} />
            <span>Scope:</span>
            <span className="font-semibold">Authorized Only</span>
          </div>
        </div>
      </div>

      {/* Preset Quick Actions for 3-Minute Hackathon Demo */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Play size={12} className="text-sky-400" /> Hackathon Demo Scenarios
          </span>
          <span className="text-xs text-slate-500">Click to run instant agent workflow</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          {DEMO_PRESETS.map((preset) => {
            const Icon = preset.icon;
            const isCurrent = prompt === preset.prompt;
            return (
              <button
                key={preset.label}
                onClick={() => {
                  setPrompt(preset.prompt);
                  handleRun(preset.prompt);
                }}
                disabled={loading}
                className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all cursor-pointer ${
                  isCurrent
                    ? 'border-sky-400 bg-sky-950/40 shadow-md shadow-sky-500/10'
                    : 'border-slate-800 bg-slate-900/50 hover:border-slate-700 hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1.5">
                  <Icon size={16} style={{ color: preset.color }} />
                  <span
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded"
                    style={{ background: `${preset.color}22`, color: preset.color }}
                  >
                    {preset.badge}
                  </span>
                </div>
                <span className="text-xs font-medium text-slate-200 line-clamp-2">
                  {preset.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Prompt Input Form */}
      <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/70 shadow-lg backdrop-blur-md">
        <label className="block text-xs font-medium text-slate-400 mb-2">
          Security Task Prompt (Authorized Lab Target)
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRun()}
            placeholder="e.g., Check open ports on my authorized lab server 127.0.0.1"
            className="flex-1 bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
          />
          <button
            onClick={() => handleRun()}
            disabled={loading || !prompt.trim()}
            className="px-5 py-2.5 rounded-xl font-medium text-sm text-white bg-gradient-to-r from-sky-600 to-cyan-500 hover:from-sky-500 hover:to-cyan-400 disabled:opacity-50 transition-all flex items-center gap-2 shadow-lg shadow-sky-500/20 cursor-pointer"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span>Analyze</span>
          </button>
        </div>
      </div>

      {/* Main Hackathon Decision & Execution Display */}
      {response && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {/* Top Decision HUD: 3 Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Card 1: Strands Decider 2B Decision */}
            <div className="p-5 rounded-2xl border border-sky-500/30 bg-slate-900/80 backdrop-blur-md relative overflow-hidden shadow-xl">
              <div className="absolute top-0 right-0 w-32 h-32 bg-sky-500/10 rounded-full blur-2xl pointer-events-none" />
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                  <Cpu size={14} /> STRANDS DECIDER 2B
                </span>
                <span className="text-xs font-mono text-slate-400">System One</span>
              </div>

              <div className="mt-2">
                <div className="text-xs text-slate-400">Chosen Security Tool:</div>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className="text-lg font-black tracking-wider px-3 py-1 rounded-lg font-mono text-white shadow-inner"
                    style={{ background: getToolBadgeColor(response.decider_decision.tool) }}
                  >
                    {response.decider_decision.tool.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-800 text-xs">
                <div>
                  <div className="text-slate-500">Confidence</div>
                  <div className="text-base font-bold text-sky-300 font-mono mt-0.5">
                    {(response.decider_decision.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-slate-500">Decision Latency</div>
                  <div className="text-base font-bold text-emerald-400 font-mono mt-0.5 flex items-center gap-1">
                    <Clock size={14} />
                    {response.decider_decision.latency_ms.toFixed(1)} ms
                  </div>
                </div>
              </div>

              {/* Tool Probabilities Bar */}
              {response.decider_decision.probabilities && (
                <div className="mt-3 pt-3 border-t border-slate-800">
                  <div className="text-[11px] text-slate-400 mb-1.5 flex justify-between">
                    <span>Option Probabilities:</span>
                    <span className="font-mono text-sky-400">Single Forward Pass</span>
                  </div>
                  <div className="space-y-1">
                    {Object.entries(response.decider_decision.probabilities).map(([key, val]) => (
                      <div key={key} className="flex items-center gap-2 text-[10px] font-mono">
                        <span className="w-16 truncate text-slate-400">{key}:</span>
                        <div className="flex-1 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.max(val * 100, 3)}%`,
                              background:
                                key === response.decider_decision.tool ? '#38bdf8' : '#475569',
                            }}
                          />
                        </div>
                        <span className="w-9 text-right text-slate-300">{(val * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Card 2: Grounding & Authorization Guardrail */}
            <div
              className={`p-5 rounded-2xl border backdrop-blur-md relative overflow-hidden shadow-xl ${
                response.guardrail_decision.verdict === 'ALLOW'
                  ? 'border-emerald-500/30 bg-emerald-950/20'
                  : 'border-rose-500/40 bg-rose-950/25'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span
                  className={`text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                    response.guardrail_decision.verdict === 'ALLOW'
                      ? 'text-emerald-400'
                      : 'text-rose-400'
                  }`}
                >
                  {response.guardrail_decision.verdict === 'ALLOW' ? (
                    <ShieldCheck size={14} />
                  ) : (
                    <ShieldAlert size={14} />
                  )}
                  GUARDRAIL BOUNDARY
                </span>
                <span className="text-xs font-mono text-slate-400">Noul Gate</span>
              </div>

              <div className="mt-2">
                <div className="text-xs text-slate-400">Safety Verdict:</div>
                <div className="mt-1 flex items-center gap-2">
                  <span
                    className={`text-lg font-black tracking-wider px-3 py-1 rounded-lg font-mono text-white flex items-center gap-1.5 ${
                      response.guardrail_decision.verdict === 'ALLOW' ? 'bg-emerald-600' : 'bg-rose-600'
                    }`}
                  >
                    {response.guardrail_decision.verdict === 'ALLOW' ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <XCircle size={16} />
                    )}
                    {response.guardrail_decision.verdict}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800 text-xs">
                <div className="text-slate-500 mb-1">Target Evaluation:</div>
                <div className="font-mono text-slate-200 bg-slate-950/60 p-2 rounded-lg border border-slate-800 text-[11px] break-all">
                  {response.guardrail_decision.target || 'No target specified'}
                </div>
                <p className="mt-2 text-slate-400 text-xs leading-relaxed">
                  {response.guardrail_decision.reasoning}
                </p>
              </div>
            </div>

            {/* Card 3: Execution Status */}
            <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Activity size={14} className="text-cyan-400" /> TOOL EXECUTION
                </span>
                <span className="text-xs font-mono text-slate-400">Telemetry</span>
              </div>

              <div className="mt-2">
                <div className="text-xs text-slate-400">Execution Status:</div>
                <div className="mt-1">
                  <span
                    className={`text-sm font-bold font-mono px-2.5 py-1 rounded-md ${
                      response.execution_status === 'COMPLETED'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
                        : response.execution_status === 'BLOCKED'
                        ? 'bg-rose-950 text-rose-400 border border-rose-500/40'
                        : 'bg-amber-950 text-amber-400 border border-amber-500/40'
                    }`}
                  >
                    {response.execution_status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-slate-800 text-xs">
                <div>
                  <div className="text-slate-500">Total Latency</div>
                  <div className="text-base font-bold text-slate-200 font-mono mt-0.5">
                    {response.total_latency_ms} ms
                  </div>
                </div>
                <div>
                  <div className="text-slate-500">Security Adapter</div>
                  <div className="text-sm font-semibold text-slate-200 font-mono mt-0.5">
                    {response.selected_tool}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800">
                <button
                  onClick={() => setRawJsonOpen(!rawJsonOpen)}
                  className="w-full text-xs py-1.5 px-3 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 font-mono flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                >
                  <FileCode size={13} />
                  <span>{rawJsonOpen ? 'Hide Raw JSON' : 'Inspect Raw JSON Payload'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Raw JSON Accordion */}
          {rawJsonOpen && (
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-950 font-mono text-xs text-slate-300 overflow-x-auto max-h-64">
              <pre>{JSON.stringify(response, null, 2)}</pre>
            </div>
          )}

          {/* Tool Result Findings List */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md shadow-lg">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 mb-3">
              <Terminal size={16} className="text-sky-400" /> Structured Tool Assessment Findings
            </h2>
            <div className="space-y-2">
              {response.result.findings && response.result.findings.length > 0 ? (
                response.result.findings.map((f: string, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/70 text-xs text-slate-200 font-mono"
                  >
                    <span className="text-sky-400 font-bold mt-0.5">›</span>
                    <span className="leading-relaxed">{f}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 italic">No direct tool findings recorded.</div>
              )}
            </div>
          </div>

          {/* Amazon Bedrock Generative Reasoning & Explanation */}
          <div className="p-6 rounded-2xl border border-amber-500/30 bg-gradient-to-br from-slate-900 via-slate-900/90 to-amber-950/20 backdrop-blur-xl shadow-xl">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-amber-500/20">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-amber-200 uppercase tracking-wider">
                    Amazon Bedrock Generative Security Analysis
                  </h2>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Model: {health?.bedrock_model || 'anthropic.claude-3-haiku-20240307-v1:0'}
                  </span>
                </div>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono">
                AI Explanation
              </span>
            </div>

            <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
              {response.explanation}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
export default SentinelPage;
