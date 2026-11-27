// The most likely game for each NBA game (the page's own eng_likely worker code): the most common final score out of
// n runs, then the run closest to every rotation player's typical line, replayed. Returns its score and box score.
//   node likely_sim.js IN.json OUT.json      IN: {R, n, games: [{id, sides: {home, away}, pl: [home, away], seed}]}
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const src = html.match(/<script type="text\/plain" id="workerSrc">([\s\S]*?)<\/script>/)[1];
const posted = [];
const ctx = { postMessage: (x) => posted.push(x), setTimeout: (f) => f(), console, Math, Float64Array, Float32Array, Int32Array, Int16Array,
              Uint8Array, Uint32Array, Array, Object, JSON, Map };
vm.createContext(ctx);
vm.runInContext(src, ctx);
const [inPath, outPath] = process.argv.slice(2);
const inp = JSON.parse(fs.readFileSync(inPath, 'utf8'));
const out = {};
inp.games.forEach((g, gi) => {
  posted.length = 0;
  const cfg = { R: g.R || inp.R, home: g.sides.home, away: g.sides.away, minutes: 48, shotClock: 24, pl: g.pl };
  ctx.onmessage({ data: { cmd: 'eng_likely', engine: 'nbaposs', cfg, n: inp.n || 50000, id: gi + 1, seed: g.seed || 4242 } });
  const w = posted.find((m) => m.kind === 'watch');
  if (!w) return;
  out[g.id] = { score: w.likely.score, mode: w.likely.mode, pHome: w.likely.pHome, maxZ: w.likely.maxZ, half: w.likely.half,
                box: w.box ? { home: w.box[0], away: w.box[1] } : null };
});
fs.writeFileSync(outPath, JSON.stringify(out));
