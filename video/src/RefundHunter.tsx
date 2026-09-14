// RefundHunter — landscape (1920x1080) explainer for the AWS Agents for Humans hackathon.
//
// Same "story-scene on cream paper" language as the Agent Memo reels (paper, dot
// grid, kinetic Fraunces captions, red pen accent, grain + vignette, progress
// bar, closing lockup) but landscape and WITHOUT the roaming robot. It is fully
// self-timed: captions carry the narration, so no recorded voiceover or word-
// timing file is needed. Real product screenshots are shown as taped photos so
// the video demonstrates the working project, as the rules require.

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

const W = 1920, H = 1080;
const FPS = 30;
const CAPTION_TOP = 892;     // narration band sits in the lower third
const WORDS_PER_SEC = 3.4;

// ── easings ────────────────────────────────────────────────────────────────
const clampOpts = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const expo = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.out(Easing.exp), ...clampOpts });
const smooth = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.inOut(Easing.cubic), ...clampOpts });
const back = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { easing: Easing.out(Easing.back(1.7)), ...clampOpts });

// ── cast ─────────────────────────────────────────────────────────────────────
const SPARK_PATH = "m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z";

const ClaudeSpark: React.FC<{ x: number; y: number; size: number; p?: number; rot?: number }> =
  ({ x, y, size, p = 1, rot = 0 }) => (
    <svg viewBox="0 0 24 24" width={size} height={size} style={{
      position: 'absolute', left: x - size / 2, top: y - size / 2,
      transform: `scale(${Math.min(1, p * 1.1)}) rotate(${rot}deg)`, opacity: Math.min(1, p * 1.3),
    }}>
      <path fill={CLAUDE} d={SPARK_PATH} />
    </svg>
  );

const Person: React.FC<{ x: number; y: number; p: number; scale?: number; think?: boolean }> =
  ({ x, y, p, scale = 1, think }) => {
    const frame = useCurrentFrame();
    const bob = Math.sin(frame / 12) * 3;
    return (
      <svg width={160} height={230} style={{
        position: 'absolute', left: x - 80, top: y - 115 + bob,
        transform: `scale(${scale * Math.min(1, p * 1.15)})`, opacity: Math.min(1, p * 1.4), overflow: 'visible',
      }}>
        <line x1={70} y1={168} x2={62} y2={216} stroke={INK} strokeWidth={9} strokeLinecap="round" />
        <line x1={90} y1={168} x2={98} y2={216} stroke={INK} strokeWidth={9} strokeLinecap="round" />
        <rect x={52} y={92} width={56} height={82} rx={22} fill={INK} />
        {think ? (
          <>
            <line x1={54} y1={112} x2={40} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" />
            <line x1={106} y1={110} x2={120} y2={70} stroke={INK} strokeWidth={9} strokeLinecap="round" />
          </>
        ) : (
          <>
            <line x1={54} y1={112} x2={40} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" />
            <line x1={106} y1={112} x2={120} y2={152} stroke={INK} strokeWidth={9} strokeLinecap="round" />
          </>
        )}
        <circle cx={80} cy={56} r={30} fill={PAPER} stroke={INK} strokeWidth={5.5} />
        <circle cx={70} cy={54} r={4} fill={INK} />
        <circle cx={92} cy={54} r={4} fill={INK} />
        <path d="M 70 68 Q 80 74 92 68" stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round" />
      </svg>
    );
  };

