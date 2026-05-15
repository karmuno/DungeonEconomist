// Shared VentureKeep styles for UX proposal mocks
const VK_CSS = `
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
.vk-mock { --bg-primary:#000; --bg-secondary:#0f1419; --bg-input:#111827; --bg-card:#1f2937;
  --border-color:#4b5563; --border-subtle:#374151;
  --accent-green:#4ade80; --accent-green-dim:#166534; --accent-green-dark:#22c55e;
  --accent-red:#ef4444; --accent-blue:#60a5fa; --accent-gold:#fbbf24; --accent-purple:#a78bfa;
  --text-primary:#f3f4f6; --text-secondary:#9ca3af; --text-muted:#6b7280;
  --radius:6px;
  font-family:'JetBrains Mono','Cascadia Code','Fira Code',Consolas,Monaco,monospace;
  color:var(--text-primary); background:var(--bg-primary); height:100%;
  font-size:13px; line-height:1.4;
}
.vk-mock *, .vk-mock *::before, .vk-mock *::after { box-sizing: border-box; }
.vk-mock h1, .vk-mock h2, .vk-mock h3 { color: var(--accent-green); margin: 0; font-weight: 700; }
.vk-mock h1 { font-size: 1.5rem; }
.vk-mock h3 { font-size: 1rem; }
.vk-mock .text-muted { color: var(--text-muted); }
.vk-mock .text-green { color: var(--accent-green); }
.vk-mock .text-gold { color: var(--accent-gold); }
.vk-mock .text-red { color: var(--accent-red); }
.vk-mock .text-blue { color: var(--accent-blue); }
.vk-mock .mb-1 { margin-bottom: 4px; }
.vk-mock .mb-2 { margin-bottom: 8px; }
.vk-mock .mb-3 { margin-bottom: 12px; }
.vk-mock .btn { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; font: inherit;
  font-size: 12px; font-weight: 600; border: 1px solid transparent; border-radius: var(--radius);
  cursor: pointer; }
.vk-mock .btn-primary { background: var(--accent-green-dark); color: #000; }
.vk-mock .btn-primary:hover { background: var(--accent-green); }
.vk-mock .btn-secondary { background: transparent; color: var(--text-secondary); border-color: var(--border-color); }
.vk-mock .btn-danger { background: var(--accent-red); color: #fff; }
.vk-mock .btn-sm { padding: 3px 10px; font-size: 11px; }
.vk-mock .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius);
  box-shadow: 0 2px 8px rgba(0,0,0,.5); padding: 14px; }
.vk-mock .badge { display: inline-flex; padding: 2px 7px; font-size: 10px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .06em; border-radius: 4px; }
.vk-mock .badge-success { background: rgba(74,222,128,.15); color: var(--accent-green); border: 1px solid rgba(74,222,128,.3); }
.vk-mock .badge-info { background: rgba(96,165,250,.15); color: var(--accent-blue); border: 1px solid rgba(96,165,250,.3); }
.vk-mock .badge-warning { background: rgba(251,191,36,.15); color: var(--accent-gold); border: 1px solid rgba(251,191,36,.3); }
.vk-mock .badge-danger { background: rgba(239,68,68,.15); color: var(--accent-red); border: 1px solid rgba(239,68,68,.3); }
`;

// Inject once
if (!document.getElementById('vk-mock-styles')) {
  const s = document.createElement('style');
  s.id = 'vk-mock-styles';
  s.textContent = VK_CSS;
  document.head.appendChild(s);
}

window.VK_CSS_LOADED = true;
