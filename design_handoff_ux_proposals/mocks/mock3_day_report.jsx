// Mock 3: Day Report modal — every-day narrative summary with dungeon activity
const { useState: useS3, useEffect: useE3 } = React;

const SAMPLE_DAY = {
  day: 43,
  calendar: 'Hearthmoon 12',
  treasuryBefore: { g: 127, s: 3, c: 5 },
  treasuryAfter:  { g: 145, s: 1, c: 2 },
  treasuryDelta:  '+17.6gp',
  sections: [
    {
      title: 'Crypt of the Mad King · Depth 2',
      subtitle: 'The Silent Seven',
      kind: 'expedition',
      entries: [
        { t: 'info',    text: 'Entered Room 4. A low chant echoes from the east passage.' },
        { t: 'combat',  text: 'Encountered 3 skeletons.', detail: 'Sister Vale turns 2 undead. Pip lands the killing blow on the third. Party took 0 HP.' },
        { t: 'loot',    text: 'Found a sealed reliquary.', detail: '+12gp 4sp · +80 XP' },
        { t: 'choice',  text: 'Stairs discovered to Depth 3.', detail: '→ The party decided to retreat. Depth 2 saved.', choice: true },
      ],
    },
    {
      title: 'Keep',
      kind: 'keep',
      entries: [
        { t: 'healing', text: 'Brogg healed 3 HP at the Temple.', detail: '4 → 7 / 22' },
        { t: 'upkeep',  text: 'Daily upkeep paid.', detail: '−2gp 4sp (8 adventurers)' },
        { t: 'tavern',  text: 'Redwin (Fighter, Lv 2) joined the tavern.' },
      ],
    },
  ],
};

const DOT = {
  info: 'var(--text-muted)',
  combat: 'var(--accent-red)',
  loot: 'var(--accent-gold)',
  choice: 'var(--accent-blue)',
  healing: 'var(--accent-green)',
  upkeep: 'var(--accent-gold)',
  tavern: 'var(--accent-green)',
};

function DayReportEntry({ entry, revealed }) {
  return (
    <div style={{display:'flex', gap:10, padding:'6px 0', borderBottom:'1px solid var(--border-subtle)',
      opacity: revealed ? 1 : 0, transform: revealed ? 'translateY(0)' : 'translateY(4px)',
      transition: 'opacity .3s, transform .3s'}}>
      <div style={{width:6, height:6, borderRadius:'50%', background: DOT[entry.t] || 'var(--text-muted)', marginTop:6, flexShrink:0}} />
      <div style={{flex:1}}>
        <div style={{fontSize:12, color:'var(--text-primary)'}}>{entry.text}</div>
        {entry.detail && <div className="text-muted" style={{fontSize:11, marginTop:2, fontStyle: entry.choice ? 'italic' : 'normal', color: entry.choice ? 'var(--accent-blue)' : 'var(--text-muted)'}}>{entry.detail}</div>}
      </div>
    </div>
  );
}