// A real screenshot, printed and taped to the desk.
const PhotoShot: React.FC<{ src: string; x: number; y: number; w: number; rot?: number; delay?: number; label?: string }> =
  ({ src, x, y, w, rot = -3, delay = 0, label }) => {
    const frame = useCurrentFrame();
    const pop = back(frame, delay, delay + 16);
    if (pop <= 0.01) return null;
    return (
      <div style={{
        position: 'absolute', left: x - w / 2, top: y, width: w,
        background: '#fff', padding: 12, paddingBottom: label ? 44 : 12,
        boxShadow: '0 30px 60px rgba(20,20,20,0.22), 0 8px 20px rgba(20,20,20,0.12)',
        transform: `rotate(${rot}deg) scale(${Math.min(1, pop * 1.06)}) translateY(${(1 - pop) * -40}px)`,
        opacity: Math.min(1, pop * 1.3), zIndex: 22,
      }}>
        <Img src={staticFile(src)} style={{ width: '100%', display: 'block', border: `1px solid ${LINE}` }} />
        {label ? (
          <div style={{ position: 'absolute', bottom: 10, left: 0, right: 0, textAlign: 'center', fontFamily: COURIER, fontSize: 22, color: GREY }}>{label}</div>
        ) : null}
        {[{ l: -24, r: 20 }, { l: w - 60, r: -14 }].map((t, i) => (
          <div key={i} style={{
            position: 'absolute', top: -14, left: t.l, width: 96, height: 34,
            background: 'rgba(226,214,182,0.6)', transform: `rotate(${t.r}deg)`, boxShadow: '0 2px 6px rgba(20,20,20,.08)',
          }} />
        ))}
      </div>
    );
  };

const Chip: React.FC<{ x: number; y: number; text: string; p: number; tone?: 'ink' | 'red' | 'green'; size?: number }> =
  ({ x, y, text, p, tone = 'ink', size = 30 }) => {
    const c = tone === 'red' ? RED : tone === 'green' ? GREEN : INK;
    return (
      <div style={{
        position: 'absolute', left: x, top: y, transform: `translate(-50%,-50%) scale(${Math.min(1, p * 1.1)})`,
        fontFamily: COURIER, fontSize: size, color: c, whiteSpace: 'nowrap',
        border: `3px solid ${c}`, borderRadius: 12, padding: '10px 22px', background: CARD,
        boxShadow: '0 10px 22px rgba(20,20,20,0.10)', opacity: Math.min(1, p * 1.4),
      }}>{text}</div>
    );
  };

// A labelled paper card with a folded corner.
const FileCard: React.FC<{ x: number; y: number; w: number; h: number; label: string; p: number; rot?: number; tone?: 'ink' | 'claude' }> =
  ({ x, y, w, h, label, p, rot = 0, tone = 'ink' }) => {
    const c = tone === 'claude' ? CLAUDE : INK;
    return (
      <div style={{
        position: 'absolute', left: x - w / 2, top: y - h / 2 - (1 - p) * 40, width: w, height: h,
        background: CARD, border: `5px solid ${c}`, borderRadius: 14,
        transform: `rotate(${rot}deg) scale(${Math.min(1, p * 1.1)})`, opacity: Math.min(1, p * 1.4),
        boxShadow: '0 20px 40px rgba(20,20,20,0.12)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ position: 'absolute', right: -5, top: -5, width: 40, height: 40, background: PAPER, border: `5px solid ${c}`, borderRadius: '0 0 0 12px', clipPath: 'polygon(0 0, 100% 100%, 0 100%)' }} />
        <div style={{ fontFamily: FRAUNCES, fontWeight: 700, fontSize: 30, color: c, textAlign: 'center', padding: '0 14px', lineHeight: 1.1 }}>{label}</div>
      </div>
    );
  };

const Arrow: React.FC<{ x1: number; y1: number; x2: number; y2: number; p: number }> = ({ x1, y1, x2, y2, p }) => {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  const ex = x1 + dx * p, ey = y1 + dy * p;
  const ang = Math.atan2(dy, dx);
  return (
    <svg style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }} width={W} height={H}>
      <line x1={x1} y1={y1} x2={ex} y2={ey} stroke={INK} strokeWidth={5} strokeLinecap="round" />
      {p > 0.9 && (
        <path d={`M ${x2} ${y2} L ${x2 - 18 * Math.cos(ang - 0.4)} ${y2 - 18 * Math.sin(ang - 0.4)} M ${x2} ${y2} L ${x2 - 18 * Math.cos(ang + 0.4)} ${y2 - 18 * Math.sin(ang + 0.4)}`} stroke={INK} strokeWidth={5} strokeLinecap="round" fill="none" />
      )}
      <circle cx={x1 + dx * 0.5} cy={y1 + dy * 0.5 - len * 0} r={0} />
    </svg>
  );
};

