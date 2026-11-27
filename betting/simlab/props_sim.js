// Player-prop distributions from the Sim Lab NBA engine (the same worker code the page runs), for edge/nba_pp.py.
//   node props_sim.js IN.json OUT.json
// IN:  {R, n, seed, games: [{id, home, away, sides: {home, away}, pl: [home profile, away profile]}]}
// OUT: {games: {id: {p_home, mean_home, mean_away, n, players: {pid: {name, side, min, hist: {stat: counts}}}}}}
// Stats: pts reb ast tpm pra pr pa ra (counts by whole value) and min (rounded minutes).
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const src = html.match(/<script type="text\/plain" id="workerSrc">([\s\S]*?)<\/script>/)[1];
const ctx = { postMessage: () => {}, setTimeout: (f) => f(), console, Math, Float64Array, Int32Array, Uint32Array, Uint8Array, Array, Object, JSON };
vm.createContext(ctx);
vm.runInContext(src + '\n;this.__x = { seed, nbaPossGame, nbaTracker, NB, NBN };', ctx);
const W = ctx.__x;

const [inPath, outPath] = process.argv.slice(2);
const inp = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const N = inp.n || 50000;
const BINS = { pts: 90, reb: 35, ast: 25, tpm: 15, pra: 120, pr: 105, pa: 105, ra: 50, min: 54 };
const out = { n: N, games: {} };
inp.games.forEach((g, gi) => {
  const R = g.R || inp.R;                       // a backtest day carries its own calibration
  const cfg = { R, home: g.sides.home, away: g.sides.away, minutes: 48, shotClock: 24, pl: g.pl };
  W.seed((g.seed || inp.seed || 7000) + gi);
  const tk = W.nbaTracker(g.pl, R.reb_credit);
  const H = tk.T.map((t) => t.ps.map(() => Object.fromEntries(Object.entries(BINS).map(([k, b]) => [k, new Int32Array(b)]))));
  const add = (h, k, v) => { h[k][Math.max(0, Math.min(BINS[k] - 1, Math.round(v)))]++; };
  // cross-moments for the joint distribution check (points x assists, points x rebounds)
  const X = tk.T.map((t) => t.ps.map(() => ({ pa: 0, pr: 0, p2: 0, a2: 0, r2: 0 })));
  let hw = 0, sh = 0, sa = 0, poss = 0;
  // same-game entries: count runs where every listed leg hits (a push counts as a miss)
  const legs = (g.legs || []).map((l) => { let s = -1, j = -1; tk.T.forEach((t, si) => t.ps.forEach((p, pj) => { if (p.id === l.pid) { s = si; j = pj; } })); return { ...l, s, j }; });
  let allHit = 0; const legHit = legs.map(() => 0);
  const val = (c, b, st) => { const pts = c[b + W.NB.pts], reb = c[b + W.NB.orb] + c[b + W.NB.drb], ast = c[b + W.NB.ast];
    return { pts, reb, ast, tpm: c[b + W.NB.f3m], pra: pts + reb + ast, pr: pts + reb, pa: pts + ast, ra: reb + ast }[st]; };
  for (let i = 0; i < N; i++) {
    const r = W.nbaPossGame(cfg, null, null, tk);
    if (r[0] > r[1]) hw++; sh += r[0]; sa += r[1]; poss += r[3] || 0;
    if (legs.length) {
      let all = true;
      legs.forEach((l, k) => { if (l.s < 0) { all = false; return; } const v = val(tk.T[l.s].cur, l.j * W.NBN, l.stat);
        const hit = l.side === 'over' ? v > l.line : v < l.line; if (hit) legHit[k]++; else all = false; });
      if (all) allHit++;
    }
    tk.T.forEach((t, s) => {
      for (let j = 0; j < t.n; j++) {
        const b = j * W.NBN, c = t.cur, pts = c[b + W.NB.pts], reb = c[b + W.NB.orb] + c[b + W.NB.drb], ast = c[b + W.NB.ast], h = H[s][j];
        add(h, 'pts', pts); add(h, 'reb', reb); add(h, 'ast', ast); add(h, 'tpm', c[b + W.NB.f3m]); add(h, 'pra', pts + reb + ast);
        add(h, 'pr', pts + reb); add(h, 'pa', pts + ast); add(h, 'ra', reb + ast); add(h, 'min', c[b + W.NB.min]);
        const x = X[s][j]; x.pa += pts * ast; x.pr += pts * reb; x.p2 += pts * pts; x.a2 += ast * ast; x.r2 += reb * reb;
      }
    });
  }
  const players = {};
  const K = Object.keys(W.NB);
  tk.T.forEach((t, s) => t.ps.forEach((p, j) => {
    const m = Object.fromEntries(K.map((k) => [k, t.sum[j * W.NBN + W.NB[k]] / N]));
    m.reb = m.orb + m.drb;
    const x = X[s][j], v = (s2, mu) => s2 / N - mu * mu, ma = m.ast, mp = m.pts, mr = m.reb;
    const corr = (sxy, mx, my, sx2, sy2) => { const d = Math.sqrt(Math.max(v(sx2, mx), 1e-9) * Math.max(v(sy2, my), 1e-9)); return (sxy / N - mx * my) / d; };
    players[p.id] = { name: p.name, side: s === 0 ? 'home' : 'away', min: m.min, mean: m, proj_min: p.min,
                      corr_pa: corr(x.pa, mp, ma, x.p2, x.a2), corr_pr: corr(x.pr, mp, mr, x.p2, x.r2),
                      hist: Object.fromEntries(Object.entries(H[s][j]).map(([k, a]) => [k, Array.from(a)])) };
  }));
  out.games[g.id] = { p_home: hw / N, mean_home: sh / N, mean_away: sa / N, poss: poss / N, n: N, players,
                      joint: legs.length ? { all: allHit / N, legs: legHit.map((x) => x / N), found: legs.map((l) => l.s >= 0) } : null };
});
fs.writeFileSync(outPath, JSON.stringify(out));