function DayReportMock() {
  const [open, setOpen] = useS3(true);
  const [revealedCount, setRevealedCount] = useS3(0);
  const totalEntries = SAMPLE_DAY.sections.reduce((s, sec) => s + sec.entries.length, 0);

  useE3(() => {
    if (!open) return;
    setRevealedCount(0);
    let i = 0;
    const id = setInterval(() => {
      i++;
      setRevealedCount(i);
      if (i >= totalEntries) clearInterval(id);
    }, 250);
    return () => clearInterval(id);
  }, [open]);

  function replay() { setRevealedCount(0); setTimeout(() => setOpen(true), 10); }

  let seen = 0;

  return (
    <div className="vk-mock" style={{padding: 0, height: '100%', position:'relative', overflow:'hidden'}}>
      {/* faux dashboard backdrop */}
      <div style={{padding: 16, opacity:.35, pointerEvents:'none'}}>
        <div className="card" style={{padding:10, marginBottom:10}}>
          <div className="text-muted" style={{fontSize:10, textTransform:'uppercase'}}>Game Day</div>
          <div style={{fontSize:'1.8rem', fontWeight:700}}>{SAMPLE_DAY.day}</div>
        </div>
        <div className="card" style={{padding: 14}}>
          <h3 className="mb-2">Active Expeditions</h3>
          <div style={{fontSize:12}} className="text-muted">The Silent Seven · Depth 2 · Day 5/? </div>
        </div>
      </div>

      {open && (
        <div style={{position:'absolute', inset:0, background:'rgba(0,0,0,.75)', display:'flex',
          alignItems:'center', justifyContent:'center', padding: 20, zIndex: 10}}>
          <div className="card" style={{width:'100%', maxWidth: 560, maxHeight:'90%', overflow:'auto', padding: 0, animation:'dayIn .3s ease-out'}}>
            <div style={{padding:'12px 16px', borderBottom:'1px solid var(--border-color)', display:'flex', justifyContent:'space-between', alignItems:'center'}}>
              <div>
                <div className="text-muted" style={{fontSize:10, textTransform:'uppercase', letterSpacing:'.1em'}}>Day Report</div>
                <div style={{display:'flex', alignItems:'baseline', gap:8}}>
                  <h2 style={{fontSize:'1.4rem'}}>Day {SAMPLE_DAY.day}</h2>
                  <span className="text-muted" style={{fontSize:11}}>{SAMPLE_DAY.calendar}</span>
                </div>
              </div>
              <button onClick={replay} className="btn btn-secondary btn-sm">⟲ Replay</button>
            </div>

            <div style={{padding: 16}}>
              {SAMPLE_DAY.sections.map((sec, si) => (
                <div key={si} style={{marginBottom: 14}}>
                  <div style={{display:'flex', alignItems:'baseline', gap:8, marginBottom: 4, paddingBottom: 4, borderBottom:'1px solid var(--border-color)'}}>
                    <h3 style={{fontSize:13, color: sec.kind === 'expedition' ? 'var(--accent-blue)' : 'var(--accent-green)'}}>{sec.title}</h3>
                    {sec.subtitle && <span className="text-muted" style={{fontSize:11}}>· {sec.subtitle}</span>}
                  </div>
                  {sec.entries.map((e, ei) => {
                    const idx = seen++;
                    return <DayReportEntry key={ei} entry={e} revealed={idx < revealedCount} />;
                  })}
                </div>
              ))}

              {revealedCount >= totalEntries && (
                <div style={{marginTop:16, padding:10, background:'var(--bg-secondary)', border:'1px solid var(--border-color)', borderRadius:'var(--radius)',
                  display:'flex', justifyContent:'space-between', alignItems:'center', animation:'dayIn .3s'}}>
                  <div>
                    <div className="text-muted" style={{fontSize:10, textTransform:'uppercase', letterSpacing:'.08em'}}>Treasury</div>
                    <div style={{fontSize:13}}>
                      <span className="text-muted">127.4gp</span>
                      <span className="text-muted" style={{margin:'0 6px'}}>→</span>
                      <span className="text-gold" style={{fontWeight:700}}>145.1gp</span>
                      <span className="text-green" style={{marginLeft:8, fontSize:11}}>{SAMPLE_DAY.treasuryDelta}</span>
                    </div>
                  </div>
                  <div style={{display:'flex', gap:6}}>
                    <button className="btn btn-secondary btn-sm" onClick={() => setOpen(false)}>Dismiss</button>
                    <button className="btn btn-primary btn-sm" onClick={() => setOpen(false)}>Advance Day ▸</button>
                  </div>
                </div>
              )}

              {revealedCount < totalEntries && (
                <div style={{marginTop:10, textAlign:'center'}}>
                  <button className="btn btn-secondary btn-sm" onClick={() => setRevealedCount(totalEntries)}>Skip animation</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!open && (
        <div style={{position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center'}}>
          <button className="btn btn-primary" onClick={() => setOpen(true)}>Show Day Report</button>
        </div>
      )}

      <style>{`@keyframes dayIn { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform:none; } }`}</style>
    </div>
  );
}

window.DayReportMock = DayReportMock;