// The big-moment word. At most one on screen at a time.
const SlamWord: React.FC<{ text: string; startF: number; y?: number; hold?: number; size?: number; tone?: 'ink' | 'red' | 'green' }> =
  ({ text, startF, y = 360, hold = 60, size = 190, tone = 'ink' }) => {
    const frame = useCurrentFrame();
    const p = back(frame, startF, startF + 12);
    const out = smooth(frame, startF + hold, startF + hold + 16);
    if (p <= 0.01 || out >= 1) return null;
    const c = tone === 'red' ? RED : tone === 'green' ? GREEN : INK;
    return (
      <div style={{
        position: 'absolute', left: 0, right: 0, top: y, textAlign: 'center',
        fontFamily: FRAUNCES, fontWeight: 900, fontSize: size, color: c, letterSpacing: '-0.02em',
        transform: `scale(${0.7 + 0.3 * p}) translateY(${(1 - p) * 20 + out * -30}px)`, opacity: (1 - out),
        zIndex: 30,
      }}>{text}</div>
    );
  };

// ── captions ─────────────────────────────────────────────────────────────────
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
const Caption: React.FC<{ text: string; hl?: string; size?: number; voice?: number }> = ({ text, hl = '', size = 52, voice }) => {
  const frame = useCurrentFrame();
  const words = text.split(/\s+/).filter(Boolean);
  const hlSet = new Set(hl.split(/\s+/).map(norm).filter(Boolean));
  // When a scene has a voice clip, spread the words across it (finishing a touch
  // early) so the captions track the spoken words. Otherwise fall back to a rate.
  const per = voice ? (voice * 0.9 * FPS) / Math.max(1, words.length) : FPS / WORDS_PER_SEC;
  return (
    <div style={{
      position: 'absolute', left: 140, right: 140, top: CAPTION_TOP, height: 150,
      display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'flex-start', gap: '0.28em',
      textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 700, fontSize: size, lineHeight: 1.16, color: INK, zIndex: 24,
    }}>
      {words.map((w, i) => {
        const s = i * per;
        const p = expo(frame, s, s + 10);
        return (
          <span key={i} style={{ display: 'inline-block', opacity: p, transform: `translateY(${(1 - p) * 12}px)`, color: hlSet.has(norm(w)) ? RED : INK }}>{w}</span>
        );
      })}
    </div>
  );
};

// ── scene visuals ──────────────────────────────────────────────────────────
type SceneId =
  | 'hook' | 'example' | 'chore' | 'meet' | 'flow' | 'run' | 'ask' | 'approve'
  | 'interrupt' | 'settings' | 'aws' | 'close';

const stageCenter = { x: W / 2, y: 400 };

