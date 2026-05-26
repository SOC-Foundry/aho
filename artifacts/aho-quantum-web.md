Your instinct is good but I'd sharpen one thing first: the snapshot on the dashboard isn't the wave - it's the *collapse*. The wave is what happens to your **knowledge** of the machine in the gaps between scans. That reframe is what makes the rest of the analogy do real work instead of just being decorative.

Here's how the pieces map, walking your sequence.

**State representation.** Treat the endpoint as a state vector in a Hilbert space where each thing you monitor is a basis dimension - a cert is valid or not, a service is up or down, the SSH private key is absent or present, a config file hashes to baseline or it doesn't. Each check is effectively a qubit-like observable. The full machine state is the tensor product of all of them. Your "compliance Hamiltonian" H is then a weighted sum of these check operators, where the weights encode criticality (an exposed private key dominates a stale cert).

**The scan as measurement.** Running your monitoring pass is the measurement. It collapses your *epistemic* state to a definite eigenstate - you now know, for that instant, exactly where the machine sits. There's even a faint but genuine back-action: a scan that stats files touches atime, an agent under load perturbs the very performance you might also be measuring. Most security checks are too gentle for that to matter, but it's not purely metaphorical.

**The score as an expectation value.** This is where it stops being a metaphor and becomes useful. Your posture score is ⟨ψ|H|ψ⟩ - the expectation value of the compliance operator. But the same formalism hands you the *variance*, ⟨H²⟩ − ⟨H⟩², for free. That means your dashboard can show a score *and an error bar*, which is something a naive weighted-sum scorecard can't express.

**Be honest about what kind of uncertainty this is.** What you're modeling is *epistemic*, not ontological. The endpoint genuinely has a definite state; you just don't know it between scans. So your "superposition" is really a Bayesian probability distribution wearing quantum notation. That's fine - the math still applies cleanly - but it means the parts of QM that are *uniquely* quantum won't transfer. There's no interference, because compliance probabilities are real and non-negative; you have no source of negative amplitude that could cancel. And what looks like entanglement across machines - two endpoints flipping together because they share a CA or a config-management source - is classical common-cause correlation, not Bell-type entanglement. The correlated-subsystem math is still handy for blast-radius reasoning; just don't claim it's spooky.

**Decoherence is the part that genuinely fits - and it's the payoff.** A freshly provisioned machine is a "pure," precisely known state. Left alone, environmental interaction (users, updates, drift, an attacker) pushes it toward a maximally mixed state - maximum uncertainty about its posture. Re-imaging or re-baselining is state re-preparation. Concretely: give each check a coherence time Tᵢ - how long a measurement stays trustworthy. "SSH key absent" decoheres slowly (very stable). "Process X running" decoheres in minutes. After a scan at time tᵢ that returned compliant, the probability the check is *still* compliant now is roughly

  pᵢ(t) = cᵢ + (1 − cᵢ)·e^(−(t − tᵢ)/Tᵢ)

where cᵢ is the equilibrium base rate it relaxes toward. Then your live score is Σ wᵢ pᵢ(t) and, for independent checks, variance Σ wᵢ² pᵢ(1 − pᵢ). The score now *decays toward maximum entropy between scans and snaps back tight at each measurement* - which is exactly the wave behavior you were reaching for.

**Density matrix for the fleet.** When you aggregate across many endpoints, the right object isn't a single state vector but a density matrix ρ - an ensemble. Diagonal entries are the classical probabilities of each posture configuration; fleet-wide posture is just a mixed state. And if you ever have checks that genuinely can't be measured simultaneously - say, one that requires taking a service offline to inspect its config-at-rest, so you can't know "service running" and "config X" at the same instant - those are non-commuting observables, and that's a real scheduling constraint, not a contrivance.

The shippable version of all this in your HTML dashboard: a posture score line with an uncertainty band that widens between scans and pinches at each measurement, plus per-check coherence times that make staleness a first-class, principled input rather than an afterthought. Want me to build that as a working artifact?

