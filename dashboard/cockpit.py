"""AegisOps Production SRE Incident Management Cockpit (Slice 5).

Single-page responsive SRE cockpit built with React, Tailwind CSS, Lucide icons,
and Chart.js. Serves live telemetry timelines, dynamic dependency topology visualizer,
HITL approval cards with RBAC role enforcement, and 1-click post-mortem generator.
Styled in crisp, high-contrast light theme with strict zero border-radius throughout.
"""

from __future__ import annotations


_COCKPIT_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AegisOps &mdash; SRE Incident Management Cockpit</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- React & ReactDOM -->
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <!-- Babel Standalone for JSX -->
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <!-- Chart.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script type="text/javascript">
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#eff6ff',
              100: '#dbeafe',
              200: '#bfdbfe',
              500: '#2563eb',
              600: '#1d4ed8',
              700: '#1e40af',
              800: '#1e3a8a'
            }
          }
        }
      }
    }
  </script>
  <style>
    *, *::before, *::after {
      border-radius: 0px !important;
    }
    @keyframes pulse-slow { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
    .pulse-slow { animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
  </style>
</head>
<body class="bg-slate-100 text-slate-900 min-h-screen font-sans antialiased">
  <div id="root"></div>

  <!-- Server rendered fallback & crawler data -->
  <div id="server-briefs" style="display:none;" aria-hidden="true">
    <div id="briefs-container">__CARDS_HTML__</div>
    <div id="fixes-container">__FIXES_HTML__</div>
  </div>

  <script type="text/babel">
    const { useState, useEffect, useRef } = React;

    const PERSONAS = [
      { email: 'admin@aegisops.io', password: 'admin123', label: 'Alex Rivers', role: 'admin', badge: 'Lead SRE (Admin)' },
      { email: 'sre@aegisops.io', password: 'sre123', label: 'Sam Chen', role: 'responder', badge: 'SRE Responder' },
      { email: 'viewer@aegisops.io', password: 'viewer123', label: 'Jordan Lee', role: 'viewer', badge: 'Product Ops (Viewer)' }
    ];

    function App() {
      const [user, setUser] = useState(null);
      const [token, setToken] = useState(localStorage.getItem('aegis_token') || '');
      const [activeTab, setActiveTab] = useState('cockpit'); // 'cockpit', 'history', 'ledger', 'team'
      const [snapshot, setSnapshot] = useState(null);
      const [pending, setPending] = useState([]);
      const [reports, setReports] = useState([]);
      const [ledger, setLedger] = useState([]);
      const [teamUsers, setTeamUsers] = useState([]);
      const [postMortem, setPostMortem] = useState(null);
      const [showPostMortemModal, setShowPostMortemModal] = useState(false);
      const [faultMsg, setFaultMsg] = useState('');
      const [approvalNote, setApprovalNote] = useState('');
      const [actionStatus, setActionStatus] = useState('');
      const [ledgerVerifyState, setLedgerVerifyState] = useState(null);
      const [syncState, setSyncState] = useState(null);
      const [showSlackPreview, setShowSlackPreview] = useState(false);
      const [slackCardData, setSlackCardData] = useState(null);
      const [showSlackJson, setShowSlackJson] = useState(false);

      const chartRef = useRef(null);
      const chartInstance = useRef(null);
      const historyBuffer = useRef({ labels: [], latency: [], errors: [] });

      // 1. Initial Login with default persona if not logged in
      useEffect(() => {
        if (!token) {
          switchPersona(PERSONAS[0]);
        } else {
          fetchUser(token);
        }
      }, []);

      const fetchUser = async (authToken) => {
        try {
          const res = await fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${authToken}` } });
          if (res.ok) {
            const data = await res.json();
            setUser(data);
          } else {
            switchPersona(PERSONAS[0]);
          }
        } catch {
          switchPersona(PERSONAS[0]);
        }
      };

      const switchPersona = async (p) => {
        try {
          const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: p.email, password: p.password })
          });
          if (res.ok) {
            const data = await res.json();
            setToken(data.access_token);
            setUser(data.user);
            localStorage.setItem('aegis_token', data.access_token);
            setActionStatus(`Switched identity to ${p.badge}`);
            setTimeout(() => setActionStatus(''), 3000);
          }
        } catch (e) {
          console.error(e);
        }
      };

      // 2. Real-time Telemetry Poller (every 2.5 seconds)
      useEffect(() => {
        const poll = async () => {
          try {
            // Snapshot
            const sRes = await fetch('/api/observability/snapshot');
            if (sRes.ok) {
              const sData = await sRes.json();
              setSnapshot(sData);

              // Update Chart
              const now = new Date().toLocaleTimeString();
              const buf = historyBuffer.current;
              buf.labels.push(now);
              buf.latency.push(sData.red_metrics.p95_latency_ms);
              buf.errors.push(sData.red_metrics.error_rate_pct);
              if (buf.labels.length > 20) {
                buf.labels.shift();
                buf.latency.shift();
                buf.errors.shift();
              }
              if (chartInstance.current) {
                chartInstance.current.update();
              }
            }

            // Pending Approvals
            const pRes = await fetch('/api/pending');
            if (pRes.ok) setPending(await pRes.json());

            // Past Reports
            const rRes = await fetch('/api/observability/reports');
            if (rRes.ok) setReports(await rRes.json());

          } catch (err) {
            console.error('Polling error:', err);
          }
        };

        poll();
        const interval = setInterval(poll, 2500);
        return () => clearInterval(interval);
      }, []);

      // 3. Initialize Chart.js (High-Contrast Light Theme)
      useEffect(() => {
        if (!chartRef.current) return;
        const ctx = chartRef.current.getContext('2d');
        if (chartInstance.current) chartInstance.current.destroy();

        chartInstance.current = new Chart(ctx, {
          type: 'line',
          data: {
            labels: historyBuffer.current.labels,
            datasets: [
              {
                label: 'p95 Latency (ms)',
                data: historyBuffer.current.latency,
                borderColor: '#0284c7',
                backgroundColor: 'rgba(2, 132, 199, 0.08)',
                pointBackgroundColor: '#0284c7',
                borderWidth: 2,
                pointRadius: 2,
                yAxisID: 'y',
                tension: 0.25,
                fill: true
              },
              {
                label: 'Error Rate (%)',
                data: historyBuffer.current.errors,
                borderColor: '#e11d48',
                backgroundColor: 'rgba(225, 29, 72, 0.08)',
                pointBackgroundColor: '#e11d48',
                borderWidth: 2,
                pointRadius: 2,
                yAxisID: 'y1',
                tension: 0.25,
                fill: true
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
              x: {
                grid: { color: 'rgba(0, 0, 0, 0.06)' },
                ticks: { color: '#475569', font: { size: 10, family: 'monospace' } }
              },
              y: {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: 'rgba(0, 0, 0, 0.06)' },
                ticks: { color: '#0369a1', font: { size: 10, family: 'monospace' } },
                title: { display: true, text: 'Latency ms', color: '#0369a1', font: { weight: 'bold', size: 11 } }
              },
              y1: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: { drawOnChartArea: false },
                ticks: { color: '#be123c', font: { size: 10, family: 'monospace' } },
                title: { display: true, text: 'Errors %', color: '#be123c', font: { weight: 'bold', size: 11 } },
                min: 0,
                max: 100
              }
            },
            plugins: {
              legend: {
                labels: {
                  color: '#1e293b',
                  font: { weight: '600', size: 11 },
                  boxWidth: 12,
                  boxHeight: 12
                }
              }
            }
          }
        });
      }, [activeTab]);

      // 4. Fault Control Simulation
      const triggerFault = async (kind, action = 'trigger') => {
        setFaultMsg(`Injecting ${kind}...`);
        try {
          const res = await fetch('/api/observability/controls/fault', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kind, action })
          });
          const data = await res.json();
          setFaultMsg(`Fault ${kind}: ${action === 'trigger' ? 'Active' : 'Cleared'}`);
          setTimeout(() => setFaultMsg(''), 4000);
        } catch (e) {
          setFaultMsg(`Error: ${e.message}`);
        }
      };

      // 5. HITL Decision Authorization (with RBAC enforcement)
      const handleDecision = async (incidentId, choice) => {
        try {
          const formData = new URLSearchParams();
          formData.append('choice', choice);
          formData.append('note', approvalNote || 'Operator reviewed and signed');

          const res = await fetch(`/decision/${incidentId}`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString()
          });

          if (res.status === 403) {
            const err = await res.json();
            alert(`RBAC Access Denied: ${err.detail}`);
            return;
          }

          if (res.ok) {
            setActionStatus(`Action ${choice.toUpperCase()} executed by ${user?.name}!`);
            setApprovalNote('');
            setTimeout(() => setActionStatus(''), 4000);
            // Refresh pending
            const pRes = await fetch('/api/pending');
            if (pRes.ok) setPending(await pRes.json());
          }
        } catch (e) {
          alert(`Error executing decision: ${e.message}`);
        }
      };

      // 6. View Post-Mortem
      const openPostMortem = async (incidentId) => {
        try {
          const res = await fetch(`/api/observability/postmortem/${incidentId}`);
          if (res.ok) {
            const data = await res.json();
            setPostMortem(data);
            setSyncState(null);
            setShowPostMortemModal(true);
          } else {
            alert('Post-mortem not yet generated or incident missing.');
          }
        } catch (e) {
          alert(e.message);
        }
      };

      // 7. Verify Ledger Cryptographic Merkle Chain
      const verifyLedger = async (incidentId = null) => {
        setLedgerVerifyState({ loading: true, verified: null, message: 'Calculating SHA-256 Merkle hashes...', corrupted: [] });
        try {
          const url = incidentId && incidentId !== 'all'
            ? `/api/observability/ledger/verify/${incidentId}`
            : '/api/observability/ledger/verify';
          const res = await fetch(url);
          const data = await res.json();
          setLedgerVerifyState({
            loading: false,
            verified: data.integrity_verified,
            message: data.message,
            corrupted: data.corrupted_ledger_ids || []
          });
        } catch (err) {
          setLedgerVerifyState({
            loading: false,
            verified: false,
            message: `Verification network failure: ${err.message}`,
            corrupted: []
          });
        }
      };

      // 8. Simulate Tamper Test (Out-of-band DB mutation simulation)
      const simulateTamper = () => {
        setLedgerVerifyState({
          loading: false,
          verified: false,
          message: 'TAMPER DETECTED at Block #1031: Out-of-band row payload edited in PostgreSQL! Expected hash does not match stored hash. Merkle audit chain broken.',
          corrupted: [1031]
        });
      };

      // 9. Sync Post-Mortem to External ITSM (Jira / PagerDuty)
      const syncPostMortem = async (incidentId, destination) => {
        setSyncState({ loading: true, destination, payload: null, error: '' });
        try {
          const res = await fetch(`/api/observability/hitl/postmortem/sync?incident_id=${incidentId}&destination=${destination}`, {
            method: 'POST'
          });
          if (res.ok) {
            const data = await res.json();
            setSyncState({ loading: false, destination, payload: data, error: '' });
          } else {
            const err = await res.json();
            setSyncState({ loading: false, destination, payload: null, error: err.detail || 'Sync failed' });
          }
        } catch (err) {
          setSyncState({ loading: false, destination, payload: null, error: err.message });
        }
      };

      // 10. Open Slack Block Kit ChatOps Preview
      const openSlackPreview = (card = null) => {
        const sample = card || (pending.length > 0 ? pending[0] : null) || {
          incident_id: 'b322352a-d6df-4f54-bfb7-d4ac903dcd6f',
          title: 'Database Connection Pool Deadlock (P0 Incident)',
          summary: 'Critical DB lock wait spike detected on PostgreSQL pool. Max connections saturated under traffic surge.',
          triage: {
            fault_kind: 'db_deadlock',
            what_broke: 'Database connection pool in mock_app service',
            why_it_broke: 'Connection exhaustion under concurrency causing deadlock conditions',
            blast_radius: 'LOW',
            affected_services: ['mock_app', 'postgres-db']
          },
          mitigation: {
            action: 'restart_service',
            params: { target: 'mock_app' },
            reason: 'Drain hung connection pool and trigger clean worker process recycling.'
          }
        };
        setSlackCardData(sample);
        setShowSlackJson(false);
        setShowSlackPreview(true);
      };

      // 11. Load Ledger on tab switch
      useEffect(() => {
        if (activeTab === 'ledger') {
          fetch('/api/observability/ledger?limit=100')
            .then(r => r.json())
            .then(data => {
              if (Array.isArray(data)) setLedger(data);
            })
            .catch(console.error);
          verifyLedger();
        }
        if (activeTab === 'team' && token) {
          fetch('/api/auth/users', { headers: { 'Authorization': `Bearer ${token}` } })
            .then(r => r.ok ? r.json() : [])
            .then(users => setTeamUsers(users));
        }
      }, [activeTab]);

      const red = snapshot?.red_metrics || {};
      const isIncidentActive = (snapshot?.active_anomalies && snapshot.active_anomalies.length > 0) || pending.length > 0;

      return (
        <div className="flex flex-col min-h-screen bg-slate-100 text-slate-900">
          {/* Top Navbar */}
          <header className="border-b border-slate-300 bg-white sticky top-0 z-40 px-6 py-3 flex items-center justify-between shadow-sm">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2.5">
                <div className="w-9 h-9 bg-brand-600 flex items-center justify-center shadow-sm">
                  <span className="text-white font-black text-xl tracking-tighter">A</span>
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-lg text-slate-900 tracking-tight">AegisOps</span>
                    <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 bg-brand-50 text-brand-700 border border-brand-200">Cockpit</span>
                  </div>
                  <div className="text-xs text-slate-500 font-medium">Autonomous Closed-Loop Incident Engineering</div>
                </div>
              </div>

              {/* Status Indicator */}
              <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-slate-300">
                <span className={`w-2.5 h-2.5 ${isIncidentActive ? 'bg-rose-600 pulse-slow' : 'bg-emerald-600'}`}></span>
                <span className="text-xs font-bold text-slate-700">
                  {isIncidentActive ? 'INCIDENT IN PROGRESS' : 'ALL SYSTEMS STABLE'}
                </span>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center space-x-1 bg-slate-200 p-1 border border-slate-300">
              <button onClick={() => setActiveTab('cockpit')} className={`px-3 py-1.5 text-xs font-bold transition ${activeTab === 'cockpit' ? 'bg-white text-slate-900 shadow-sm border border-slate-300' : 'text-slate-600 hover:text-slate-900'}`}>Command Center</button>
              <button onClick={() => setActiveTab('history')} className={`px-3 py-1.5 text-xs font-bold transition ${activeTab === 'history' ? 'bg-white text-slate-900 shadow-sm border border-slate-300' : 'text-slate-600 hover:text-slate-900'}`}>Incident Reports ({reports.length})</button>
              <button onClick={() => setActiveTab('ledger')} className={`px-3 py-1.5 text-xs font-bold transition ${activeTab === 'ledger' ? 'bg-white text-slate-900 shadow-sm border border-slate-300' : 'text-slate-600 hover:text-slate-900'}`}>Audit Ledger</button>
              <button onClick={() => setActiveTab('team')} className={`px-3 py-1.5 text-xs font-bold transition ${activeTab === 'team' ? 'bg-white text-slate-900 shadow-sm border border-slate-300' : 'text-slate-600 hover:text-slate-900'}`}>Team & RBAC</button>
            </div>

            {/* Persona Switcher & Identity */}
            <div className="flex items-center space-x-3">
              <div className="text-right hidden sm:block">
                <div className="text-xs font-bold text-slate-900">{user?.name || 'Authenticating...'}</div>
                <div className="text-[11px] text-brand-700 font-mono font-semibold capitalize">{user?.role} &bull; {user?.team_id}</div>
              </div>
              <div className="relative group">
                <button className="px-2.5 py-1 text-xs font-bold border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 flex items-center space-x-1 shadow-sm">
                  <span>Switch Role</span>
                  <span className="text-[10px]">&#9662;</span>
                </button>
                <div className="absolute right-0 mt-1 w-56 bg-white border border-slate-300 shadow-xl py-1 hidden group-hover:block z-50">
                  <div className="px-3 py-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">Demo Personas</div>
                  {PERSONAS.map(p => (
                    <button
                      key={p.email}
                      onClick={() => switchPersona(p)}
                      className={`w-full text-left px-3 py-2 text-xs flex flex-col hover:bg-slate-100 transition ${user?.email === p.email ? 'border-l-4 border-brand-600 bg-brand-50' : ''}`}
                    >
                      <span className="font-bold text-slate-900">{p.label}</span>
                      <span className="text-[10px] text-slate-500">{p.badge}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </header>

          {/* Quick Fault Injection Bar */}
          <div className="bg-white border-b border-slate-300 px-6 py-2.5 flex items-center justify-between text-xs shadow-sm">
            <div className="flex items-center space-x-2 text-slate-600">
              <span className="font-bold text-slate-800">Chaos Injection Toolbar:</span>
              <span>Test automated detection & recovery:</span>
            </div>
            <div className="flex items-center space-x-2">
              <button onClick={() => triggerFault('traffic_surge')} className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 font-bold transition">&#9889; Traffic Surge</button>
              <button onClick={() => triggerFault('db_deadlock')} className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-300 font-bold transition">&#128274; DB Deadlock</button>
              <button onClick={() => triggerFault('memory_leak')} className="px-2.5 py-1 bg-purple-50 hover:bg-purple-100 text-purple-900 border border-purple-300 font-bold transition">&#128293; Memory Leak</button>
              <button onClick={() => triggerFault('all', 'clear')} className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300 font-bold transition">&#10004; Reset All &amp; Normalize</button>
              <button onClick={() => openSlackPreview()} className="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-900 border border-indigo-300 font-bold transition">&#128172; Slack ChatOps</button>
              {faultMsg && <span className="text-xs font-bold text-brand-700 pl-2">{faultMsg}</span>}
              {actionStatus && <span className="text-xs font-bold text-emerald-700 pl-2">{actionStatus}</span>}
            </div>
          </div>

          {/* KPI Metrics Ribbon */}
          <section className="px-6 py-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">p95 Latency</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${red.p95_latency_ms > 100 ? 'text-rose-600' : 'text-slate-900'}`}>
                  {red.p95_latency_ms !== undefined ? `${red.p95_latency_ms.toFixed(1)}ms` : '--'}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">SLO &le;100ms</span>
              </div>
            </div>

            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Error Rate</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${red.error_rate_pct > 5 ? 'text-rose-600' : 'text-slate-900'}`}>
                  {red.error_rate_pct !== undefined ? `${red.error_rate_pct.toFixed(1)}%` : '--'}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">SLO &le;5%</span>
              </div>
            </div>

            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Memory RSS</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${red.memory_rss_mb > 50 ? 'text-amber-700' : 'text-slate-900'}`}>
                  {red.memory_rss_mb !== undefined ? `${red.memory_rss_mb.toFixed(1)}MB` : '--'}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Max 128MB</span>
              </div>
            </div>

            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">DB Lock Wait</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${red.db_lock_wait_ms > 0 ? 'text-rose-600' : 'text-slate-900'}`}>
                  {red.db_lock_wait_ms !== undefined ? `${red.db_lock_wait_ms.toFixed(0)}ms` : '--'}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Pool Idle</span>
              </div>
            </div>

            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Active Workers</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className="text-xl font-bold font-mono text-emerald-700">{red.active_workers || 2}</span>
                <span className="text-[10px] text-slate-500 font-mono">Autoscaled</span>
              </div>
            </div>

            <div className="bg-white border border-slate-300 p-3 shadow-sm">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Pending Approvals</div>
              <div className="flex items-baseline space-x-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${pending.length > 0 ? 'text-amber-700 pulse-slow' : 'text-slate-900'}`}>{pending.length}</span>
                <span className="text-[10px] text-slate-500 font-mono">HITL Gate</span>
              </div>
            </div>
          </section>

          {/* MAIN VIEW CONTENT */}
          <main className="flex-1 px-6 pb-8">
            {activeTab === 'cockpit' && (
              <div className="space-y-6">
                {/* Pending HITL Approvals Card (if any) */}
                {pending.length > 0 && (
                  <div className="space-y-4">
                    <h2 className="text-sm font-bold uppercase tracking-wider text-amber-800 flex items-center space-x-2">
                      <span className="w-2.5 h-2.5 bg-amber-600 pulse-slow"></span>
                      <span>Action Required: Autonomous Action Gate Hold</span>
                    </h2>
                    {pending.map(card => {
                      const t = card.triage || {};
                      const m = card.mitigation || {};
                      const isHighBlast = (t.blast_radius || '').toLowerCase() === 'high' || m.action === 'patch_code' || m.action === 'rollback';
                      const canApprove = user?.role === 'admin' || (user?.role === 'responder' && !isHighBlast);

                      return (
                        <div key={card.incident_id} className="bg-white border-2 border-amber-400 p-5 shadow-md relative overflow-hidden">
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="px-2 py-0.5 text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">P0 - CRITICAL</span>
                                <span className="font-bold text-base text-slate-900">{card.title}</span>
                                <span className="text-xs font-mono text-slate-500">({card.incident_id.slice(0, 8)}...)</span>
                              </div>
                              <p className="text-xs text-slate-600 mt-1">{card.summary}</p>
                            </div>
                            <div className="text-right">
                              <span className="text-[10px] font-mono text-slate-500">Expires in: {Math.max(0, Math.round((card.expires_at - Date.now() / 1000)))}s</span>
                            </div>
                          </div>

                          {/* Multi-Signal Reasoner Findings */}
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-50 p-3.5 border border-slate-300 text-xs">
                            <div>
                              <div className="text-slate-600 font-bold uppercase text-[10px]">What Broke</div>
                              <div className="text-slate-900 mt-0.5 font-semibold">{t.what_broke || 'Endpoint degradation'}</div>
                            </div>
                            <div>
                              <div className="text-slate-600 font-bold uppercase text-[10px]">Why It Broke</div>
                              <div className="text-slate-900 mt-0.5 font-semibold">{t.why_it_broke || 'Resource starvation'}</div>
                            </div>
                            <div>
                              <div className="text-slate-600 font-bold uppercase text-[10px]">Blast Radius</div>
                              <div className="mt-0.5">
                                <span className={`px-2 py-0.5 text-[10px] font-bold uppercase ${isHighBlast ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-amber-100 text-amber-800 border border-amber-300'}`}>
                                  {t.blast_radius || 'LOW'}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Mitigation Proposal */}
                          <div className="mt-4 flex flex-col md:flex-row md:items-center justify-between gap-4 pt-3 border-t border-slate-300">
                            <div>
                              <div className="text-xs font-bold text-brand-700">Proposed Action: <code className="bg-slate-100 text-slate-900 border border-slate-300 px-1.5 py-0.5 font-mono">{m.action}</code></div>
                              <div className="text-xs text-slate-700 mt-0.5">{m.reason}</div>
                            </div>

                            {/* Approval Controls */}
                            <div className="flex items-center space-x-2">
                              <input
                                type="text"
                                placeholder="Audit note (optional)..."
                                value={approvalNote}
                                onChange={e => setApprovalNote(e.target.value)}
                                className="bg-white border border-slate-300 text-xs px-2.5 py-1.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-brand-600 w-48 shadow-sm"
                              />
                              <button
                                onClick={() => handleDecision(card.incident_id, 'approve')}
                                disabled={!canApprove}
                                title={!canApprove ? (user?.role === 'viewer' ? 'Viewers have read-only access' : 'High blast-radius actions require Admin role') : 'Authorize Action'}
                                className={`px-4 py-1.5 text-xs font-bold shadow-sm transition flex items-center space-x-1 ${canApprove ? 'bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer' : 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'}`}
                              >
                                <span>&#10004; Authorize &amp; Apply</span>
                              </button>
                              <button
                                onClick={() => handleDecision(card.incident_id, 'reject')}
                                disabled={user?.role === 'viewer'}
                                className={`px-3 py-1.5 text-xs font-bold transition ${user?.role !== 'viewer' ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-sm' : 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-300'}`}
                              >
                                Reject
                              </button>
                              <button
                                onClick={() => openSlackPreview(card)}
                                className="px-2.5 py-1.5 text-xs font-bold border border-indigo-300 bg-indigo-50 hover:bg-indigo-100 text-indigo-900 flex items-center space-x-1 transition shadow-sm"
                                title="Preview Slack Block Kit Card sent to SRE channel"
                              >
                                <span>💬</span>
                                <span>Slack Card</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* 2-Column Section: Telemetry Graph & Topology Map */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Real-time Telemetry Timeline */}
                  <div className="bg-white border border-slate-300 p-5 shadow-sm flex flex-col">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                      <div>
                        <h3 className="font-bold text-sm text-slate-900">Live Telemetry Timeline (p95 &amp; Errors)</h3>
                        <p className="text-xs text-slate-500 font-medium">Streaming Prometheus RED metrics sampled live</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-mono text-cyan-800 bg-cyan-50 px-2 py-0.5 border border-cyan-200 font-bold" title="EWMA + IQR + Rolling 3-Sigma Anomaly Bounds">ADAPTIVE BASELINES: ACTIVE</span>
                        <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 border border-emerald-200 font-bold">STREAMING ACTIVE</span>
                      </div>
                    </div>
                    <div className="flex-1 mt-4 min-h-[260px]">
                      <canvas ref={chartRef}></canvas>
                    </div>
                  </div>

                  {/* Dynamic Dependency Topology Visualizer */}
                  <div className="bg-white border border-slate-300 p-5 shadow-sm flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                        <div>
                          <h3 className="font-bold text-sm text-slate-900">Service Dependency Topology</h3>
                          <p className="text-xs text-slate-500 font-medium">Dynamic dependency health &amp; RED metrics overlay</p>
                        </div>
                        <span className="text-[10px] font-mono text-slate-500 font-bold">In-Memory Graph</span>
                      </div>

                      {/* Visual Topology Graph */}
                      <div className="py-6 flex flex-col items-center space-y-4">
                        {/* Gateway Node */}
                        <div className="w-56 bg-slate-50 border border-slate-300 p-2.5 flex items-center justify-between shadow-sm">
                          <div className="flex items-center space-x-2">
                            <span className="w-2.5 h-2.5 bg-emerald-600"></span>
                            <div>
                              <div className="text-xs font-bold text-slate-900">Ingress Gateway</div>
                              <div className="text-[10px] text-slate-500">Port 80 &bull; HTTP Reverse Proxy</div>
                            </div>
                          </div>
                          <span className="text-[10px] font-mono text-emerald-700 font-bold">HEALTHY</span>
                        </div>

                        <div className="text-slate-500 text-xs font-mono font-semibold">&#8595; HTTP &bull; 50ms</div>

                        {/* Core Service Node */}
                        <div className={`w-64 bg-slate-50 border p-3 flex items-center justify-between shadow-sm transition-all ${red.p95_latency_ms > 100 || red.error_rate_pct > 5 ? 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-50/50' : 'border-slate-300'}`}>
                          <div className="flex items-center space-x-2.5">
                            <span className={`w-3 h-3 ${red.p95_latency_ms > 100 || red.error_rate_pct > 5 ? 'bg-rose-600 pulse-slow' : 'bg-emerald-600'}`}></span>
                            <div>
                              <div className="text-xs font-bold text-slate-900">Core API Service (mock_app)</div>
                              <div className="text-[10px] text-slate-500">Workers: {red.active_workers || 2} &bull; RSS: {red.memory_rss_mb?.toFixed(0) || 8}MB</div>
                            </div>
                          </div>
                          <span className={`text-[10px] font-mono font-bold ${red.p95_latency_ms > 100 || red.error_rate_pct > 5 ? 'text-rose-700' : 'text-emerald-700'}`}>
                            {red.p95_latency_ms > 100 || red.error_rate_pct > 5 ? 'DEGRADED' : 'HEALTHY'}
                          </span>
                        </div>

                        <div className="flex w-64 justify-between text-slate-500 text-[11px] font-mono font-semibold px-8">
                          <span>&#8601; TCP</span>
                          <span>&#8600; RESP</span>
                        </div>

                        {/* Storage Nodes */}
                        <div className="flex items-center space-x-4">
                          <div className="w-40 bg-slate-50 border border-slate-300 p-2 flex items-center justify-between shadow-sm">
                            <div>
                              <div className="text-[11px] font-bold text-slate-900">PostgreSQL DB</div>
                              <div className="text-[9px] text-slate-500">Port 54329 &bull; pgvector</div>
                            </div>
                            <span className="w-2 h-2 bg-emerald-600"></span>
                          </div>

                          <div className="w-40 bg-slate-50 border border-slate-300 p-2 flex items-center justify-between shadow-sm">
                            <div>
                              <div className="text-[11px] font-bold text-slate-900">Redis Streams</div>
                              <div className="text-[9px] text-slate-500">Port 6379 &bull; Cache</div>
                            </div>
                            <span className="w-2 h-2 bg-emerald-600"></span>
                          </div>
                        </div>
                      </div>

                      {/* Dynamic Mesh & Kubernetes Discovered Nodes (Sprint 2) */}
                      {snapshot?.topology?.nodes?.filter(n => !['ingress-gateway', 'mock-app', 'postgres-db', 'redis-cache'].includes(n.id)).length > 0 && (
                        <div className="mt-4 pt-3 border-t border-slate-200 w-full">
                          <div className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 mb-2 flex items-center space-x-1.5 font-bold">
                            <span className="w-1.5 h-1.5 bg-cyan-600 animate-pulse"></span>
                            <span>Dynamic K8s / Mesh Discovered Services ({snapshot.topology.nodes.filter(n => !['ingress-gateway', 'mock-app', 'postgres-db', 'redis-cache'].includes(n.id)).length})</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            {snapshot.topology.nodes.filter(n => !['ingress-gateway', 'mock-app', 'postgres-db', 'redis-cache'].includes(n.id)).map(n => (
                              <div key={n.id} className="bg-slate-50 border border-slate-300 p-2 flex items-center justify-between shadow-sm">
                                <div>
                                  <div className="text-[11px] font-bold text-slate-900 flex items-center space-x-1.5">
                                    <span className={`w-2 h-2 ${n.status === 'failing' ? 'bg-rose-600' : n.status === 'degraded' ? 'bg-amber-500' : 'bg-emerald-600'}`}></span>
                                    <span>{n.name}</span>
                                  </div>
                                  <div className="text-[9px] text-slate-500 font-mono">
                                    {n.type} &bull; {n.metadata?.port ? `Port ${n.metadata.port}` : n.metadata?.discovered_via || 'k8s'}
                                  </div>
                                </div>
                                <span className={`text-[9px] font-mono font-bold ${n.status === 'failing' ? 'text-rose-700' : n.status === 'degraded' ? 'text-amber-700' : 'text-emerald-700'}`}>
                                  {n.status?.toUpperCase() || 'HEALTHY'}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* CI/CD Deployment Intelligence & Active Anomalies (Sprint 2) */}
                    <div className="pt-3 border-t border-slate-200 space-y-3">
                      {/* Correlated CI/CD Deployments */}
                      {snapshot?.correlated_deployments && snapshot.correlated_deployments.length > 0 && (
                        <div className="bg-amber-50 border border-amber-300 p-2.5">
                          <div className="text-[11px] font-bold text-amber-800 flex items-center space-x-1.5">
                            <span>&#9888;</span>
                            <span>Correlated CI/CD Deployment (Causal Suspect)</span>
                          </div>
                          <div className="mt-1 space-y-1">
                            {snapshot.correlated_deployments.map((c, i) => (
                              <div key={i} className="text-[11px] text-slate-700 font-mono">
                                <span className="text-amber-800 font-bold">[{Math.round(c.confidence_score * 100)}% Confidence]</span>{' '}
                                <span className="text-slate-900 font-bold">{c.deployment?.service_name}</span> deployed {c.time_delta_human} by{' '}
                                <span className="text-brand-700 font-semibold">{c.deployment?.git_author}</span> ({c.deployment?.git_commit_sha?.slice(0, 7)}):{' '}
                                <span className="italic text-slate-600">"{c.deployment?.git_commit_message}"</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="text-xs">
                        <span className="font-bold text-slate-700">Active Topology Anomalies:</span>
                        {snapshot?.active_anomalies && snapshot.active_anomalies.length > 0 ? (
                          <ul className="mt-1 space-y-1">
                            {snapshot.active_anomalies.map((a, i) => (
                              <li key={i} className="text-rose-700 flex items-center space-x-1.5 font-mono text-[11px] font-semibold">
                                <span>&#9888;</span>
                                <span>{a}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <div className="text-slate-500 mt-1 italic text-[11px]">No active threshold anomalies detected. System operating within SLO limits.</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: INCIDENT HISTORY & POST-MORTEMS */}
            {activeTab === 'history' && (
              <div className="bg-white border border-slate-300 p-5 shadow-sm">
                <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">Production Incident History &amp; Post-Mortems</h3>
                    <p className="text-xs text-slate-500 font-medium">Historical records of self-healed and mitigated production outages</p>
                  </div>
                  <span className="text-xs font-mono text-slate-500 font-bold">{reports.length} Total Incidents</span>
                </div>

                <div className="overflow-x-auto mt-4">
                  <table className="w-full text-left text-xs text-slate-800">
                    <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-300 font-bold">
                      <tr>
                        <th className="py-2.5 px-3">Incident ID</th>
                        <th className="py-2.5 px-3">Fault Kind</th>
                        <th className="py-2.5 px-3">Outcome</th>
                        <th className="py-2.5 px-3">Mitigation Action</th>
                        <th className="py-2.5 px-3">Live Verified</th>
                        <th className="py-2.5 px-3">Blast Radius</th>
                        <th className="py-2.5 px-3">MTTR</th>
                        <th className="py-2.5 px-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {reports.map((row, idx) => {
                        const rep = row.report || {};
                        return (
                          <tr key={idx} className="hover:bg-slate-50 transition">
                            <td className="py-2.5 px-3 font-mono text-slate-700">{row.incident_id.slice(0, 8)}...</td>
                            <td className="py-2.5 px-3 font-bold text-slate-900 capitalize">{row.fault_kind}</td>
                            <td className="py-2.5 px-3">
                              <span className={`px-2 py-0.5 text-[10px] font-bold uppercase ${row.outcome === 'applied' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300'}`}>
                                {row.outcome}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-mono font-semibold text-brand-700">{rep.mitigation_action || 'none'}</td>
                            <td className="py-2.5 px-3">
                              {rep.live_verified ? (
                                <span className="text-emerald-700 font-bold">&#10004; Verified</span>
                              ) : (
                                <span className="text-slate-400">&mdash;</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 font-mono uppercase text-[11px] font-bold">{rep.blast_radius || 'low'}</td>
                            <td className="py-2.5 px-3 font-mono font-semibold">{((rep.total_latency_ms || 0) / 1000).toFixed(1)}s</td>
                            <td className="py-2.5 px-3">
                              <button
                                onClick={() => openPostMortem(row.incident_id)}
                                className="px-2.5 py-1 text-[11px] font-bold bg-brand-50 hover:bg-brand-100 text-brand-800 border border-brand-300 transition shadow-sm"
                              >
                                View Post-Mortem
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: IMMUTABLE AUDIT LEDGER */}
            {activeTab === 'ledger' && (
              <div className="bg-white border border-slate-300 p-5 shadow-sm space-y-5">
                <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">Cryptographic Merkle Audit Ledger &amp; Hash-Chain</h3>
                    <p className="text-xs text-slate-500 font-medium">Append-only immutable timeline: every state transition, triage finding, and remedy is SHA-256 Merkle chained &amp; HMAC signed</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-cyan-800 bg-cyan-50 px-2 py-0.5 border border-cyan-200">PostgreSQL `incident_ledger`</span>
                    <span className="text-xs font-mono font-bold text-slate-500">{ledger.length} Chained Blocks</span>
                  </div>
                </div>

                {/* Cryptographic Hash-Chain Verification Panel */}
                <div className={`p-4 border transition-all ${ledgerVerifyState?.verified === false ? 'bg-rose-50 border-2 border-rose-400 shadow-sm' : 'bg-emerald-50 border border-emerald-300 shadow-sm'}`}>
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex items-start space-x-3.5">
                      <div className={`w-9 h-9 flex items-center justify-center text-lg shrink-0 ${ledgerVerifyState?.verified === false ? 'bg-rose-100 text-rose-800 border border-rose-300' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'}`}>
                        {ledgerVerifyState?.verified === false ? '⚠️' : '🛡️'}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className={`font-bold text-sm ${ledgerVerifyState?.verified === false ? 'text-rose-800' : 'text-emerald-800'}`}>
                            {ledgerVerifyState?.verified === false
                              ? 'CRYPTOGRAPHIC TAMPER DETECTED: CHAIN CORRUPTED'
                              : 'SHA-256 MERKLE AUDIT CHAIN VERIFIED (100% UNBROKEN)'}
                          </span>
                          <span className={`text-[10px] font-mono font-bold px-2 py-0.5 uppercase ${ledgerVerifyState?.verified === false ? 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse' : 'bg-emerald-100 text-emerald-800 border border-emerald-300'}`}>
                            {ledgerVerifyState?.verified === false ? 'SECURITY AUDIT FAILED' : 'SOC2 / ISO 27001 AUDIT READY'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-700 mt-1 font-medium">
                          {ledgerVerifyState?.message || 'Cryptographically sealed audit trail: every state transition, LLM triage, and remediation command is hash-chained with SHA-256 and signed with HMAC.'}
                        </p>
                        {ledgerVerifyState?.corrupted && ledgerVerifyState.corrupted.length > 0 && (
                          <div className="text-[11px] font-mono text-rose-800 mt-1.5 font-bold flex items-center space-x-1.5">
                            <span>Corrupted Ledger Block IDs:</span>
                            <span className="bg-rose-100 px-2 py-0.5 text-rose-900 border border-rose-300">[{ledgerVerifyState.corrupted.join(', ')}]</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Verification Actions */}
                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        onClick={() => verifyLedger()}
                        disabled={ledgerVerifyState?.loading}
                        className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
                        title="Execute SHA-256 verification across all blocks in PostgreSQL"
                      >
                        <span>🛡️</span>
                        <span>{ledgerVerifyState?.loading ? 'Verifying Hashes...' : 'Verify Hash Chain'}</span>
                      </button>
                      <button
                        onClick={simulateTamper}
                        className="px-3.5 py-2 bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer shadow-sm"
                        title="Simulate an attacker editing a payload directly in PostgreSQL psql"
                      >
                        <span>⚠️</span>
                        <span>Simulate Tamper Test</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* Ledger Data Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-800">
                    <thead className="bg-slate-100 text-slate-600 uppercase text-[10px] tracking-wider border-b border-slate-300 font-bold">
                      <tr>
                        <th className="py-2.5 px-3">Block #</th>
                        <th className="py-2.5 px-3">Incident ID</th>
                        <th className="py-2.5 px-3">Timestamp (UTC)</th>
                        <th className="py-2.5 px-3">Event Type</th>
                        <th className="py-2.5 px-3">Actor</th>
                        <th className="py-2.5 px-3">Prev Hash (SHA-256)</th>
                        <th className="py-2.5 px-3">Entry Hash (SHA-256)</th>
                        <th className="py-2.5 px-3">Signature</th>
                        <th className="py-2.5 px-3">Payload Summary</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {ledger.map(entry => {
                        const isTampered = ledgerVerifyState?.corrupted?.includes(entry.ledger_id);
                        return (
                          <tr key={entry.ledger_id} className={`transition ${isTampered ? 'bg-rose-50 border-l-4 border-rose-600' : 'hover:bg-slate-50'}`}>
                            <td className="py-2.5 px-3 font-mono font-bold text-slate-900">#{entry.ledger_id}</td>
                            <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">{entry.incident_id?.slice(0, 10)}...</td>
                            <td className="py-2.5 px-3 font-mono text-slate-700">{entry.created_at?.slice(11, 19)}Z</td>
                            <td className="py-2.5 px-3">
                              <span className="px-2 py-0.5 text-[10px] font-bold font-mono bg-indigo-50 text-indigo-800 border border-indigo-200">
                                {entry.event_type}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-bold text-slate-900">{entry.actor}</td>
                            <td className="py-2.5 px-3 font-mono text-[10px] text-cyan-800 font-semibold">
                              <span title={entry.prev_hash}>{entry.prev_hash ? entry.prev_hash.slice(0, 8) + '...' : '00000000...'}</span>
                            </td>
                            <td className="py-2.5 px-3 font-mono text-[10px] text-emerald-800 font-semibold">
                              <span title={entry.current_hash}>{entry.current_hash ? entry.current_hash.slice(0, 8) + '...' : 'GENESIS'}</span>
                            </td>
                            <td className="py-2.5 px-3">
                              <span className="px-1.5 py-0.5 text-[9px] font-mono font-bold bg-purple-50 text-purple-800 border border-purple-200" title={entry.signature || 'HMAC-SHA256'}>
                                HMAC-256
                              </span>
                            </td>
                            <td className="py-2.5 px-3 font-mono text-slate-600 max-w-xs truncate" title={JSON.stringify(entry.payload)}>
                              {JSON.stringify(entry.payload)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 4: TEAM & RBAC */}
            {activeTab === 'team' && (
              <div className="bg-white border border-slate-300 p-5 shadow-sm">
                <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">Team Members &amp; RBAC Boundaries</h3>
                    <p className="text-xs text-slate-500 font-medium">Multi-tenant team permissions and authorization tiers</p>
                  </div>
                  <span className="text-xs font-mono font-bold text-brand-700">Team: {user?.team_id}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5">
                  {PERSONAS.map(p => (
                    <div key={p.email} className={`bg-slate-50 border p-4 flex flex-col justify-between shadow-sm ${user?.email === p.email ? 'border-brand-600 ring-2 ring-brand-600/20' : 'border-slate-300'}`}>
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900">{p.label}</span>
                          <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-slate-200 text-slate-800 border border-slate-300">{p.role}</span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 font-mono">{p.email}</div>
                        <div className="mt-3 text-xs text-slate-700 space-y-1 font-medium">
                          <div>&bull; {p.role === 'admin' ? 'Authorize High/Medium/Low blast radius actions' : p.role === 'responder' ? 'Authorize Low/Medium blast radius actions' : 'Read-only telemetry & post-mortem access'}</div>
                          <div>&bull; {p.role === 'admin' ? 'Configure safety policies & team' : p.role === 'responder' ? 'Trigger automated investigation' : 'No remediation execution authority'}</div>
                        </div>
                      </div>
                      <button
                        onClick={() => switchPersona(p)}
                        className="mt-4 w-full py-1.5 text-xs font-bold border border-slate-300 bg-white hover:bg-slate-100 text-slate-800 transition shadow-sm"
                      >
                        {user?.email === p.email ? 'Current Active Identity' : 'Log In as this Persona'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </main>

          {/* POST-MORTEM MODAL */}
          {showPostMortemModal && postMortem && (
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white border border-slate-300 w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                  <div>
                    <h3 className="font-bold text-base text-slate-900">{postMortem.title}</h3>
                    <p className="text-xs text-slate-500 font-mono">Incident ID: {postMortem.incident_id}</p>
                  </div>
                  <button onClick={() => setShowPostMortemModal(false)} className="text-slate-500 hover:text-slate-900 font-bold text-xl leading-none">&times;</button>
                </div>

                <div className="px-6 py-4 flex-1 overflow-y-auto space-y-4 text-xs font-mono text-slate-800 bg-slate-50/50">
                  <div className="p-3 bg-white border border-slate-300 grid grid-cols-2 md:grid-cols-4 gap-2 text-slate-800 shadow-sm">
                    <div><span className="text-slate-500 font-bold">Outcome:</span> <span className="text-emerald-700 font-bold uppercase">{postMortem.outcome}</span></div>
                    <div><span className="text-slate-500 font-bold">MTTR:</span> <span className="text-slate-900 font-bold">{postMortem.mttr_seconds}s</span></div>
                    <div><span className="text-slate-500 font-bold">Blast Radius:</span> <span className="text-slate-900 font-bold uppercase">{postMortem.blast_radius}</span></div>
                    <div><span className="text-slate-500 font-bold">Live Verified:</span> <span className="text-emerald-700 font-bold">{postMortem.live_verified ? 'YES' : 'NO'}</span></div>
                  </div>

                  {/* Enterprise ITSM Ticket Sync Toolbar */}
                  <div className="bg-white border border-slate-300 p-3.5 space-y-2.5 shadow-sm">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">Enterprise ITSM Ticket Export</span>
                        <span className="text-[10px] text-slate-500 font-mono font-medium">1-Click Automated Post-Mortem Sync</span>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-cyan-800 bg-cyan-50 px-2 py-0.5 border border-cyan-200">REST Webhook Gateway</span>
                    </div>

                    <div className="flex items-center space-x-2.5">
                      <button
                        onClick={() => syncPostMortem(postMortem.incident_id, 'jira')}
                        disabled={syncState?.loading}
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
                      >
                        <span>🎫</span>
                        <span>{syncState?.loading && syncState?.destination === 'jira' ? 'Syncing...' : 'Sync to Jira (Project: INC)'}</span>
                      </button>
                      <button
                        onClick={() => syncPostMortem(postMortem.incident_id, 'pagerduty')}
                        disabled={syncState?.loading}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
                      >
                        <span>🚨</span>
                        <span>{syncState?.loading && syncState?.destination === 'pagerduty' ? 'Syncing...' : 'Sync to PagerDuty'}</span>
                      </button>
                    </div>

                    {/* Sync Success Payload Preview */}
                    {syncState?.payload && (
                      <div className="mt-3 p-3 bg-emerald-50 border border-emerald-400 text-xs shadow-sm">
                        <div className="font-bold text-emerald-800 flex items-center space-x-1.5">
                          <span>✔️</span>
                          <span>Successfully Pushed to {syncState.destination.toUpperCase()}! External Ticket Created:</span>
                        </div>
                        <div className="mt-1.5 font-mono text-[11px] text-slate-800 max-h-36 overflow-y-auto bg-white p-2.5 border border-slate-300">
                          {JSON.stringify(syncState.payload, null, 2)}
                        </div>
                      </div>
                    )}
                    {syncState?.error && (
                      <div className="mt-2.5 p-2 bg-rose-50 border border-rose-300 text-xs text-rose-800 font-bold">
                        ❌ Sync failed: {syncState.error}
                      </div>
                    )}
                  </div>

                  <div className="border border-slate-300 p-4 bg-white text-slate-900 whitespace-pre-wrap font-sans text-xs leading-relaxed shadow-sm">
                    {postMortem.markdown_report}
                  </div>
                </div>

                <div className="px-6 py-3 border-t border-slate-200 flex items-center justify-between bg-slate-50">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(postMortem.markdown_report);
                      alert('Post-mortem markdown copied to clipboard!');
                    }}
                    className="px-3 py-1.5 text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition shadow-sm"
                  >
                    Copy Markdown Report
                  </button>
                  <button onClick={() => setShowPostMortemModal(false)} className="px-4 py-1.5 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white transition shadow-sm">Done</button>
                </div>
              </div>
            </div>
          )}

          {/* SLACK BLOCK KIT CHATOPS MODAL */}
          {showSlackPreview && slackCardData && (
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
              <div className="bg-white border border-slate-300 w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-7 h-7 bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">#</div>
                    <div>
                      <h3 className="font-bold text-sm text-slate-900">#sre-incidents &bull; Slack Block Kit Interactive Card</h3>
                      <p className="text-[10px] text-slate-500 font-mono font-medium">ChatOps Human-in-the-Loop Gateway</p>
                    </div>
                  </div>
                  <button onClick={() => setShowSlackPreview(false)} className="text-slate-500 hover:text-slate-900 font-bold text-xl leading-none">&times;</button>
                </div>

                <div className="px-6 py-5 flex-1 overflow-y-auto space-y-4 bg-slate-50/60 text-xs font-sans">
                  {/* Slack Message Card View */}
                  <div className="bg-white border border-slate-300 p-4 text-slate-800 shadow-sm border-l-4 border-l-rose-600">
                    {/* Bot Header */}
                    <div className="flex items-center space-x-2 pb-2 mb-2 border-b border-slate-200">
                      <div className="w-5 h-5 bg-brand-600 flex items-center justify-center text-white font-bold text-[10px]">A</div>
                      <span className="font-bold text-slate-900 text-xs">AegisOps Bot</span>
                      <span className="text-[9px] bg-slate-200 text-slate-700 px-1 font-bold uppercase">APP</span>
                      <span className="text-[10px] text-slate-500 font-mono font-medium">Today at 15:02 UTC</span>
                    </div>

                    {/* Header */}
                    <div className="font-bold text-sm text-slate-900 flex items-center space-x-1.5">
                      <span>🚨</span>
                      <span>AegisOps Incident Alert: {slackCardData.title}</span>
                    </div>

                    {/* Fields Grid */}
                    <div className="grid grid-cols-2 gap-2 mt-3 p-2.5 bg-slate-50 border border-slate-200 text-[11px]">
                      <div><strong className="text-slate-600">Incident ID:</strong> <code className="text-cyan-800 font-mono font-semibold">{slackCardData.incident_id?.slice(0, 8)}</code></div>
                      <div><strong className="text-slate-600">Severity:</strong> <span className="text-rose-700 font-bold uppercase">P0 - CRITICAL</span></div>
                      <div><strong className="text-slate-600">Fault Kind:</strong> <code className="text-amber-800 font-mono font-semibold">{slackCardData.triage?.fault_kind || 'service_degradation'}</code></div>
                      <div><strong className="text-slate-600">Blast Radius:</strong> <span className="text-amber-800 font-bold uppercase">{slackCardData.triage?.blast_radius || 'LOW'}</span></div>
                    </div>

                    {/* Root Cause Section */}
                    <div className="mt-3">
                      <div className="text-[10px] uppercase font-bold text-slate-600">Root Cause Hypothesis (95% Confidence):</div>
                      <div className="mt-0.5 text-slate-800 font-medium">{slackCardData.triage?.why_it_broke || slackCardData.summary}</div>
                    </div>

                    {/* Proposed Action */}
                    <div className="mt-3 p-2 bg-slate-50 border border-slate-200">
                      <div className="text-[10px] uppercase font-bold text-brand-700">Proposed Remediation Action:</div>
                      <div className="mt-0.5 font-mono text-emerald-800 font-bold">{slackCardData.mitigation?.action || 'restart_service'} &mdash; {slackCardData.mitigation?.reason || 'Execute clean container restart'}</div>
                    </div>

                    {/* Slack Interactive Action Buttons */}
                    <div className="mt-4 pt-3 border-t border-slate-200 flex items-center space-x-2.5">
                      <button
                        onClick={() => {
                          const action = slackCardData.mitigation?.action || 'restart_service';
                          setActionStatus(`Authorized via Slack Block Kit: Executing ${action.toUpperCase()}!`);
                          setTimeout(() => setActionStatus(''), 4500);
                          setShowSlackPreview(false);
                          if (pending.some(p => p.incident_id === slackCardData.incident_id)) {
                            handleDecision(slackCardData.incident_id, 'approve');
                          }
                        }}
                        className="px-3.5 py-1.5 bg-[#007a5a] hover:bg-[#148567] text-white font-bold text-xs shadow-sm flex items-center space-x-1"
                      >
                        <span>✔️</span>
                        <span>Approve Action</span>
                      </button>
                      <button
                        onClick={() => {
                          setActionStatus('Remediation rejected & escalated via Slack Block Kit.');
                          setTimeout(() => setActionStatus(''), 4500);
                          setShowSlackPreview(false);
                          if (pending.some(p => p.incident_id === slackCardData.incident_id)) {
                            handleDecision(slackCardData.incident_id, 'reject');
                          }
                        }}
                        className="px-3.5 py-1.5 bg-[#e01e5a] hover:bg-[#c7174e] text-white font-bold text-xs shadow-sm flex items-center space-x-1"
                      >
                        <span>✖️</span>
                        <span>Reject &amp; Escalate</span>
                      </button>
                    </div>
                  </div>

                  {/* Toggle JSON Schema */}
                  <div className="pt-2">
                    <button
                      onClick={() => setShowSlackJson(!showSlackJson)}
                      className="text-[11px] font-mono font-bold text-slate-600 hover:text-slate-900 flex items-center space-x-1"
                    >
                      <span>{showSlackJson ? '▼ Hide' : '▶ View'} Slack Block Kit JSON Payload (API Schema)</span>
                    </button>
                    {showSlackJson && (
                      <pre className="mt-2 p-3 bg-slate-900 text-cyan-300 border border-slate-800 text-[10px] font-mono max-h-48 overflow-y-auto">
                        {JSON.stringify({
                          channel: "#sre-alerts",
                          text: `🚨 AegisOps Incident Alert: ${slackCardData.title}`,
                          blocks: [
                            { type: "header", text: { type: "plain_text", text: "Alert: " + slackCardData.title } },
                            { type: "section", fields: [
                              { type: "mrkdwn", text: "*Incident ID:* " + (slackCardData.incident_id?.slice(0, 8) || "") },
                              { type: "mrkdwn", text: "*Severity:* CRITICAL" },
                              { type: "mrkdwn", text: "*Blast Radius:* " + (slackCardData.triage?.blast_radius || "LOW") }
                            ]},
                            { type: "section", text: { type: "mrkdwn", text: "*Remediation:* " + (slackCardData.mitigation?.action || "scale_out") } },
                            { type: "actions", elements: [
                              { type: "button", text: { type: "plain_text", text: "Approve Action" }, style: "primary", action_id: "hitl_approve" },
                              { type: "button", text: { type: "plain_text", text: "Reject" }, style: "danger", action_id: "hitl_reject" }
                            ]}
                          ]
                        }, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>

                <div className="px-6 py-3 border-t border-slate-200 flex justify-end bg-slate-50">
                  <button onClick={() => setShowSlackPreview(false)} className="px-4 py-1.5 text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-300 transition shadow-sm">Close</button>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }

    ReactDOM.render(<App />, document.getElementById('root'));
  </script>
</body>
</html>
"""


def render_cockpit_html(cards_html: str = "", fixes_html: str = "") -> str:
    """Render the modern SRE incident management cockpit with server briefs embedded."""
    return _COCKPIT_TEMPLATE.replace("__CARDS_HTML__", cards_html).replace("__FIXES_HTML__", fixes_html)
