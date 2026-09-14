# Refund Hunter — explainer video (Remotion)

The landscape (1920x1080) YouTube explainer, in a "story-scene on
cream paper" style. Self-timed: the on-screen captions carry the narration, so
no recorded voiceover is needed. Real product screenshots (in `public/rh/`) are
shown as taped photos so the video demonstrates the working product.

`src/RefundHunter.tsx` is the whole composition (12 scenes: hook, example,
chore, meet, flow, run, ask, approve, interrupt, settings, aws, close).

It was authored inside a Remotion project. To render it, drop `RefundHunter.tsx`
into a Remotion `src/`, register it in `Root.tsx` as a 1920x1080 composition
(`durationInFrames = Math.ceil(RH_TOTAL * 30)`, fps 30), put the `public/rh/`
images in the project's `public/`, then:

    npx remotion render RefundHunter out.mp4

The finished file is `docs/Refund-Hunter-explainer.mp4`.