Here it is - a live, self-contained dashboard. Open it in a browser; it runs a simulated tsp3-cos endpoint with ten realistic observables.
Each concept from our discussion is wired in directly. The score is the expectation value ⟨H⟩ = Σwᵢpᵢ/Σwᵢ, shown with its ±σ band. Every observable decoheres independently between scans by p(t) = c + (m−c)·e^(−Δt/τ) - fast checks like unauthorized-listener detection (τ = 30s) age quickly, slow ones like LUKS encryption (τ = 900s) barely move. The scope draws the wave packet: the cyan envelope spreads as knowledge ages and pinches to a node at every measurement, since right after a scan every pᵢ ∈ {0,1} and the variance is exactly zero.
The thing worth playing with: hit INJECT DRIFT, then watch. ⟨H⟩ stays flat and the band keeps widening - because you don't know anything broke yet. The faint violet line is the hidden ground truth; a good monitoring cadence keeps it inside your uncertainty band. Run the cadence slider up to 90s and you'll see the truth wander outside the band - that's the flying-blind regime made visible. Then hit RUN SCAN and everything collapses back.
Two natural extensions if you want them: a density-matrix view for a whole fleet of endpoints, or wiring the model to real telemetry where each check's τ is fit from its observed flip rate rather than hand-set.


