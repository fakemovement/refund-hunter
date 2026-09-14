// RefundHunter — landscape (1920x1080) explainer for the AWS Agents for Humans hackathon.
//
// Same "story-scene on cream paper" language as the Agent Memo reels (paper, dot
// grid, kinetic Fraunces captions, red accent, grain + vignette, progress bar,
// closing lockup) but landscape and WITHOUT the roaming robot. A natural
// ElevenLabs voiceover (one take per scene, rh-audio.json) drives the timing,
// and the demo beats are real dashboard captures shown as a framed screen with
// a camera push-in and a moving cursor that clicks — so it reads as a walkthrough.

import React from 'react';
import {
  AbsoluteFill, Audio, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig,
} from 'remotion';
import { loadFont as loadFraunces } from '@remotion/google-fonts/Fraunces';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadCourier } from '@remotion/google-fonts/CourierPrime';
import rhAudio from './rh-audio.json';

const { fontFamily: FRAUNCES } = loadFraunces();
const { fontFamily: INTER } = loadInter();
const { fontFamily: COURIER } = loadCourier();

const PAPER = '#FAF7F2';
const CARD = '#FFFEFB';
const INK = '#141414';
const RED = '#C33C1E';
const GREY = '#8A857C';
const LINE = '#E5E0D6';
const CLAUDE = '#D97757';
const GREEN = '#3F7D4E';
const GOLD_COIN = '#E8C766';

const W = 1920, H = 1080;
const FPS = 30;
const CAPTION_TOP = 902;

const clampOpts = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const expo = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.out(Easing.exp), ...clampOpts });
const smooth = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.inOut(Easing.cubic), ...clampOpts });
const back = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.out(Easing.back(1.7)), ...clampOpts });
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

// ── cast ─────────────────────────────────────────────────────────────────────
const SPARK_PATH = "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z";
const ClaudeSpark: React.FC<{ x: number; y: number; size: number; p?: number; rot?: number }> =
  ({ x, y, size, p = 1, rot = 0 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} style={{ position: 'absolute', left: x - size / 2, top: y - size / 2, transform: `scale(${Math.min(1, p * 1.1)}) rotate(${rot}deg)`, opacity: Math.min(1, p * 1.3) }}>
      <path fill={CLAUDE} d={SPARK_PATH} />
    </svg>
  );

const Person: React.FC<{ x: number; y: number; p: number; scale?: number; think?: boolean }> =
  ({ x, y, p, scale = 1, think }) => {
    const frame = useCurrentFrame();
    const bob = Math.sin(frame / 12) * 3;
    return (
      <svg width={160} height={230} style={{ position: 'absolute', left: x - 80, top: y - 115 + bob, transform: `scale(${scale * Math.min(1, p * 1.15)})`, opacity: Math.min(1, p * 1.4), overflow: 'visible' }}>
        <line x1={70} y1={168} x2={62} y2={216} stroke={INK} strokeWidth={9} strokeLinecap="round" />
        <line x1={90} y1={168} x2={98} y2={216} stroke={INK} strokeWidth={9} strokeLinecap="round" />
        <rect x={52} y={92} width={56} height={82} rx={22} fill={INK} />
        {think ? (
          <><line x1={54} y1={112} x2={40} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" /><line x1={106} y1={110} x2={120} y2={70} stroke={INK} strokeWidth={9} strokeLinecap="round" /></>
        ) : (
          <><line x1={54} y1={112} x2={40} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" /><line x1={106} y1={112} x2={120} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" /></>
        )}
        <circle cx={80} cy={56} r={30} fill={PAPER} stroke={INK} strokeWidth={5.5} />
        <circle cx={70} cy={54} r={4} fill={INK} /><circle cx={92} cy={54} r={4} fill={INK} />
        <path d="M 70 68 Q 80 74 92 68" stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />
      </svg>
    );
  };

