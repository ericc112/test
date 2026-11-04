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
  const cfg = { R: inp.R, home: g.sides.home, away: g.sides.away, minutes: 48, shotClock: 24, pl: g.pl };
  W.seed((inp.seed || 7000) + gi);
  const tk = W.nbaTracker(g.pl, inp.R.reb_credit);
  const H = tk.T.map((t) => t.ps.map(() => Object.fromEntries(Object.entries(BINS).map(([k, b]) => [k, new Int32Array(b)]))));
  const add = (h, k, v) => { h[k][Math.max(0, Math.min(BINS[k] - 1, Math.round(v)))]++; };
  let hw = 0, sh = 0, sa = 0;
  for (let i = 0; i < N; i++) {
    const r = W.nbaPossGame(cfg, null, null, tk);
    if (r[0] > r[1]) hw++; sh += r[0]; sa += r[1];
    tk.T.forEach((t, s) => {
      for (let j = 0; j < t.n; j++) {
        const b = j * W.NBN, c = t.cur, pts = c[b + W.NB.pts], reb = c[b + W.NB.orb] + c[b + W.NB.drb], ast = c[b + W.NB.ast], h = H[s][j];
        add(h, 'pts', pts); add(h, 'reb', reb); add(h, 'ast', ast); add(h, 'tpm', c[b + W.NB.f3m]); add(h, 'pra', pts + reb + ast);
        add(h, 'pr', pts + reb); add(h, 'pa', pts + ast); add(h, 'ra', reb + ast); add(h, 'min', c[b + W.NB.min]);
      }
    });
  }
  const players = {};
  tk.T.forEach((t, s) => t.ps.forEach((p, j) => {
    players[p.id] = { name: p.name, side: s === 0 ? 'home' : 'away', min: t.sum[j * W.NBN + W.NB.min] / N,
                      hist: Object.fromEntries(Object.entries(H[s][j]).map(([k, a]) => [k, Array.from(a)])) };
  }));
  out.games[g.id] = { p_home: hw / N, mean_home: sh / N, mean_away: sa / N, n: N, players };
});
fs.writeFileSync(outPath, JSON.stringify(out));