const Visual: React.FC<{ id: SceneId }> = ({ id }) => {
  const frame = useCurrentFrame();
  const f = frame;

  switch (id) {
    case 'hook':
      return (
        <>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 130, color: INK, letterSpacing: '-0.02em', opacity: expo(f, 4, 20) }}>
            Stores owe you<span style={{ color: RED }}> money.</span>
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 320, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 44, color: GREY, opacity: expo(f, 26, 42) }}>
            Almost nobody collects it.
          </div>
          {[0, 1, 2, 3, 4].map((i) => {
            const d = 40 + i * 8;
            const drop = smooth(f, d, d + 40);
            return (
              <div key={i} style={{ position: 'absolute', left: 300 + i * 280, top: 540 + drop * 120, width: 64, height: 64, borderRadius: 32, background: GOLD_COIN, border: `4px solid ${INK}`, opacity: expo(f, d, d + 8) * (1 - smooth(f, d + 44, d + 60)), display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 34, color: INK }}>$</div>
            );
          })}
        </>
      );
    case 'example':
      return (
        <>
          <PhotoTag />
        </>
      );
    case 'chore': {
      const steps = ['notice the drop', 'find the rule', 'dig up the order #', 'write the email', 'chase the reply'];
      return (
        <>
          <Person x={300} y={430} p={expo(f, 4, 20)} scale={1.3} think />
          {steps.map((s, i) => {
            const d = 16 + i * 12;
            return <Chip key={i} x={720 + (i % 2) * 40} y={230 + i * 120} text={s} p={back(f, d, d + 14)} tone={i === 4 ? 'red' : 'ink'} size={30} />;
          })}
        </>
      );
    }
    case 'meet':
      return (
        <>
          <ClaudeSpark x={W / 2} y={300} size={150} p={back(f, 4, 22)} rot={smooth(f, 4, 60) * 20} />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 420, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 96, color: INK, opacity: expo(f, 18, 34) }}>Refund Hunter</div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 545, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY, letterSpacing: 4, opacity: expo(f, 30, 46) }}>AN AGENT THAT DOES IT FOR YOU</div>
        </>
      );
    case 'flow': {
      const cards: [string, number, 'ink' | 'claude'][] = [
        ['Your\ninbox', 210, 'ink'], ['Reader\nagent', 560, 'claude'], ['Hunter\nagent', 910, 'claude'], ['Asks\nyou', 1260, 'ink'], ['Files the\nclaim', 1610, 'ink'],
      ];
      return (
        <>
          {cards.map(([label, x, tone], i) => {
            const d = 8 + i * 14;
            return (
              <React.Fragment key={i}>
                <FileCard x={x} y={380} w={220} h={200} label={label} p={back(f, d, d + 14)} tone={tone} rot={i % 2 ? 2 : -2} />
                {i < cards.length - 1 && <Arrow x1={x + 118} y1={380} x2={cards[i + 1][1] - 118} y2={380} p={smooth(f, d + 10, d + 24)} />}
              </React.Fragment>
            );
          })}
        </>
      );
    }
    case 'run':
      return <PhotoShot src="rh/02-run.png" x={W / 2} y={70} w={1180} rot={-2} delay={4} label="one press — it read a dozen receipts and checked every store" />;
    case 'ask':
      return (
        <>
          <PhotoShot src="rh/02-run.png" x={640} y={70} w={1020} rot={-2} delay={4} label="it found four refunds" />
          <Chip x={1500} y={300} text={'"File $22?"'} p={back(f, 40, 54)} tone="red" size={40} />
          <Chip x={1500} y={430} text={'yes  /  skip'} p={back(f, 52, 66)} size={36} />
          <div style={{ position: 'absolute', left: 1330, top: 520, width: 360, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 30, color: GREY, opacity: expo(f, 66, 80) }}>it sent nothing on its own</div>
        </>
      );
    case 'approve':
      return (
        <>
          <PhotoShot src="rh/03-approve.png" x={W / 2} y={70} w={1180} rot={-2} delay={4} label="tap yes — it writes the claim with the order # and the rule, and sends it" />
          <SlamWord text="$89.99 found" startF={70} y={330} hold={48} size={150} tone="green" />
        </>
      );
    case 'interrupt':
      return (
        <>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 190, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 96, color: INK, opacity: expo(f, 4, 20) }}>It pauses. It waits.</div>
          <Chip x={W / 2 - 360} y={470} text={'agent running…'} p={back(f, 20, 34)} size={34} />
          <div style={{ position: 'absolute', left: W / 2 - 120, top: 452, fontFamily: FRAUNCES, fontWeight: 900, fontSize: 60, color: RED, opacity: expo(f, 34, 46) }}>⏸</div>
          <Chip x={W / 2 + 360} y={470} text={'your yes → resume'} p={back(f, 46, 60)} tone="green" size={34} />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 600, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY, opacity: expo(f, 60, 74) }}>a Strands interrupt — for hours or days</div>
        </>
      );
    case 'settings':
      return (
        <>
          <PhotoShot src="rh/05-settings.png" x={640} y={30} w={880} rot={-2} delay={4} />
          {['Claude or ChatGPT key', 'connect your Gmail', 'email me when it needs a yes'].map((s, i) => {
            const d = 30 + i * 16;
            return <Chip key={i} x={1470} y={260 + i * 150} text={s} p={back(f, d, d + 14)} tone={i === 2 ? 'red' : 'ink'} size={30} />;
          })}
        </>
      );
    case 'aws':
      return (
        <>
          <PhotoShot src="rh/arch.png" x={W / 2} y={120} w={1320} rot={0} delay={4} />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 760, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 30, color: GREY, letterSpacing: 2, opacity: expo(f, 40, 56) }}>STRANDS AGENTS · BEDROCK AGENTCORE · DYNAMODB · S3 · EVENTBRIDGE</div>
        </>
      );
    case 'close':
      return (
        <>
          <ClaudeSpark x={W / 2} y={250} size={110} p={back(f, 6, 24)} />
          <div style={{ position: 'absolute', left: 0, right: 0, top: 360, textAlign: 'center', fontFamily: FRAUNCES, fontWeight: 900, fontSize: 100, color: INK, opacity: expo(f, 14, 30) }}>Refund Hunter<span style={{ color: RED }}>.</span></div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 500, textAlign: 'center', fontFamily: INTER, fontWeight: 700, fontSize: 36, color: GREY, opacity: expo(f, 30, 46) }}>It collects the money you're owed — and only asks when it matters.</div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 600, textAlign: 'center', fontFamily: COURIER, fontSize: 28, color: CLAUDE, opacity: expo(f, 46, 62) }}>github.com/fakemovement/refund-hunter</div>
        </>
      );
    default:
      return null;
  }
};