const Chip: React.FC<{ x: number; y: number; text: string; p: number; tone?: 'ink' | 'red' | 'green'; size?: number }> =
  ({ x, y, text, p, tone = 'ink', size = 30 }) => {
    const c = tone === 'red' ? RED : tone === 'green' ? GREEN : INK;
    return (
      <div style={{ position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) scale(${Math.min(1, p * 1.1)})`, fontFamily: COURIER, fontSize: size, color: c, whiteSpace: 'nowrap', border: `3px solid ${c}`, borderRadius: 12, padding: '10px 22px', background: CARD, boxShadow: '0 10px 22px rgba(20,20,20,0.10)', opacity: Math.min(1, p * 1.4) }}>{text}</div>
    );
  };

const FileCard: React.FC<{ x: number; y: number; w: number; h: number; label: string; p: number; rot?: number; tone?: 'ink' | 'claude' }> =
  ({ x, y, w, h, label, p, rot = 0, tone = 'ink' }) => {
    const c = tone === 'claude' ? CLAUDE : INK;
    return (
      <div style={{ position: 'absolute', left: x - w / 2, top: y - h / 2 - (1 - p) * 40, width: w, height: h, background: CARD, border: `5px solid ${c}`, borderRadius: 14, transform: `rotate(${rot}deg) scale(${Math.min(1, p * 1.1)})`, opacity: Math.min(1, p * 1.4), boxShadow: '0 20px 40px rgba(20,20,20,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ position: 'absolute', right: -5, top: -5, width: 40, height: 40, background: PAPER, border: `5px solid ${c}`, borderRadius: '0 0 0 12px', clipPath: 'polygon(0 0, 100% 100%, 0 100%)' }} />
        <div style={{ fontFamily: FRAUNCES, fontWeight: 700, fontSize: 30, color: c, textAlign: 'center', padding: '0 14px', lineHeight: 1.1, whiteSpace: 'pre-line' }}>{label}</div>
      </div>
    );
  };

const Arrow: React.FC<{ x1: number; y1: number; x2: number; y2: number; p: number }> = ({ x1, y1, x2, y2, p }) => {
  const dx = x2 - x1, dy = y2 - y1;
  const ex = x1 + dx * p, ey = y1 + dy * p;
  const ang = Math.atan2(dy, dx);
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }} width={W} height={H}>
      <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={INK} strokeWidth={5} strokeLinecap="round" />
      {p > 0.9 && <path d={`M ${x2} ${y2} L ${x2 - 18 * Math.cos(ang - 0.4)} ${y2 - 18 * Math.sin(ang - 0.4)} M ${x2} ${y2} L ${x2 - 18 * Math.cos(ang + 0.4)} ${y2 - 18 * Math.sin(ang + 0.4)}`} stroke={INK} strokeWidth={5} strokeLinecap="round" fill="none" />}
    </svg>
  );
};

const SlamWord: React.FC<{ text: string; startF: number; y?: number; hold?: number; size?: number; tone?: 'ink' | 'red' | 'green' }> =
  ({ text, startF, y = 360, hold = 60, size = 190, tone = 'ink' }) => {
    const frame = useCurrentFrame();
    const p = back(frame, startF, startF + 12);
    const out = smooth(frame, startF + hold, startF + hold + 16);
    if (p <= 0.01 || out >= 1) return null;
    const c = tone === 'red' ? RED : tone === 'green' ? GREEN : INK;
    return (
      <div style={{ position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: size, color: c, letterSpacing: '-0.02em', transform: `scale(${0.7 + 0.3 * p}) translateY(${(1 - p) * 20 + out * -30}px)`, opacity: (1 - out), zIndex: 30 }}>{text}</div>
    );
  };

// ── the framed screen + camera + cursor (the walkthrough) ────────────────────
const SHOTS: Record<string, { src: string; w: number; h: number }> = {
  run: { src: 'rh/cap-run.png', w: 1600, h: 3000 },
  final: { src: 'rh/cap-final.png', w: 1600, h: 3400 },
  settings: { src: 'rh/cap-settings.png', w: 1500, h: 1500 },
};
const BAR = 46;
const STAGE = { x: 210, y: 70, w: 1500, h: 770 };
const CONTENT = { x: STAGE.x, y: STAGE.y + BAR, w: STAGE.w, h: STAGE.h - BAR };
const CC = { x: CONTENT.x + CONTENT.w / 2, y: CONTENT.y + CONTENT.h / 2 };

type Cam = { fx: number; fy: number; z: number };
type Cursor = { fx: number; fy: number; t: number }; // waypoint at time t (s)
type Shot = { shot: keyof typeof SHOTS; from: Cam; to: Cam; cursor?: Cursor[]; clicks?: number[] };

const Pointer: React.FC<{ x: number; y: number; press: number }> = ({ x, y, press }) => (
  <svg width={44} height={52} viewBox="0 0 44 52" style={{ position: 'absolute', left: x, top: y, zIndex: 40, transform: `scale(${1 - 0.14 * press})`, transformOrigin: '6px 4px', filter: 'drop-shadow(0 3px 5px rgba(0,0,0,0.35))' }}>
    <path d="M6 3 L6 40 L15 31 L21 45 L27 42 L21 28 L34 28 Z" fill="#fff" stroke={INK} strokeWidth={2.4} strokeLinejoin="round" />
  </svg>
);

const WalkScreen: React.FC<{ cfg: Shot; dur: number }> = ({ cfg, dur }) => {
  const frame = useCurrentFrame();
  const p = smooth(frame, 0, dur * FPS);
  const img = SHOTS[cfg.shot];
  const cam: Cam = { fx: lerp(cfg.from.fx, cfg.to.fx, p), fy: lerp(cfg.from.fy, cfg.to.fy, p), z: lerp(cfg.from.z, cfg.to.z, p) };
  const scale = (CONTENT.w / img.w) * cam.z;
  const dispW = img.w * scale, dispH = img.h * scale;
  const imgLeft = CC.x - cam.fx * dispW;
  const imgTop = CC.y - cam.fy * dispH;
  const toScreen = (fx: number, fy: number) => ({ x: imgLeft + fx * dispW, y: imgTop + fy * dispH });

  // cursor position by easing between waypoints
  let cur = null as null | { x: number; y: number };
  if (cfg.cursor && cfg.cursor.length) {
    const tsec = frame / FPS;
    const wp = cfg.cursor;
    let a = wp[0], b = wp[wp.length - 1];
    for (let i = 0; i < wp.length - 1; i++) { if (tsec >= wp[i].t && tsec <= wp[i + 1].t) { a = wp[i]; b = wp[i + 1]; break; } }
    const seg = b.t > a.t ? interpolate(tsec, [a.t, b.t], [0, 1], { ...clampOpts, easing: Easing.inOut(Easing.cubic) }) : (tsec >= b.t ? 1 : 0);
    const fx = lerp(a.fx, b.fx, seg), fy = lerp(a.fy, b.fy, seg);
    cur = toScreen(fx, fy);
  }
  const appear = expo(frame, 4, 16);

  return (
    <AbsoluteFill>
      {/* screen frame */}
      <div style={{ position: 'absolute', left: STAGE.x, top: STAGE.y, width: STAGE.w, height: STAGE.h, background: '#fff', borderRadius: 18, boxShadow: '0 34px 70px rgba(20,20,20,0.22), 0 8px 20px rgba(20,20,20,0.12)', overflow: 'hidden', border: `1px solid ${LINE}`, opacity: appear, transform: `translateY(${(1 - appear) * 24}px)` }}>
        {/* browser bar */}
        <div style={{ position: 'absolute', left: 0, top: 0, width: '100%', height: BAR, background: '#F0ECE4', borderBottom: `1px solid ${LINE}`, display: 'flex', alignItems: 'center', paddingLeft: 18, gap: 9 }}>
          {['#E5695B', '#E8C766', '#7CB07C'].map((c, i) => <div key={i} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />)}
          <div style={{ marginLeft: 18, fontFamily: COURIER, fontSize: 20, color: GREY }}>refund-hunter · dashboard</div>
        </div>
        {/* content viewport */}
        <div style={{ position: 'absolute', left: 0, top: BAR, width: STAGE.w, height: STAGE.h - BAR, overflow: 'hidden' }}>
          <Img src={staticFile(img.src)} style={{ position: 'absolute', left: imgLeft - STAGE.x, top: imgTop - (STAGE.y + BAR), width: dispW, height: dispH }} />
        </div>
      </div>
      {/* cursor + click ripple, drawn above the frame */}
      {cur && (
        <>
          {(cfg.clicks ?? []).map((ct, i) => {
            const rp = smooth(frame, ct * FPS, ct * FPS + 16);
            if (rp <= 0 || rp >= 1) return null;
            return <div key={i} style={{ position: 'absolute', left: cur!.x - 6 + rp * -40, top: cur!.y - 6 + rp * -40, width: 12 + rp * 80, height: 12 + rp * 80, borderRadius: '50%', border: `3px solid ${RED}`, opacity: 1 - rp, zIndex: 39 }} />;
          })}
          <Pointer x={cur.x - 6} y={cur.y - 4} press={(cfg.clicks ?? []).reduce((acc, ct) => Math.max(acc, 1 - Math.min(1, Math.abs(frame - ct * FPS) / 6)), 0)} />
        </>
      )}
    </AbsoluteFill>
  );
};

// ── captions ─────────────────────────────────────────────────────────────────
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
const Caption: React.FC<{ text: string; hl?: string; size?: number; voice?: number }> = ({ text, hl = '', size = 50, voice }) => {
  const frame = useCurrentFrame();
  const words = text.split(/\s+/).filter(Boolean);
  const hlSet = new Set(hl.split(/\s+/).map(norm).filter(Boolean));
  const per = voice ? (voice * 0.82 * FPS) / Math.max(1, words.length) : FPS / 3.2;
  return (
    <div style={{ position: 'absolute', left: 150, right: 150, top: CAPTION_TOP, height: 150, display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'flex-start', gap: '0.28em', textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 700, fontSize: size, lineHeight: 1.16, color: INK, zIndex: 24 }}>
      {words.map((w, i) => {
        const s = i * per;
        const pp = expo(frame, s, s + 9);
        return <span key={i} style={{ display: 'inline-block', opacity: pp, transform: `translateY(${(1 - pp) * 10}px)`, color: hlSet.has(norm(w)) ? RED : INK }}>{w}</span>;
      })}
    </div>
  );
};

// ── animated (non-screenshot) scene visuals ─────────────────────────────────
type SceneId = 'hook' | 'example' | 'chore' | 'meet' | 'flow' | 'run' | 'ask' | 'approve' | 'email' | 'interrupt' | 'settings' | 'aws' | 'close';

const PhotoTag: React.FC = () => {
  const f = useCurrentFrame();
  const pop = back(f, 4, 22);
  const cross = smooth(f, 34, 52);
  return (
    <>
      <div style={{ position: 'absolute', left: W / 2 - 280, top: 250, width: 560, padding: '40px 30px', background: CARD, border: `5px solid ${INK}`, borderRadius: 18, transform: `scale(${Math.min(1, pop * 1.05)}) rotate(-3deg)`, opacity: Math.min(1, pop * 1.3), boxShadow: '0 24px 48px rgba(20,20,20,0.16)', textAlign: 'center' }}>
        <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY }}>Air fryer · Target</div>
        <div style={{ position: 'relative', display: 'inline-block', marginTop: 16 }}>
          <span style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 92, color: INK }}>$129.99</span>
          <svg style={{ position: 'absolute', left: -10, top: 40, overflow: 'visible' }} width={360} height={20}><line x1={0} y1={10} x2={340 * cross} y2={10} stroke={RED} strokeWidth={9} strokeLinecap="round" /></svg>
        </div>
        <div style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 64, color: GREEN, marginTop: 6, opacity: smooth(f, 52, 66) }}>$107.99</div>
      </div>
      <SlamWord text="you're owed $22" startF={72} y={640} hold={40} size={110} tone="red" />
    </>
  );
};

const AnimVisual: React.FC<{ id: SceneId }> = ({ id }) => {
  const f = useCurrentFrame();
  switch (id) {
    case 'hook':
      return (
        <>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 210, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 132, color: INK, letterSpacing: '-0.02em', opacity: expo(f, 4, 20) }}>Stores owe you<span style={{ color: RED }}> money.</span></div>
          {[0, 1, 2, 3, 4, 5].map((i) => { const d = 30 + i * 7; const drop = smooth(f, d, d + 44); return <div key={i} style={{ position: 'absolute', left: 260 + i * 250, top: 470 + drop * 150, width: 66, height: 66, borderRadius: 33, background: GOLD_COIN, border: `4px solid ${INK}`, opacity: expo(f, d, d + 8) * (1 - smooth(f, d + 48, d + 64)), display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 34, color: INK }}>$</div>; })}
        </>
      );
    case 'example': return <PhotoTag />;
    case 'chore': {
      const steps = ['spot the drop', 'know the rule', 'find the order #', 'write the email', 'chase the reply'];
      return (<>
        <Person x={300} y={430} p={expo(f, 4, 20)} scale={1.3} think />
        {steps.map((s, i) => { const d = 14 + i * 11; return <Chip key={i} x={760 + (i % 2) * 40} y={230 + i * 118} text={s} p={back(f, d, d + 14)} tone={i === 4 ? 'red' : 'ink'} size={30} />; })}
      </>);
    }
    case 'meet':
      return (<>
        <ClaudeSpark x={W / 2} y={300} size={150} p={back(f, 4, 22)} rot={smooth(f, 4, 60) * 20} />
        <div style={{ position: 'absolute', left: 0, right: 0, top: 420, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 100, color: INK, opacity: expo(f, 16, 32) }}>Refund Hunter</div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 555, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY, letterSpacing: 4, opacity: expo(f, 28, 44) }}>A BACKGROUND AGENT THAT DOES IT FOR YOU</div>
      </>);
    case 'flow': {
      const cards: [string, number, 'ink' | 'claude'][] = [['Your\ninbox', 210, 'ink'], ['Reader\nagent', 560, 'claude'], ['Hunter\nagent', 910, 'claude'], ['Asks\nyou', 1260, 'ink'], ['Files the\nclaim', 1610, 'ink']];
      return (<>
        {cards.map(([label, x, tone], i) => { const d = 8 + i * 13; return (
          <React.Fragment key={i}>
            <FileCard x={x} y={390} w={220} h={200} label={label} p={back(f, d, d + 14)} tone={tone} rot={i % 2 ? 2 : -2} />
            {i < cards.length - 1 && <Arrow x1={x + 118} y1={390} x2={cards[i + 1][1] - 118} y2={390} p={smooth(f, d + 10, d + 24)} />}
          </React.Fragment>); })}
      </>);
    }
    case 'interrupt':
      return (<>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 210, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 104, color: INK, opacity: expo(f, 4, 20) }}>It pauses. It waits.</div>
        <Chip x={W / 2 - 380} y={480} text={'agent running…'} p={back(f, 18, 32)} size={34} />
        <div style={{ position: 'absolute', left: W / 2 - 34, top: 452, fontFamily: FRAUNCES, fontWeight: 900, fontSize: 64, color: RED, opacity: expo(f, 32, 44) }}>⏸</div>
        <Chip x={W / 2 + 380} y={480} text={'your yes → resume'} p={back(f, 46, 60)} tone="green" size={34} />
        <div style={{ position: 'absolute', left: 0, right: 0, top: 600, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY, opacity: expo(f, 60, 74) }}>a Strands interrupt — even for days</div>
      </>);
    case 'aws':
      return (<>
        <div style={{ position: 'absolute', left: STAGE.x, top: STAGE.y, width: STAGE.w, height: STAGE.h, background: '#fff', borderRadius: 18, boxShadow: '0 30px 60px rgba(20,20,20,0.2)', overflow: 'hidden', border: `1px solid ${LINE}`, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: expo(f, 4, 18) }}>
          <Img src={staticFile('rh/arch.png')} style={{ width: '96%' }} />
        </div>
      </>);
    case 'close':
      return (<>
        <ClaudeSpark x={W / 2} y={250} size={110} p={back(f, 6, 24)} />
        <div style={{ position: 'absolute', left: 0, right: 0, top: 360, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 104, color: INK, opacity: expo(f, 14, 30) }}>Refund Hunter<span style={{ color: RED }}>.</span></div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 505, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY, opacity: expo(f, 30, 46) }}>Collects the money you're owed. Asks only when it matters.</div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 590, textAlign: 'center', fontFamily: COURIER, fontSize: 28, color: CLAUDE, opacity: expo(f, 46, 62) }}>github.com/fakemovement/refund-hunter</div>
      </>);
    default: return null;
  }
};

// close-up walkthrough config per demo scene
const SHOT_CFG: Partial<Record<SceneId, Shot>> = {
  run: { shot: 'run', from: { fx: 0.5, fy: 0.055, z: 1.02 }, to: { fx: 0.42, fy: 0.08, z: 1.14 },
    cursor: [{ fx: 0.5, fy: 0.4, t: 0 }, { fx: 0.795, fy: 0.014, t: 1.4 }, { fx: 0.795, fy: 0.014, t: 6 }], clicks: [1.7] },
  ask: { shot: 'run', from: { fx: 0.5, fy: 0.11, z: 1.25 }, to: { fx: 0.52, fy: 0.135, z: 1.5 },
    cursor: [{ fx: 0.95, fy: 0.18, t: 0 }, { fx: 0.6, fy: 0.10, t: 2.2 }, { fx: 0.6, fy: 0.10, t: 6.5 }] },
  approve: { shot: 'run', from: { fx: 0.42, fy: 0.135, z: 1.5 }, to: { fx: 0.30, fy: 0.15, z: 1.7 },
    cursor: [{ fx: 0.8, fy: 0.2, t: 0 }, { fx: 0.227, fy: 0.1505, t: 2.2 }, { fx: 0.227, fy: 0.1505, t: 4.9 }], clicks: [2.6] },
  email: { shot: 'final', from: { fx: 0.42, fy: 0.5, z: 1.25 }, to: { fx: 0.42, fy: 0.52, z: 1.42 } },
  settings: { shot: 'settings', from: { fx: 0.5, fy: 0.24, z: 1.14 }, to: { fx: 0.5, fy: 0.74, z: 1.2 },
    cursor: [{ fx: 0.62, fy: 0.24, t: 0.4 }, { fx: 0.62, fy: 0.24, t: 2.2 }, { fx: 0.30, fy: 0.62, t: 4.4 }, { fx: 0.30, fy: 0.62, t: 5.4 }] },
};

// ── scene assembly ───────────────────────────────────────────────────────────
const CAPTIONS: Record<SceneId, { caption: string; hl?: string }> = {
  hook:      { caption: "Stores owe you money all the time. Price drops, late deliveries, missed dates. And almost nobody collects it.", hl: "money" },
  example:   { caption: "Buy an air fryer for $130. A week later Target drops it to $108. Their own policy owes you the difference.", hl: "$130 $108" },
  chore:     { caption: "You'd have to spot the drop, know the rule, find the order number, write the email, and chase a reply. So most of us let it go.", hl: "let it go" },
  meet:      { caption: "Refund Hunter does that whole chore for you. A simple background agent for anyone who shops online.", hl: "for you" },
  flow:      { caption: "Once a day it reads your receipts, works out what each store owes you, and the moment it finds money, it comes to you.", hl: "comes to you" },
  run:       { caption: "One button. It reads a dozen receipts, checks every store, and finds four refunds worth $89.99.", hl: "$89.99" },
  ask:       { caption: "It hasn't sent anything. It just asks. Costco dropped $50, and you're still inside the 30-day window.", hl: "$50" },
  approve:   { caption: "Tap yes. It writes the claim with your order number and Costco's own rule, and files it.", hl: "yes" },
  email:     { caption: "Here's the real email it sent. Everything the store needs, and nothing you had to type.", hl: "real email" },
  interrupt: { caption: "That pause is the whole point. The agent waits for you, even for days, then picks up where it left off.", hl: "waits for you" },
  settings:  { caption: "Bring your own Claude or ChatGPT key, connect your Gmail, and get an email the moment something needs you.", hl: "Claude ChatGPT" },
  aws:       { caption: "Behind it: two agents on the Strands SDK, running on Amazon Bedrock, waking up on their own each morning.", hl: "Strands Bedrock" },
  close:     { caption: "That's Refund Hunter. It collects the money you're owed, and only speaks up when it needs you.", hl: "needs you" },
};

type Scene = { id: SceneId; caption: string; hl?: string; dur: number; voice: number; audio: string };
const SCENES: Scene[] = (rhAudio.scenes as { id: SceneId; dur: number; voice: number; audio: string }[])
  .map((a) => ({ id: a.id, dur: a.dur, voice: a.voice, audio: a.audio, ...CAPTIONS[a.id] }));
export const RH_TOTAL = rhAudio.total;

const SceneFade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  const inP = smooth(f, 0, 9);
  const outP = smooth(f, dur * FPS - 9, dur * FPS);
  return <AbsoluteFill style={{ opacity: inP * (1 - outP) }}>{children}</AbsoluteFill>;
};

export const RefundHunter: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const endF = Math.round(RH_TOTAL * fps);
  const lockupO = smooth(frame, endF - 0.5 * fps, endF - 0.2 * fps);

  let acc = 0;
  const bounds: { start: number; scene: Scene }[] = [];
  for (const s of SCENES) { bounds.push({ start: acc, scene: s }); acc += s.dur; }

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <AbsoluteFill style={{ backgroundImage: `radial-gradient(circle, ${LINE} 2px, transparent 2px)`, backgroundSize: '62px 62px', opacity: 0.4 }} />
      <div style={{ position: 'absolute', top: 40, left: 64, fontFamily: FRAUNCES, fontWeight: 700, fontSize: 34, color: GREY, zIndex: 50 }}>Refund Hunter<span style={{ color: RED }}>.</span></div>
      <div style={{ position: 'absolute', top: 48, right: 64, fontFamily: INTER, fontWeight: 700, fontSize: 22, color: GREY, letterSpacing: 3, zIndex: 50 }}>AGENTS FOR HUMANS · EVERYDAY</div>

      {bounds.map((b) => {
        const shotCfg = SHOT_CFG[b.scene.id];
        return (
          <Sequence key={b.scene.id} from={Math.round(b.start * fps)} durationInFrames={Math.round(b.scene.dur * fps) + 2} layout="none">
            <Audio src={staticFile(b.scene.audio)} />
            <SceneFade dur={b.scene.dur}>
              {shotCfg ? <WalkScreen cfg={shotCfg} dur={b.scene.dur} /> : <AnimVisual id={b.scene.id} />}
              <Caption text={b.scene.caption} hl={b.scene.hl} voice={b.scene.voice} />
            </SceneFade>
          </Sequence>
        );
      })}

      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: lockupO, zIndex: 40, background: PAPER }}>
        <div style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 120, color: INK, letterSpacing: '-0.02em' }}>Refund Hunter<span style={{ color: RED }}>.</span></div>
      </AbsoluteFill>

      <div style={{ position: 'absolute', top: 0, left: 0, height: 10, width: `${Math.min(100, (100 * frame) / endF)}%`, background: RED, zIndex: 60, opacity: 1 - smooth(frame, endF - 18, endF - 4) }} />
      <AbsoluteFill style={{ zIndex: 70, pointerEvents: 'none', opacity: 0.05, mixBlendMode: 'multiply' }}>
        <svg width="100%" height="100%"><filter id="grainRH"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" /></filter><rect width="100%" height="100%" filter="url(#grainRH)" /></svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 71, pointerEvents: 'none', background: 'radial-gradient(ellipse 92% 82% at 50% 45%, transparent 66%, rgba(20,20,20,0.08) 100%)' }} />
    </AbsoluteFill>
  );
};
