# Blender render farm — turning it on (the one thing Skychief needs from you)

**Bottom line:** the per-shot Blender render farm is fully built and staged on Skychief.
It renders the moment someone is **signed in** on Skychief's own screen. Right now
nobody is — the machine is sitting at the Windows sign-in screen. Pick one of the three
ways below to sign in (option 1 is the easiest and has no downside), tell me it's done,
and I run the rest. No other setup is needed.

---

## Why this is the only missing piece (what I measured, 2026-07-21)

Blender can only draw a gaussian splat when it has a live graphics-card window — and
Windows switches all graphics off when a program runs invisibly in the background. So
the farm has to run Blender as a normal on-screen program, inside a signed-in session.

The good news, confirmed on Skychief:

| What I checked | Result | What it means |
|---|---|---|
| Which card drives Skychief's screen | **RTX 3090, at 3840×2160, monitor attached** | A signed-in screen gives Blender the *real* 3090 — full-speed rendering, no tricks needed. |
| Is anyone signed in? | **No** — sitting at the sign-in screen | This is the only gap. Sign in and the farm works. |
| The card itself | Free and idle (0% used, 24 GB open) | Nothing is in the way. |
| Remote-desktop (RDP) alone | Gives only fake "software" graphics | A plain remote-desktop login is **not** enough by itself — see option 3 for the fix. |
| Auto sign-in | Half-configured, **not working** | The old registry switch is flipped on but has no saved password, so nothing happens at startup. Option 2 finishes it properly. |

---

## Option 1 — Sign in at the machine once  *(recommended — 1 minute, nothing to change)*

Best for the first test and any time you're near the machine. Lasts until the next
restart. Changes no settings, carries no security tradeoff.

1. At Skychief's own keyboard and screen, sign in normally (account **Joel PC Login**).
   If the screen is black, wiggle the mouse to wake it.
2. Tell me "signed in." I run the graphics check and the first render straight away.

That's the whole thing.

---

## Option 2 — Turn on automatic sign-in  *(for hands-off, survives restarts — 2 minutes)*

Do this if you want the farm to run any time, even after a reboot, with nobody present.
After this, Skychief boots straight to a signed-in desktop on the 3090.

1. On Skychief, download Microsoft's free **Autologon** tool (Sysinternals) — one small
   program, no installation.
2. Open it, enter the account name and its password, click **Enable**.
3. Restart Skychief once to confirm it boots straight to the desktop.

**Plain security note:** after this, the machine powers on to an *unlocked* desktop with
no password prompt — anyone who can physically switch it on is in. On a studio box in
your own space that's usually an acceptable trade; just know that's the deal. (Autologon
saves the password *encrypted*, not as readable text, which is why it's the right tool
rather than the old registry edit.)

**One catch to know about:** the main "Joel PC Login" account is a Microsoft account with
a PIN/passkey, and those sometimes refuse automatic sign-in. If Autologon won't stick for
it, use the local **LidargraphRDP** account instead (it's already an administrator and
auto sign-in works cleanly on local accounts) — the farm runs exactly the same under it.

---

## Option 3 — Remote in, then hand the screen to the 3090  *(fallback — away and can't restart)*

Only when you can't be at the machine and don't want to reboot. It works but is fiddly,
and it drops your remote view (expected).

1. From the Mac, Remote-Desktop to **192.168.50.109** as **LidargraphRDP**.
2. In that session run: `query session`  (note the id of your `rdp-tcp` line), then
   `tscon <that id> /dest:console`
3. Your remote window disconnects — that's correct. The session is now live on Skychief's
   real screen and the 3090.
4. Tell me it's done (I verify over SSH and run the farm).

Why the extra command: a plain remote-desktop session only offers Windows' fake remote
display, which tops out at ancient software graphics — Blender's render would come out
blank. The `tscon … /dest:console` step moves the session onto the real screen and the
3090, which is the standard, documented fix for exactly this.

---

## What runs automatically the moment a session exists

The instant you're signed in (any option above), the sequence is:

1. **Graphics check** — I run `gl_smoke.cmd`. It opens Blender for a second and reports
   which graphics chip it got. I want to see **"NVIDIA GeForce RTX 3090."** If instead it
   says "software" or "Microsoft," the session is the fake-display kind (that only happens
   via plain remote-desktop) and we apply option 3's `tscon` step.
2. **First render** — the queue is already loaded with a 3-frame test of the obelisk tile
   (tile_3_2, 4.3 million splats). `run_farm.cmd` renders it to
   `C:\blender_lane\farm\out\smoke_tile_3_2\`. This proves the whole pipeline end-to-end
   and gives us the first real numbers (render time and graphics-memory use per tile).
3. **Production** — from there each camera shot is one small text file listing the tiles
   its view crosses and the camera path; the queue renders them one at a time, unattended,
   with memory guards and per-shot crash isolation so one bad shot never stops the run.

Everything for steps 1–3 is already on Skychief at `C:\blender_lane\farm\` (mirrored in
this repo at `docs/blender_lane/farm/`). Nothing else to install or configure — just the
sign-in.

If you also want to start the queue *remotely* (from the Mac) without a double-click,
run `register_farm_task.ps1` once while signed in; after that I can trigger the whole
queue over SSH with a single command (`schtasks /Run /TN OaklandBlenderFarm`) — but it
only surfaces while a session is signed in, per everything above.