const GOLD_COIN = '#E8C766';

// A crossed-out price tag for the example scene.
const PhotoTag: React.FC = () => {
  const f = useCurrentFrame();
  const pop = back(f, 4, 22);
  const cross = smooth(f, 40, 60);
  return (
    <>
      <div style={{
        position: 'absolute', left: W / 2 - 260, top: 250, width: 520, padding: '40px 30px',
        background: CARD, border: `5px solid ${INK}`, borderRadius: 18, transform: `scale(${Math.min(1, pop * 1.05)}) rotate(-3deg)`, opacity: Math.min(1, pop * 1.3),
        boxShadow: '0 24px 48px rgba(20,20,20,0.16)', textAlign: 'center',
      }}>
        <div style={{ fontFamily: INTER, fontWeight: 700, fontSize: 34, color: GREY }}>Air fryer · Target</div>
        <div style={{ position: 'relative', display: 'inline-block', marginTop: 16 }}>
          <span style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 92, color: INK }}>$129.99</span>
          <svg style={{ position: 'absolute', left: -10, top: 40, overflow: 'visible' }} width={340} height={20}>
            <line x1={0} y1={10} x2={320 * cross} y2={10} stroke={RED} strokeWidth={9} strokeLinecap="round" />
          </svg>
        </div>
        <div style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 64, color: GREEN, marginTop: 6, opacity: smooth(f, 58, 72) }}>$107.99</div>
      </div>
      <SlamWord text="you're owed $22" startF={78} y={640} hold={40} size={110} tone="red" />
    </>
  );
};

// ── the scene list ───────────────────────────────────────────────────────────
// Captions + visuals live here; durations and the voice clip come from
// rh-audio.json (one ElevenLabs take per scene), so the video always fits the
// narration exactly.
type Scene = { id: SceneId; caption: string; hl?: string; dur: number; voice: number; audio: string };
const CAPTIONS: Record<SceneId, { caption: string; hl?: string }> = {
  hook:      { caption: "Target, Costco, Amazon — they all owe refunds. Price drops, late deliveries, missed guarantees.", hl: "refunds" },
  example:   { caption: "You buy an air fryer for $129. Nine days later it drops to $108. Target's own rule says you get the $22 back.", hl: "$22 back" },
  chore:     { caption: "But you'd have to notice, look up the rule, find the order number, write the email, and chase the reply. So nobody does.", hl: "nobody" },
  meet:      { caption: "Refund Hunter is an agent that does all of it for you. It's for anyone who shops online.", hl: "agent" },
  flow:      { caption: "Every day it reads your receipts, checks each store's rules and today's prices, and when it finds money, it asks you.", hl: "asks you" },
  run:       { caption: "Here it is. One press reads a dozen receipts and checks every store. Best Buy's too late; Walmart was on time.", hl: "One press" },
  ask:       { caption: "It found four refunds worth almost $90. It sent nothing. It asks you one plain question for each.", hl: "four refunds" },
  approve:   { caption: "Tap yes, and it writes the claim with the order number and the store's rule, then sends it. Tap skip, and nothing happens.", hl: "yes skip" },
  interrupt: { caption: "That pause is the whole idea. The agent stops mid-task and waits for you, for hours or days, then picks up where it left off.", hl: "waits for you" },
  settings:  { caption: "Bring your own Claude or ChatGPT key, connect your Gmail, and it can email you the moment something needs a yes.", hl: "email you" },
  aws:       { caption: "Under the hood: two agents on the Strands SDK, running on Amazon Bedrock AgentCore, woken every morning on their own.", hl: "Strands AgentCore" },
  close:     { caption: "Refund Hunter. It collects the small money you're owed, and only talks to you when it needs a yes.", hl: "needs a yes" },
};
const SCENES: Scene[] = (rhAudio.scenes as { id: SceneId; dur: number; voice: number; audio: string }[])
  .map((a) => ({ id: a.id, dur: a.dur, voice: a.voice, audio: a.audio, ...CAPTIONS[a.id] }));

