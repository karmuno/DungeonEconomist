// Mock 2: Normalized currency with hover tooltip showing exact g/s/c split
const { useState: useS2 } = React;

function normalizeGp(g, s, c) {
  // 1gp = 10sp = 100cp (OSR convention)
  const totalCp = g * 100 + s * 10 + c;
  const gpFloat = totalCp / 100;
  if (gpFloat >= 10) return gpFloat.toFixed(0);
  if (gpFloat >= 1)  return gpFloat.toFixed(1);
  return gpFloat.toFixed(2);
}
function fullCurrency(g, s, c) {
  const parts = [];
  if (g) parts.push(g + 'gp');
  if (s) parts.push(s + 'sp');
  if (c) parts.push(c + 'cp');
  return parts.join(' ') || '0cp';
}

function Purse({ g, s, c }) {
  const [show, setShow] = useS2(false);
  return (
    <span style={{position:'relative', display:'inline-block', color:'var(--accent-gold)', cursor:'help', borderBottom:'1px dotted var(--accent-gold)'}}
      onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {normalizeGp(g, s, c)}gp
      {show && (
        <span style={{position:'absolute', bottom:'calc(100% + 6px)', right:0, zIndex:20,
          background:'#0a0a0a', border:'1px solid var(--accent-gold)', borderRadius:4, padding:'6px 10px',
          whiteSpace:'nowrap', fontSize:11, color:'var(--text-primary)', fontWeight:400, cursor:'default',
          boxShadow:'0 4px 12px rgba(0,0,0,.6)'}}>
          <div style={{color:'var(--text-muted)', fontSize:9, textTransform:'uppercase', letterSpacing:'.08em', marginBottom:3}}>Purse</div>
          <div style={{color:'var(--accent-gold)'}}>{g}gp <span className="text-muted">·</span> {s}sp <span className="text-muted">·</span> {c}cp</div>
          <div style={{position:'absolute', bottom:-5, right:12, width:8, height:8, background:'#0a0a0a', borderRight:'1px solid var(--accent-gold)', borderBottom:'1px solid var(--accent-gold)', transform:'rotate(45deg)'}} />
        </span>
      )}
    </span>
  );
}

function CurrencyMock() {
  const rows = [
    { name: 'Thorbin',   cls: 'Fighter',    lv: 3, hp: '17/20', xp: 4200, g: 47, s: 3, c: 0 },
    { name: 'Elora',     cls: 'Elf',        lv: 2, hp: '12/12', xp: 1800, g: 22, s: 0, c: 4 },
    { name: 'Brogg',     cls: 'Dwarf',      lv: 4, hp: '4/22',  xp: 8400, g: 130, s: 0, c: 5 },
    { name: 'Wisp',      cls: 'Magic-User', lv: 1, hp: '6/6',   xp: 300,  g: 0, s: 8, c: 3 },
    { name: 'Sister Vale', cls: 'Cleric',   lv: 2, hp: '11/14', xp: 2100, g: 19, s: 5, c: 0 },
    { name: 'Pip',       cls: 'Halfling',   lv: 1, hp: '5/6',   xp: 420,  g: 0, s: 0, c: 9 },
  ];
  return (
    <div className="vk-mock" style={{padding: 24, height: '100%'}}>
      <div style={{marginBottom: 12}}>
        <h1 style={{fontSize: '1.2rem'}} className="mb-1">Purse · normalized with detail on hover</h1>
        <p className="text-muted" style={{fontSize: 11}}>
          Instead of <code style={{color:'var(--accent-gold)'}}>130gp 0sp 5cp</code> wrapping awkwardly,
          show the normalized <code style={{color:'var(--accent-gold)'}}>130.1gp</code> — hover reveals the exact split.
        </p>
      </div>
      <div className="card" style={{padding: 0, overflow: 'hidden'}}>
        <table style={{width:'100%', borderCollapse:'collapse', fontSize: 12}}>
          <thead>
            <tr>
              {['Name','Class','Lv','HP','XP','Purse','Full (old)'].map(h =>
                <th key={h} style={{padding:'6px 10px', textAlign:'left', borderBottom:'1px solid var(--border-subtle)', color:'var(--accent-green)', fontSize:10, textTransform:'uppercase', letterSpacing:'.06em'}}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} style={{borderBottom:'1px solid var(--border-subtle)'}}>
                <td style={{padding:'6px 10px', fontWeight:600}}>{r.name}</td>
                <td style={{padding:'6px 10px'}} className="text-muted">{r.cls}</td>
                <td style={{padding:'6px 10px'}}>{r.lv}</td>
                <td style={{padding:'6px 10px'}}>{r.hp}</td>
                <td style={{padding:'6px 10px'}} className="text-blue">{r.xp}</td>
                <td style={{padding:'6px 10px'}}><Purse g={r.g} s={r.s} c={r.c} /></td>
                <td style={{padding:'6px 10px', color:'var(--text-muted)', fontSize:11, opacity:.5, textDecoration:'line-through'}}>{fullCurrency(r.g, r.s, r.c)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{marginTop: 12, display:'flex', gap: 16, flexWrap:'wrap'}}>
        <div className="card" style={{padding: 10, flex: 1, minWidth: 200}}>
          <div className="text-muted" style={{fontSize:10, textTransform:'uppercase', letterSpacing:'.08em'}}>Treasury</div>
          <div style={{fontSize: '1.3rem', fontWeight: 700}}><Purse g={127} s={3} c={5} /></div>
        </div>
        <div className="card" style={{padding: 10, flex: 1, minWidth: 200}}>
          <div className="text-muted" style={{fontSize:10, textTransform:'uppercase', letterSpacing:'.08em'}}>Expedition loot</div>
          <div style={{fontSize: '1.3rem', fontWeight: 700}}><Purse g={48} s={0} c={0} /></div>
        </div>
        <div className="card" style={{padding: 10, flex: 1, minWidth: 200}}>
          <div className="text-muted" style={{fontSize:10, textTransform:'uppercase', letterSpacing:'.08em'}}>Brogg's purse</div>
          <div style={{fontSize: '1.3rem', fontWeight: 700}}><Purse g={130} s={0} c={5} /></div>
        </div>
      </div>
      <p className="text-muted" style={{fontSize: 11, marginTop: 16, textAlign:'center'}}>
        Hover any amount to reveal the exact denomination breakdown.
      </p>
    </div>
  );
}

window.CurrencyMock = CurrencyMock;