```
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Quantum Posture Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=Spline+Sans+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
:root{
  --bg:#070a10;
  --bg2:#0b0f17;
  --panel:#0e131d;
  --panel2:#121826;
  --line:#1c2533;
  --line2:#27313f;
  --grid:rgba(120,150,180,0.07);
  --txt:#e6edf3;
  --dim:#697585;
  --dim2:#48525f;
  --teal:#39e6cf;
  --teal-d:#1f9c8e;
  --amber:#f4b145;
  --red:#ff5c6c;
  --violet:#9d8cff;
  --green:#5fe08a;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{height:100%;}
body{
  background:
    radial-gradient(900px 600px at 12% -10%, rgba(57,230,207,0.06), transparent 60%),
    radial-gradient(800px 500px at 100% 0%, rgba(157,140,255,0.05), transparent 55%),
    var(--bg);
  color:var(--txt);
  font-family:'Spline Sans Mono', ui-monospace, monospace;
  font-size:13px;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
  padding:22px;
  overflow-x:hidden;
}
/* scanline + grain atmosphere */
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:999;
  background:repeating-linear-gradient(0deg, rgba(255,255,255,0.018) 0 1px, transparent 1px 3px);
  mix-blend-mode:overlay;
}
body::after{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:998;
  background:radial-gradient(120% 120% at 50% 40%, transparent 55%, rgba(0,0,0,0.55));
}
.wrap{max-width:1240px;margin:0 auto;}

/* ---- header ---- */
header{
  display:flex;align-items:flex-end;justify-content:space-between;
  gap:18px;flex-wrap:wrap;
  border-bottom:1px solid var(--line);
  padding-bottom:16px;margin-bottom:18px;
  animation:fadeUp .5s ease both;
}
.brand h1{
  font-family:'Chakra Petch',sans-serif;
  font-weight:700;font-size:24px;letter-spacing:.04em;
  display:flex;align-items:center;gap:11px;
}
.brand h1 .glyph{
  color:var(--teal);text-shadow:0 0 16px rgba(57,230,207,.6);
  font-size:26px;
}
.brand p{color:var(--dim);font-size:11.5px;margin-top:3px;letter-spacing:.02em;}
.endpoint{
  text-align:right;font-size:11px;color:var(--dim);
}
.endpoint .host{
  color:var(--teal);font-weight:600;font-size:13px;letter-spacing:.04em;
  display:inline-flex;align-items:center;gap:7px;
}
.endpoint .host::before{
  content:"";width:7px;height:7px;border-radius:50%;
  background:var(--teal);box-shadow:0 0 8px var(--teal);
  animation:pulse 2.4s infinite;
}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}

/* ---- layout ---- */
.grid{display:grid;grid-template-columns:1fr 320px;gap:16px;}
@media(max-width:880px){.grid{grid-template-columns:1fr;}}
.col{display:flex;flex-direction:column;gap:16px;}

.panel{
  background:linear-gradient(180deg,var(--panel),var(--bg2));
  border:1px solid var(--line);
  border-radius:10px;
  animation:fadeUp .55s ease both;
}
.panel.d1{animation-delay:.06s}
.panel.d2{animation-delay:.12s}
.panel.d3{animation-delay:.18s}
.panel.d4{animation-delay:.24s}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.phead{
  display:flex;align-items:center;justify-content:space-between;
  padding:11px 15px;border-bottom:1px solid var(--line);
}
.phead .t{
  font-family:'Chakra Petch',sans-serif;font-weight:600;
  font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);
}
.phead .eq{font-size:11px;color:var(--dim2);}
.pbody{padding:15px;}

/* ---- hero score ---- */
.hero{display:flex;align-items:stretch;gap:0;flex-wrap:wrap;}
.hero .main{
  flex:1;min-width:240px;padding:18px 20px;
  display:flex;flex-direction:column;justify-content:center;
}
.hero .label{
  font-size:10.5px;letter-spacing:.16em;color:var(--dim);text-transform:uppercase;
}
.hero .score{
  font-family:'Chakra Petch',sans-serif;font-weight:700;
  font-size:62px;line-height:1;letter-spacing:-.01em;
  margin-top:4px;display:flex;align-items:baseline;gap:12px;
}
.hero .score #estVal{
  color:var(--teal);text-shadow:0 0 26px rgba(57,230,207,.45);
  transition:color .4s;
}
.hero .score .pm{
  font-family:'Spline Sans Mono',monospace;font-weight:500;
  font-size:22px;color:var(--amber);
}
.hero .stateline{
  margin-top:8px;font-size:11.5px;letter-spacing:.05em;
  display:flex;align-items:center;gap:9px;
}
.hero .dot{width:8px;height:8px;border-radius:50%;background:var(--teal);
  box-shadow:0 0 9px currentColor;color:var(--teal);}
.hero .stats{
  width:230px;border-left:1px solid var(--line);
  display:grid;grid-template-rows:1fr 1fr 1fr;
}
@media(max-width:560px){.hero .stats{width:100%;border-left:none;border-top:1px solid var(--line);}}
.stat{
  padding:10px 16px;display:flex;justify-content:space-between;align-items:center;
  border-bottom:1px solid var(--line);
}
.stat:last-child{border-bottom:none;}
.stat .k{font-size:10.5px;color:var(--dim);letter-spacing:.07em;}
.stat .v{font-size:15px;font-weight:600;}
.v.teal{color:var(--teal)}.v.amber{color:var(--amber)}.v.violet{color:var(--violet)}

/* ---- scope ---- */
.scopewrap{position:relative;}
#scope{display:block;width:100%;height:280px;border-radius:6px;}
.flash{
  position:absolute;inset:0;background:rgba(255,255,255,.9);
  opacity:0;pointer-events:none;border-radius:6px;
  mix-blend-mode:overlay;
}
.flash.go{animation:flash .5s ease;}
@keyframes flash{0%{opacity:.32}100%{opacity:0}}
.legend{
  display:flex;gap:16px;flex-wrap:wrap;margin-top:11px;
  font-size:10.5px;color:var(--dim);
}
.legend span{display:flex;align-items:center;gap:6px;}
.swatch{width:16px;height:3px;border-radius:2px;}
.swatch.band{height:9px;background:rgba(57,230,207,.22);border:1px solid rgba(57,230,207,.45);}
.swatch.est{background:var(--teal);box-shadow:0 0 6px var(--teal);}
.swatch.truth{background:var(--violet);height:0;border-top:2px dotted var(--violet);}
.swatch.scan{width:2px;height:13px;background:var(--dim);}

/* ---- controls ---- */
.controls{display:flex;flex-direction:column;gap:14px;}
.btnrow{display:flex;gap:9px;flex-wrap:wrap;}
button{
  font-family:'Spline Sans Mono',monospace;font-size:11.5px;font-weight:600;
  letter-spacing:.04em;cursor:pointer;color:var(--txt);
  background:var(--panel2);border:1px solid var(--line);
  padding:9px 13px;border-radius:7px;transition:.16s;
  display:flex;align-items:center;gap:7px;
}
button:hover{border-color:var(--teal-d);color:#fff;transform:translateY(-1px);}
button:active{transform:translateY(0);}
button.primary{
  background:linear-gradient(180deg,#1d6f66,#13524b);
  border-color:var(--teal-d);color:#eafffb;
}
button.primary:hover{box-shadow:0 0 18px rgba(57,230,207,.35);}
button.warn:hover{border-color:var(--amber);}
.slider{display:flex;flex-direction:column;gap:5px;}
.slider .lab{
  display:flex;justify-content:space-between;font-size:10.5px;color:var(--dim);
  letter-spacing:.05em;
}
.slider .lab b{color:var(--teal);font-weight:600;}
input[type=range]{
  -webkit-appearance:none;appearance:none;height:4px;border-radius:3px;
  background:var(--line);outline:none;
}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:15px;height:15px;border-radius:50%;
  background:var(--teal);cursor:pointer;box-shadow:0 0 8px rgba(57,230,207,.6);
}
input[type=range]::-moz-range-thumb{
  width:15px;height:15px;border:none;border-radius:50%;
  background:var(--teal);cursor:pointer;
}

/* ---- observables ---- */
.obs-list{display:flex;flex-direction:column;}
.obs{
  padding:10px 15px;border-bottom:1px solid var(--line);
  border-left:2px solid transparent;transition:.2s;
}
.obs:last-child{border-bottom:none;}
.obs.alarm{
  border-left-color:var(--red);
  background:linear-gradient(90deg,rgba(255,92,108,.07),transparent 60%);
}
.obs-top{display:flex;align-items:center;gap:9px;}
.obs .sdot{width:8px;height:8px;border-radius:50%;flex:none;}
.obs .nm{font-size:11.5px;flex:1;color:var(--txt);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.obs .wt{
  font-size:9.5px;color:var(--dim);background:var(--panel2);
  border:1px solid var(--line);border-radius:4px;padding:1px 5px;letter-spacing:.03em;
}
.obs .pv{font-size:11px;font-weight:600;width:42px;text-align:right;}
.bar{
  position:relative;height:7px;border-radius:4px;background:var(--line);
  margin-top:7px;overflow:hidden;
}
.bar .fill{height:100%;border-radius:4px;transition:width .25s,background .3s;}
.bar .ctick{
  position:absolute;top:-2px;width:2px;height:11px;background:var(--dim);
  opacity:.7;
}
.obs-meta{
  display:flex;justify-content:space-between;margin-top:5px;
  font-size:9.5px;color:var(--dim2);letter-spacing:.03em;
}
.decay{
  height:3px;border-radius:2px;background:var(--line);margin-top:4px;overflow:hidden;
}
.decay .dfill{height:100%;background:var(--amber);transition:width .25s;opacity:.8;}

/* ---- footer ---- */
.note{
  margin-top:16px;padding:14px 16px;border:1px dashed var(--line);
  border-radius:9px;color:var(--dim);font-size:11px;line-height:1.7;
  animation:fadeUp .6s ease both;animation-delay:.3s;
}
.note b{color:var(--teal);font-weight:600;}
.note .f{color:var(--amber);}
.note code{color:var(--violet);font-size:11px;}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="brand">
      <h1><span class="glyph">&#9682;</span> QUANTUM POSTURE MONITOR</h1>
      <p>endpoint compliance modeled as an open quantum system &mdash; measurement, decoherence, collapse</p>
    </div>
    <div class="endpoint">
      <div class="host">tsp3-cos</div>
      <div>detection-surface &middot; 10 observables</div>
    </div>
  </header>

  <!-- HERO -->
  <div class="panel d1">
    <div class="hero">
      <div class="main">
        <div class="label">Posture Expectation &mdash; &lang;H&rang;</div>
        <div class="score">
          <span id="estVal">--</span>
          <span class="pm">&plusmn;<span id="sigVal">--</span></span>
        </div>
        <div class="stateline">
          <span class="dot" id="stateDot"></span>
          <span id="stateTxt">initialising&hellip;</span>
        </div>
      </div>
      <div class="stats">
        <div class="stat"><span class="k">UNCERTAINTY &sigma;</span><span class="v amber" id="sStat">--</span></div>
        <div class="stat"><span class="k">SINCE MEASUREMENT</span><span class="v teal" id="dtStat">--</span></div>
        <div class="stat"><span class="k">STATE COHERENCE</span><span class="v" id="cohStat">--</span></div>
      </div>
    </div>
  </div>

  <div class="grid">
    <!-- LEFT -->
    <div class="col">
      <!-- SCOPE -->
      <div class="panel d2">
        <div class="phead">
          <span class="t">Posture Wavefunction &mdash; &lang;H&rang;(t)</span>
          <span class="eq" id="nextScan">next measurement &mdash;</span>
        </div>
        <div class="pbody">
          <div class="scopewrap">
            <canvas id="scope"></canvas>
            <div class="flash" id="flash"></div>
          </div>
          <div class="legend">
            <span><span class="swatch est"></span> &lang;H&rang; estimate</span>
            <span><span class="swatch band"></span> &plusmn;&sigma; uncertainty (wave packet)</span>
            <span><span class="swatch truth"></span> hidden ground truth</span>
            <span><span class="swatch scan"></span> measurement / collapse</span>
          </div>
        </div>
      </div>

      <!-- CONTROLS -->
      <div class="panel d3">
        <div class="phead"><span class="t">Measurement Control</span></div>
        <div class="pbody controls">
          <div class="btnrow">
            <button class="primary" id="scanBtn">&#9678; RUN SCAN</button>
            <button class="warn" id="driftBtn">&#9889; INJECT DRIFT</button>
            <button id="playBtn">&#10074;&#10074; PAUSE</button>
            <button id="resetBtn">&#8635; RESET</button>
          </div>
          <div class="slider">
            <div class="lab"><span>SCAN CADENCE</span><b id="cadLab">25 s</b></div>
            <input type="range" id="cadence" min="5" max="90" step="5" value="25" />
          </div>
          <div class="slider">
            <div class="lab"><span>SIM SPEED</span><b id="spdLab">1.0&times;</b></div>
            <input type="range" id="speed" min="0.25" max="3" step="0.25" value="1" />
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT: OBSERVABLES -->
    <div class="panel d4">
      <div class="phead">
        <span class="t">Observables</span>
        <span class="eq">&Hcirc; = &Sigma; w&#7522;&middot;&Ocirc;&#7522;</span>
      </div>
      <div class="obs-list" id="obsList"></div>
    </div>
  </div>

  <div class="note">
    <b>How to read this.</b> Each scan is a <b>measurement</b> that collapses every observable to a definite
    eigenvalue (0/1) &mdash; the &plusmn;&sigma; band pinches to a node. Between scans the machine drifts and your
    <i>knowledge</i> decoheres: per-observable belief relaxes toward its base rate by
    <code class="f">p(t) = c + (m &minus; c)&middot;e^(&minus;&Delta;t/&tau;)</code>, so the band spreads into a wave packet.
    The score is the expectation value <code>&lang;H&rang; = &Sigma;w&#7522;p&#7522; / &Sigma;w&#7522;</code> and the uncertainty is
    <code>&sigma; = &radic;(&Sigma;w&#7522;&sup2;&middot;p&#7522;(1&minus;p&#7522;)) / &Sigma;w&#7522;</code>. Inject drift, then watch &mdash; &lang;H&rang; stays flat
    while the band widens, because you don&rsquo;t <i>know</i> yet. The next scan reveals it.
  </div>

</div>

<script>
"use strict";
/* ============ MODEL ============ */
// tau = coherence time (sim seconds); c = equilibrium compliance prob; w = criticality weight
const DEFS = [
  {id:"falcon",  nm:"falcon-sensor.service \u00b7 running",   w:10, tau:25,  c:0.92},
  {id:"sshkey",  nm:"ssh-private-key \u00b7 absent",          w:9,  tau:600, c:0.96},
  {id:"luks",    nm:"luks2 root volume \u00b7 encrypted",      w:8,  tau:900, c:0.98},
  {id:"firewall",nm:"ufw firewall \u00b7 enabled",            w:7,  tau:120, c:0.93},
  {id:"ports",   nm:"listening ports \u00b7 no unauthorized", w:7,  tau:30,  c:0.90},
  {id:"cert",    nm:"endpoint tls cert \u00b7 not expired",   w:6,  tau:480, c:0.90},
  {id:"sshd",    nm:"sshd_config \u00b7 baseline hash",       w:6,  tau:200, c:0.88},
  {id:"patch",   nm:"os packages \u00b7 no pending CVE fix",  w:5,  tau:300, c:0.75},
  {id:"wwrite",  nm:"/etc \u00b7 no world-writable files",    w:5,  tau:400, c:0.94},
  {id:"tailnet", nm:"tailscale \u00b7 tailnet reachable",     w:4,  tau:20,  c:0.85},
];

const STEP = 0.5;        // fixed sim step (sim seconds)
const WINDOW = 120;      // visible window (sim seconds)
const MAXPTS = WINDOW/STEP;

let checks, sim, running, history, scanTimes, lastScan, nextAuto, simAcc, lastReal;
let cadence = 25, speed = 1;

function rng(){return Math.random();}

function reset(){
  checks = DEFS.map(d=>({
    ...d,
    trueState: 1,           // hidden actual compliance (epistemic, not ontological)
    lastOutcome: 1,         // last *measured* value
    lastScanT: 0,
    holdUntil: 0,           // suppresses auto-recovery after injected drift
  }));
  sim = 0; running = true; history = []; scanTimes = [0];
  lastScan = 0; nextAuto = cadence; simAcc = 0; lastReal = performance.now();
  pushSample();
}

// belief that observable i is compliant right now
function prob(ck){
  const dt = sim - ck.lastScanT;
  return ck.c + (ck.lastOutcome - ck.c) * Math.exp(-dt / ck.tau);
}

function posture(){
  let W=0, est=0, varc=0, truth=0;
  for(const ck of checks){
    const p = prob(ck);
    W += ck.w;
    est   += ck.w  * p;
    varc  += ck.w*ck.w * p*(1-p);
    truth += ck.w  * ck.trueState;
  }
  return { est:100*est/W, sigma:100*Math.sqrt(varc)/W, truth:100*truth/W };
}

function coherence(){ // 1 = freshly measured (pure-ish), 0 = fully decohered
  let s=0; for(const ck of checks) s += Math.exp(-(sim-ck.lastScanT)/ck.tau);
  return s/checks.length;
}

function doScan(){
  for(const ck of checks){ ck.lastOutcome = ck.trueState; ck.lastScanT = sim; }
  lastScan = sim; scanTimes.push(sim);
  nextAuto = sim + cadence;
  pushSample();                       // crisp collapse node
  scanTimes = scanTimes.filter(t => t > sim - WINDOW - STEP);
  const f = document.getElementById("flash");
  f.classList.remove("go"); void f.offsetWidth; f.classList.add("go");
}

function injectDrift(){
  const live = checks.filter(c=>c.trueState===1);
  if(!live.length) return;
  const ck = live[Math.floor(rng()*live.length)];
  ck.trueState = 0;
  ck.holdUntil = sim + 22;            // stays broken long enough to be observed
}

function step(){
  sim += STEP;
  for(const ck of checks){
    if(ck.trueState===1){
      // rare spontaneous failure (scaled by volatility ~ 1/tau)
      if(rng() < 0.045*(STEP/ck.tau)*30) ck.trueState = 0;
    } else {
      if(sim >= ck.holdUntil && rng() < 0.07*STEP) ck.trueState = 1; // remediation
    }
  }
  if(sim >= nextAuto) doScan();
  pushSample();
}

function pushSample(){
  const p = posture();
  history.push({t:sim, est:p.est, sigma:p.sigma, truth:p.truth});
  if(history.length > MAXPTS+2) history.shift();
}

/* ============ RENDER ============ */
const cv = document.getElementById("scope");
const ctx = cv.getContext("2d");
let cw=0, ch=0, dpr=1;

function sizeCanvas(){
  dpr = window.devicePixelRatio || 1;
  cw = cv.clientWidth; ch = cv.clientHeight;
  cv.width = cw*dpr; cv.height = ch*dpr;
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
window.addEventListener("resize", sizeCanvas);

const PAD = {l:38,r:14,t:14,b:22};
function X(t){
  const latest = history.length ? history[history.length-1].t : sim;
  const cwArea = cw-PAD.l-PAD.r;
  return (cw-PAD.r) - (latest-t)/WINDOW*cwArea;
}
function Y(v){
  v = Math.max(0,Math.min(100,v));
  return (ch-PAD.b) - v/100*(ch-PAD.t-PAD.b);
}

function drawScope(){
  ctx.clearRect(0,0,cw,ch);
  // grid
  ctx.strokeStyle = "rgba(120,150,180,0.07)";
  ctx.fillStyle = "#48525f";
  ctx.lineWidth = 1;
  ctx.font = "10px 'Spline Sans Mono', monospace";
  for(let v=0; v<=100; v+=25){
    const y = Y(v)+.5;
    ctx.beginPath(); ctx.moveTo(PAD.l,y); ctx.lineTo(cw-PAD.r,y); ctx.stroke();
    ctx.fillText(String(v).padStart(3," "), 6, y+3);
  }
  for(let s=0; s<=WINDOW; s+=30){
    const latest = history.length ? history[history.length-1].t : sim;
    const x = X(latest-s)+.5;
    if(x<PAD.l-2) continue;
    ctx.strokeStyle = "rgba(120,150,180,0.05)";
    ctx.beginPath(); ctx.moveTo(x,PAD.t); ctx.lineTo(x,ch-PAD.b); ctx.stroke();
    ctx.fillStyle = "#48525f";
    ctx.fillText(s===0?"now":("-"+s+"s"), x-13, ch-7);
  }
  if(history.length<2) return;

  // measurement markers
  for(const t of scanTimes){
    const x = X(t);
    if(x<PAD.l||x>cw-PAD.r) continue;
    ctx.strokeStyle = "rgba(105,117,133,0.5)";
    ctx.setLineDash([3,4]);
    ctx.beginPath(); ctx.moveTo(x,PAD.t); ctx.lineTo(x,ch-PAD.b); ctx.stroke();
    ctx.setLineDash([]);
  }

  // uncertainty band (the wave packet)
  ctx.beginPath();
  history.forEach((h,i)=>{ const x=X(h.t),y=Y(h.est+h.sigma); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  for(let i=history.length-1;i>=0;i--){ const h=history[i]; ctx.lineTo(X(h.t),Y(h.est-h.sigma)); }
  ctx.closePath();
  ctx.fillStyle = "rgba(57,230,207,0.16)";
  ctx.fill();
  ctx.strokeStyle = "rgba(57,230,207,0.32)";
  ctx.lineWidth = 1;
  ctx.stroke();

  // ground truth (hidden eigenstate trajectory)
  ctx.beginPath();
  history.forEach((h,i)=>{ const x=X(h.t),y=Y(h.truth); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  ctx.strokeStyle = "rgba(157,140,255,0.85)";
  ctx.lineWidth = 1.4; ctx.setLineDash([2,3]);
  ctx.stroke(); ctx.setLineDash([]);

  // estimate line (phosphor glow)
  ctx.beginPath();
  history.forEach((h,i)=>{ const x=X(h.t),y=Y(h.est); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
  ctx.shadowColor = "rgba(57,230,207,0.9)"; ctx.shadowBlur = 9;
  ctx.strokeStyle = "#39e6cf"; ctx.lineWidth = 2;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // collapse nodes on the trace
  for(const t of scanTimes){
    const x=X(t); if(x<PAD.l||x>cw-PAD.r) continue;
    const h = history.reduce((a,b)=>Math.abs(b.t-t)<Math.abs(a.t-t)?b:a);
    ctx.beginPath(); ctx.arc(x,Y(h.est),3,0,7); ctx.fillStyle="#eafffb"; ctx.fill();
  }
}

/* observable rows */
const obsEls = {};
function buildObs(){
  const list = document.getElementById("obsList");
  list.innerHTML = "";
  for(const ck of checks){
    const row = document.createElement("div");
    row.className = "obs";
    row.innerHTML = `
      <div class="obs-top">
        <span class="sdot"></span>
        <span class="nm">${ck.nm}</span>
        <span class="wt">w ${ck.w}</span>
        <span class="pv"></span>
      </div>
      <div class="bar"><div class="fill"></div><div class="ctick"></div></div>
      <div class="decay"><div class="dfill"></div></div>
      <div class="obs-meta"><span class="tau">&tau; ${ck.tau}s</span><span class="dt"></span></div>`;
    list.appendChild(row);
    obsEls[ck.id] = {
      row, dot:row.querySelector(".sdot"), pv:row.querySelector(".pv"),
      fill:row.querySelector(".fill"), ctick:row.querySelector(".ctick"),
      dfill:row.querySelector(".dfill"), dt:row.querySelector(".dt"),
    };
  }
}
function pColor(p){ return p>=0.8 ? "var(--teal)" : p>=0.55 ? "var(--amber)" : "var(--red)"; }

function renderObs(){
  for(const ck of checks){
    const e = obsEls[ck.id];
    const p = prob(ck);
    const dt = sim - ck.lastScanT;
    const decohered = 1 - Math.exp(-dt/ck.tau);
    e.fill.style.width = (p*100).toFixed(1)+"%";
    e.fill.style.background = pColor(p);
    e.pv.textContent = (p*100).toFixed(0)+"%";
    e.pv.style.color = pColor(p);
    e.ctick.style.left = "calc("+(ck.c*100).toFixed(1)+"% - 1px)";
    e.dfill.style.width = (decohered*100).toFixed(0)+"%";
    e.dt.textContent = "\u0394 "+dt.toFixed(0)+"s";
    e.dot.style.background = ck.lastOutcome ? "var(--green)" : "var(--red)";
    e.dot.style.boxShadow = "0 0 7px "+(ck.lastOutcome?"var(--green)":"var(--red)");
    e.row.classList.toggle("alarm", ck.lastOutcome===0);
  }
}

function renderHero(){
  const p = posture(), coh = coherence();
  document.getElementById("estVal").textContent = p.est.toFixed(1);
  document.getElementById("sigVal").textContent = p.sigma.toFixed(1);
  document.getElementById("sStat").textContent = "\u00b1"+p.sigma.toFixed(2);
  document.getElementById("dtStat").textContent = (sim-lastScan).toFixed(0)+" s";
  document.getElementById("cohStat").textContent = (coh*100).toFixed(0)+"%";

  const estEl = document.getElementById("estVal");
  const dot = document.getElementById("stateDot");
  const txt = document.getElementById("stateTxt");
  let col, label;
  if(p.est>=90 && p.sigma<3){ col="var(--teal)";  label="COHERENT \u00b7 posture nominal"; }
  else if(p.est>=75){         col="var(--amber)"; label="DECOHERING \u00b7 knowledge ageing"; }
  else {                      col="var(--red)";   label="DEGRADED \u00b7 measurement needed"; }
  estEl.style.color = col; dot.style.background = col; dot.style.color = col;
  txt.textContent = label;

  const ns = document.getElementById("nextScan");
  ns.textContent = "next measurement \u2014 "+Math.max(0,(nextAuto-sim)).toFixed(0)+"s";
}

/* ============ LOOP ============ */
function frame(now){
  const realDt = Math.min((now-lastReal)/1000, 0.1);
  lastReal = now;
  if(running){
    simAcc += realDt * 4 * speed;          // 4 sim-seconds per real-second at 1x
    let guard = 0;
    while(simAcc >= STEP && guard++ < 200){ simAcc -= STEP; step(); }
  }
  drawScope(); renderObs(); renderHero();
  requestAnimationFrame(frame);
}

/* ============ CONTROLS ============ */
document.getElementById("scanBtn").onclick = doScan;
document.getElementById("driftBtn").onclick = injectDrift;
document.getElementById("resetBtn").onclick = ()=>{ reset(); buildObs(); };
document.getElementById("playBtn").onclick = (e)=>{
  running = !running;
  e.currentTarget.innerHTML = running ? "&#10074;&#10074; PAUSE" : "&#9654; PLAY";
  lastReal = performance.now();
};
document.getElementById("cadence").oninput = (e)=>{
  cadence = +e.target.value;
  document.getElementById("cadLab").textContent = cadence+" s";
  nextAuto = sim + cadence;
};
document.getElementById("speed").oninput = (e)=>{
  speed = +e.target.value;
  document.getElementById("spdLab").textContent = speed.toFixed(2).replace(/0$/,"")+"\u00d7";
};

/* ============ BOOT ============ */
reset();
buildObs();
sizeCanvas();
requestAnimationFrame(frame);
</script>
</body>
</html>
```