export const RH_TOTAL = rhAudio.total;

const SceneFade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  const inP = smooth(f, 0, 10);
  const outP = smooth(f, dur * FPS - 10, dur * FPS);
  return <AbsoluteFill style={{ opacity: inP * (1 - outP) }}>{children}</AbsoluteFill>;
};

export const RefundHunter: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const endF = Math.round(RH_TOTAL * fps);
  const lockupO = smooth(frame, endF - 0.5 * fps, endF - 0.2 * fps);

  // per-scene breathing zoom
  let acc = 0;
  let camScale = 1;
  const bounds: { start: number; dur: number; scene: Scene }[] = [];
  for (const s of SCENES) { bounds.push({ start: acc, dur: s.dur, scene: s }); acc += s.dur; }
  for (const b of bounds) {
    const sF = b.start * fps, eF = (b.start + b.dur) * fps;
    if (frame >= sF && frame < eF) camScale = 1 + 0.03 * smooth(frame, sF, eF);
  }

  return (
    <AbsoluteFill style={{ background: PAPER }}>
      <AbsoluteFill style={{ backgroundImage: `radial-gradient(circle, ${LINE} 2px, transparent 2px)`, backgroundSize: '62px 62px', opacity: 0.4 }} />

      {/* title ribbon */}
      <div style={{ position: 'absolute', top: 40, left: 64, fontFamily: FRAUNCES, fontWeight: 700, fontSize: 34, color: GREY, zIndex: 50 }}>
        Refund Hunter<span style={{ color: RED }}>.</span>
      </div>
      <div style={{ position: 'absolute', top: 48, right: 64, fontFamily: INTER, fontWeight: 700, fontSize: 22, color: GREY, letterSpacing: 3, zIndex: 50 }}>
        AGENTS FOR HUMANS · EVERYDAY
      </div>

      <AbsoluteFill style={{ transform: `scale(${camScale})`, transformOrigin: '960px 480px' }}>
        {bounds.map((b) => (
          <Sequence key={b.scene.id} from={Math.round(b.start * fps)} durationInFrames={Math.round(b.dur * fps) + 2} layout="none">
            <Audio src={staticFile(b.scene.audio)} />
            <SceneFade dur={b.dur}>
              <Visual id={b.scene.id} />
              <Caption text={b.scene.caption} hl={b.scene.hl} voice={b.scene.voice} />
            </SceneFade>
          </Sequence>
        ))}
      </AbsoluteFill>

      {/* closing lockup */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: lockupO, zIndex: 40, background: PAPER }}>
        <div style={{ fontFamily: FRAUNCES, fontWeight: 900, fontSize: 120, color: INK, letterSpacing: '-0.02em' }}>Refund Hunter<span style={{ color: RED }}>.</span></div>
      </AbsoluteFill>

      {/* progress bar */}
      <div style={{ position: 'absolute', top: 0, left: 0, height: 10, width: `${Math.min(100, (100 * frame) / endF)}%`, background: RED, zIndex: 60, opacity: 1 - smooth(frame, endF - 18, endF - 4) }} />

      {/* grain + vignette */}
      <AbsoluteFill style={{ zIndex: 70, pointerEvents: 'none', opacity: 0.05, mixBlendMode: 'multiply' }}>
        <svg width="100%" height="100%"><filter id="grainRH"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" /></filter><rect width="100%" height="100%" filter="url(#grainRH)" /></svg>
      </AbsoluteFill>
      <AbsoluteFill style={{ zIndex: 71, pointerEvents: 'none', background: 'radial-gradient(ellipse 92% 82% at 50% 45%, transparent 66%, rgba(20,20,20,0.08) 100%)' }} />
    </AbsoluteFill>
  );
};
