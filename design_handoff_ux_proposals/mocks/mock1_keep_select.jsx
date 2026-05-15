// Mock 1: Keep Select — delete-confirm as popover instead of row-collapse
const { useState: useS1 } = React;

function KeepSelectMock() {
  const [confirmId, setConfirmId] = useS1(null);
  const [anchorRect, setAnchorRect] = useS1(null);
  const keeps = [
    { id: 1, name: "The Dragon's Rest", dungeon: 'Crypt of the Mad King', day: 42, gold: 127, buildings: 'Temple, Smithy' },
    { id: 2, name: 'Westfall Watchpost', dungeon: 'Hollow Hill', day: 18, gold: 48, buildings: 'Temple' },
    { id: 3, name: 'Vaelric Spire', dungeon: 'Shattered Choir', day: 3, gold: 0, buildings: '' },
  ];
  const openConfirm = (e, id) => {
    const r = e.currentTarget.getBoundingClientRect();
    const host = e.currentTarget.closest('.vk-mock').getBoundingClientRect();
    // Anchor popover so the arrow tip aligns with the delete button's center
    setAnchorRect({
      top: r.bottom - host.top + 8,
      right: host.right - r.right,
      buttonCenterFromRight: host.right - (r.left + r.width / 2),
    });
    setConfirmId(id);
  };
  const confirmingKeep = keeps.find(k => k.id === confirmId);
  return (
    <div className="vk-mock" style={{padding: 32, height: '100%'}}>
      <div style={{maxWidth: 500, margin: '0 auto', position: 'relative'}}>
        <div className="card" style={{textAlign: 'center'}}>
          <h1 className="mb-2">Your Keeps</h1>
          <p className="text-muted mb-3" style={{fontSize: 12}}>Signed in as <strong style={{color:'var(--text-primary)'}}>wayfarer</strong> <span className="text-muted">(sign out)</span></p>
          <div style={{display:'flex', flexDirection:'column', gap:8, textAlign:'left', marginBottom: 12}}>
            {keeps.map(k => (
              <div key={k.id} style={{display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 16px', background:'var(--bg-secondary)', border:'1px solid var(--border-color)', borderRadius:'var(--radius)'}}>
                <div>
                  <div style={{display:'flex', gap:6, alignItems:'baseline', flexWrap:'wrap'}}>
                    <span style={{fontWeight:700}}>{k.name}</span>
                    <span className="text-muted" style={{fontSize:11, fontStyle:'italic'}}>vs.</span>
                    <span className="text-green" style={{fontSize:13, fontWeight:700}}>{k.dungeon}</span>
                  </div>
                  <div className="text-muted" style={{fontSize:12, marginTop:2}}>
                    Day {k.day} · {k.gold}gp{k.buildings && ' · ' + k.buildings}
                  </div>
                </div>
                <button onClick={(e) => openConfirm(e, k.id)} style={{padding:'3px 8px', fontSize:11, background:'none', color:'var(--text-muted)', border:'1px solid var(--border-color)', borderRadius:'var(--radius)', cursor:'pointer', fontFamily:'inherit'}}>Delete</button>
              </div>
            ))}
          </div>
          <form style={{display:'flex', gap:8}} onSubmit={e => e.preventDefault()}>
            <input placeholder="New keep name (e.g. The Dragon's Rest)" style={{flex:1, padding:'6px 10px', background:'var(--bg-input)', border:'1px solid var(--border-color)', borderRadius:'var(--radius)', color:'var(--text-primary)', fontFamily:'inherit', fontSize:13}} />
            <button className="btn btn-primary">Create Keep</button>
          </form>
        </div>
        {confirmingKeep && anchorRect && (
          <React.Fragment>
            <div onClick={() => setConfirmId(null)} style={{position:'fixed', inset:0, zIndex:10}} />
            <div style={{position:'absolute', top: anchorRect.top, right: Math.max(0, anchorRect.buttonCenterFromRight - 120), zIndex:11,
              background:'#111827', border:'1px solid var(--accent-red)', borderRadius:'var(--radius)',
              boxShadow:'0 8px 24px rgba(0,0,0,.7)', padding:12, width: 260}}>
              <div style={{fontSize:12, color:'var(--text-primary)', marginBottom:4, fontWeight:600}}>
                Delete <span style={{color:'var(--accent-red)'}}>{confirmingKeep.name}</span>?
              </div>
              <div className="text-muted" style={{fontSize:11, marginBottom:10}}>
                This is permanent. All adventurers, parties, and progress in <strong style={{color:'var(--text-secondary)'}}>{confirmingKeep.name}</strong> will be lost.
              </div>
              <div style={{display:'flex', gap:6, justifyContent:'flex-end'}}>
                <button className="btn btn-secondary btn-sm" onClick={() => setConfirmId(null)}>Cancel</button>
                <button className="btn btn-danger btn-sm">Delete Forever</button>
              </div>
              <div style={{position:'absolute', top:-6, right: 120 - 5, width:10, height:10, background:'#111827', borderLeft:'1px solid var(--accent-red)', borderTop:'1px solid var(--accent-red)', transform:'rotate(45deg)'}} />
            </div>
          </React.Fragment>
        )}
      </div>
    </div>
  );
}

window.KeepSelectMock = KeepSelectMock;
