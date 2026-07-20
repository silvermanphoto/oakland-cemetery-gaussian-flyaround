# Oakland pilot verdict — three scenes to compare (2026-07-20)

This is the by-eye test that decides whether flying the extra 125-foot pass was
worth it. All three scenes below show the **exact same patch of ground** — a
west-central block of the cemetery (walled family plots, a small pyramid-roofed
mausoleum, a gravel path) — so anything that looks different between them comes
from the reconstruction, not from looking at different places.

Open all three, park the camera on the same monument in each, and judge.

## The three scenes (all unlisted, on Joel's SuperSplat account)

| What it is | Detail level | Live scene |
|---|---|---|
| **Original** — built from the 300-foot flight only | ~4.5 million points | https://superspl.at/scene/a64e0411 |
| **Combined, matched** — 300-foot + 125-foot flights, held to the same detail budget | ~5.7 million points | https://superspl.at/scene/7f977896 |
| **Combined, pushed** — same two flights, detail budget raised as high as it went | ~8.0 million points | https://superspl.at/scene/900d0d90 |

The first scene is the one already published earlier today as part of the
36-tile set. The two combined scenes are the new pilot trains.

Read the three as a ladder:
- **Original → Combined-matched** isolates the effect of the *second flight*
  alone (both trained to roughly the same amount of detail).
- **Combined-matched → Combined-pushed** isolates the effect of *throwing more
  detail at the same data*.

## How the v1 baseline was identified (so we're sure it's the same ground)

The pilots were trained on the cell the combined-solve partition calls
`tile_2_4`, whose footprint is x ∈ [−92.55, −14.46], z ∈ [59.41, 136.75] in the
shared model coordinates. The two partitions (original vs combined) number their
tiles in **opposite left-right order**, so the matching original tile is *not*
the one with the same name — it had to be found by footprint, not by label.

Evidence, three independent ways, all agreeing:

1. **Footprint match.** Running the statistics on the original tiles across that
   row of the site gives, left to right: `tile_1_4` at x[81…199],
   `tile_2_4` at x[−12…81], **`tile_3_4` at x[−95.7…−11.6]**, `tile_4_4` at
   x[−182…−96] — all at z[61…138]. Only **`tile_3_4`** fully contains the
   pilot's footprint (x[−92.55…−14.46], z[59.41…136.75]); its two neighbours
   only touch the edge. So the original tile for this ground is `tile_3_4`.
2. **Its own label agrees.** That scene is titled "Oakland tile_3_4" and its
   description reads "grid cell (2, 4) of the 36-tile set" — the same cell the
   pilots occupy.
3. **It looks like the same place.** Side by side, the original tile and both
   pilots show the identical pyramid-roofed mausoleum, the same walled plots,
   and the same path.

## How the pilots were made

- **Source:** a single alignment (RealityScan) of **both** drone flights
  together — the 300-foot smart-oblique pass and the 125-foot nadir pass —
  giving **462 photographs** covering this cell.
- **Resolution:** trained at the **full native 8192-pixel** image size, no
  downscaling (Joel's standing quality bar).
- **Trainer:** LichtFeld Studio on a **rented 48 GB cloud graphics card**
  (the cell's working set was too big for the studio's own 24 GB card at native
  size).
- **Time on the card:** the matched (12-million) train took **3 hours 15
  minutes**; the pushed (18-million) train took **3 hours 52 minutes**.
- **Fair-comparison prep:** each pilot was cropped to exactly this cell and
  centered on the origin — the same treatment the original tile already had — so
  all three open framed on the same geometry and the point counts above are the
  in-cell counts that actually matter.

## What to look at (the verdict is yours, by eye)

Give each of these the same test in all three scenes:

- **Can you read the gravestones?** Find a headstone with carved text and get
  close. Does the second flight make the lettering legible where it was mush
  before? Does pushing the detail budget sharpen it further, or just add noise?

- **How does the grass and ground look at standing height?** Drop the camera to
  about where a person walks and look across the plots. The original tends to
  smear ground texture into a soft carpet; watch whether the combined scenes
  hold real blades, gravel, and leaf litter instead.

- **Are the flat faces of the monuments solid and upright?** Look along the side
  of an obelisk, a wall, or the mausoleum. You want a clean flat surface, not a
  wavy or dented one. The extra low pass should firm up these vertical faces —
  see if it does, and whether the higher-detail train helps or hurts them.

- **How much junk is floating in the air?** Look up and around the edges for
  stray puffs, streaks, or haze hanging where nothing should be. More points can
  mean a crisper scene or it can mean more floaters — judge which way each pilot
  went.

If the second flight clearly wins on gravestone text and ground texture without
adding floaters, it earned its place in the pipeline. If the pushed 18-million
version doesn't visibly beat the matched 12-million one, the extra detail budget
isn't worth the longer train.
