# Model research: replacing the heuristic analyser

Status: **research / decision record**. No code depends on this yet.

## Problem

The current backend ([example.py](../backend/example.py),
[improved_segmentation.py](../backend/improved_segmentation.py)) segments songs
with hand-built MIR features: chroma, MFCC, spectral centroid, a novelty
function, then heuristic labelling. Measured on synthetic material it reached
roughly 58% boundary accuracy and 68% label accuracy — good enough to prove the
idea, not good enough to be useful on real music.

An earlier exploration of classical alternatives (MSAF's Foote, C-NMF, 2D-FMC
algorithms) is recorded in
[SEGMENTATION_ACCURACY_DISCUSSION.md](SEGMENTATION_ACCURACY_DISCUSSION.md).
Those methods are pre-deep-learning and are now clearly superseded.

## Decision

Replace the structure analyser with **SongFormer**, a supervised model that
predicts section boundaries and functional labels end to end. Keep the existing
HTTP contract so the frontend and stored `analysis.json` files are unaffected.

Add **Beat This!** for beats and downbeats, which also enables bar detection.
Treat any music LLM as an optional *description* layer, never as the source of
section timestamps.

This was validated locally on an M1 Pro before writing anything into the
backend; measured numbers and the setup traps are in [Spike results](#spike-results).

## Why not a general-purpose LLM

This was the original instinct and it is worth recording why it does not work.

The SongFormer authors benchmarked Gemini 2.5 Pro on the same task. It produces
plausible section *labels* but poor *boundaries*:

| System | Label accuracy | Boundary hit rate @0.5 s |
| --- | --- | --- |
| SongFormer | **0.807** | **0.703** |
| All-In-One | 0.740 | 0.596 |
| Gemini 2.5 Pro | 0.748 | 0.423 |

The paper attributes this to coarse temporal resolution — errors of up to two
seconds — plus formatting and alignment failures. Wall-clock time is also 10-30x
worse (30-90 s per song versus 2-4 s).

An LLM can say "this sounds like a chorus". A specialist model can say "the
chorus begins at 74.2 s". Sectionist needs the second statement to draw a
timeline, so an LLM is the wrong primary engine.

## Candidates

### Music structure (the core problem)

| Model | Year | Boundary HR@0.5s | Notes |
| --- | --- | --- | --- |
| **SongFormer** | 2026 | **0.703** | Open weights, 2-4 s/song on an L40, no beat tracking or source separation required |
| All-In-One | 2023 | 0.596 | Needs Demucs stems; beat decoding uses madmom's DBN |
| MusicFM + probe | 2024 | 0.640 | Foundation model, needs a trained head |
| SpecTNT | 2021 | ~0.560 | Superseded |
| Harmonic-CNN | 2019 | ~0.559 | Superseded |
| MSAF (classical) | 2016-2019 | n/a (MIREX metrics) | Already explored, see linked doc |

SongFormer is the clear choice: best accuracy, and crucially it analyses the raw
mix. It needs no stem separation (which is what makes All-In-One slow on a
laptop) and no beat tracking as an input, which removes two failure modes the
current code has to work around.

It emits exactly the label set the UI already uses: `intro`, `verse`,
`pre-chorus`, `chorus`, `bridge`, `inst`, `silence`, `outro`.

### Beats and downbeats (enables bar detection)

[Beat This!](https://github.com/CPJKU/beat_this) (ISMIR 2024). 20M parameters,
~8 MB for the `small0` model, ~78 MB for `final0`. State of the art *without*
madmom's Dynamic Bayesian Network post-processing, which matters because that
component is patented and licensed for non-commercial use only. Code and weights
are MIT. Runs on CPU.

### Key

[S-KEY](https://github.com/deezer/skey) (Deezer, ICASSP 2025) matches supervised
state of the art from self-supervision. Code is MIT; the shipped weights are
**non-commercial research use only**. The current librosa Krumhansl estimate
remains as the fallback.

### Chords

[BTC](https://github.com/jayg996/BTC-ISMIR19) (bi-directional transformer, ISMIR
2019) is the standard open implementation and still a reasonable baseline.
MOSS-Music can also transcribe chords, but without published benchmark numbers
yet.

### Music LLMs

| Model | Size | Licence | Fit |
| --- | --- | --- | --- |
| **MOSS-Music** (2026) | 9.1B (Qwen3-8B backbone) | Apache 2.0 | Music QA, captioning, chord/key reasoning, lyrics ASR. Needs GPU. |
| Qwen3-Omni | 30B-A3B MoE | Apache 2.0 | General audio, weaker on music-specific tasks |
| Gemini 3.1 Pro | hosted | proprietary | Not local; coarse timestamps |

MOSS-Music is the one worth trying for the commentary layer: it is Apache 2.0
and leads public music-QA benchmarks. It is not a substitute for SongFormer on
boundaries.

## Licensing

The project is open source and non-commercial, which makes the non-commercial
weights acceptable. This table is recorded so the constraint is not forgotten if
that ever changes.

| Component | Code | Weights | Usable here |
| --- | --- | --- | --- |
| SongFormer | CC-BY-4.0 | CC-BY-4.0 | yes, with attribution |
| MuQ (SongFormer encoder) | MIT | **CC-BY-NC 4.0** | yes, non-commercial only |
| MusicFM (SongFormer encoder) | MIT | MIT | yes |
| Beat This | MIT | MIT | yes |
| S-KEY | MIT | **non-commercial only** | yes, non-commercial only |
| All-In-One | MIT | MIT | yes, but madmom patent applies |
| Essentia | **AGPL-3.0** | - | avoided |

Consequence: any distribution must be non-commercial and must carry attribution
for SongFormer, MuQ and S-KEY. A future commercial build would need the
MIT-only stack (MusicFM + a self-trained head + Beat This).

## Hardware

**RTX 5090 (32 GB)** — ideal. Model fits in 3-4 GB. Note that Blackwell needs
PyTorch 2.7+ with CUDA 12.8 wheels; install torch from the `cu128` index before
anything else.

**Apple Silicon** — viable on CPU. The upstream integration notes report MPS is
*disabled by default* because some ops are unsupported, though it can be
force-enabled. CPU is the supported path. The model avoids source separation
entirely, which is what makes laptop inference practical at all.

## Implementation

The plan is implemented in [backend/analysis](../backend/analysis).

- `SECTIONIST_ENGINE` selects `auto` (default), `songformer` or `librosa`.
- `SECTIONIST_DEVICE` defaults to CUDA when available and otherwise CPU. MPS is
  opt-in, because of the cliff measured above.
- Model sections are merged (adjacent identical labels) and numbered for
  display (`Verse 1`, `Verse 2`).
- The model supplies only sections. Tempo, key, beats and chords still come
  from the librosa pipeline, so the response schema, the frontend and saved
  songs are unchanged.
- Sections carry the model's own probability for the chosen label, surfaced as
  a confidence score in the UI. The frame-level logits that the checkpoint
  discards are recovered with a hook on its post-processing call.
- Beat This! supplies the beat count and the downbeat grid; boundaries snap to
  the nearest downbeat within 0.35 s, which aligns sections to bars.
- The optional dependencies live in `backend/requirements-songformer.txt` and
  are not installed by CI.

### Known limitations

- **Repeated sections can receive different labels.** On `theone.mp3` the same
  material is labelled `chorus` at 48-80 s and `pre-chorus` at 128-144 s. The
  probabilities explain why this cannot be fixed by averaging:

  | Section | chorus | pre-chorus |
  | --- | --- | --- |
  | 48-64 s | 0.76 | 0.20 |
  | 64-80 s | 0.97 | 0.01 |
  | 128-144 s | 0.22 | 0.61 |

  The first occurrence points at `chorus` more strongly than the second points
  at `pre-chorus`, so any automatic reconciliation (majority, averaging, or
  "trust the more confident instance") pushes both towards `chorus` — the wrong
  answer. A conservative version is therefore deliberately *not* enabled.

  The useful workaround is user-driven: a "apply this label to similar
  sections" action in the editor would let a correction made once propagate
  deterministically. Fine-tuning a label head on corrected songs is the other
  route. Both are follow-ups, not part of this change.
- **Weak boundaries can be missed.** The 48-80 s section contains material that
  is split elsewhere, yet no boundary was placed inside it. The UI can split
  sections manually.
- Sounds are not snapped to beats, so boundary precision is limited to the
  model's frame rate (~8.3 frames per second after downsampling).

## Spike results

Run on an Apple **M1 Pro, 16 GB**, macOS 26.6.1, torch 2.14.1, transformers
4.57.6, against the SongFormer checkpoint (2.8 GB on disk). Input was a
synthetic 24 kHz track with a known structure (`intro 8s`, `verse 16s`,
`chorus 16s`, `verse 16s`, `chorus 16s`, `outro 8s`).

### Speed and memory

| Audio | Device | Wall time | Realtime factor | Peak RSS |
| --- | --- | --- | --- | --- |
| 80 s | CPU | 31-34 s | 2.4x | 5.4 GB |
| 80 s | MPS | 11-15 s | 7.3x | 0.6 GB |
| 120 s | MPS | 19 s | 6.3x | 0.6 GB |
| 200 s | CPU | 89 s | 2.3x | 8.1 GB |
| 200 s | MPS | **277 s** | **0.7x** | 0.7 GB |

Model load is ~2 s on CPU and ~5 s on MPS. Output is bit-identical between CPU
and MPS.

Two conclusions:

1. **CPU scales linearly** at roughly 2.3-2.4x realtime, using ~8 GB of RAM for a
   3-minute track. A 4-minute song takes about 100 s. That is acceptable for a
   desktop app with a progress bar.
2. **MPS is 3x faster but falls off a cliff between 120 s and 200 s.** At 200 s
   it is 8x slower than linear scaling predicts, which is consistent with
   unified-memory pressure and swapping on a 16 GB machine (the model is
   designed around 420 s windows). On a 16 GB Mac, either stay on CPU or chunk
   audio into ~90-120 s windows with overlap and stitch the results.

On a 32 GB RTX 5090 the whole 420 s window fits comfortably and upstream reports
2-4 s per song.

### Quality

The synthetic track's true boundaries were at 8, 24, 40, 56 and 72 s. SongFormer
found 7.92, 39.84, 55.92 and 71.88 — four of five, all within 0.16 s. It missed
the 24 s verse-to-chorus transition and merged those two sections.

Labels were weaker: the choruses were labelled `verse` and the outro `inst`.
That is not a fair test, because the input is sine-wave harmony with synthetic
percussion and sits far outside the model's training distribution. Quality on
real music is still unmeasured and needs a test with actual songs.

### Test on real music

Four real tracks (320 kbps CBR MP3, 44.1 kHz stereo), run on CPU:

| Track | Duration | Analysis time | Speed | Sections (raw / merged) |
| --- | --- | --- | --- | --- |
| `AV Man.mp3` | 192 s | 76 s | 2.5x | 9 / 6 |
| `theone.mp3` | 192 s | 74 s | 2.6x | 13 / 8 |
| `DownByTheRiver.mp3` | 73 s | 22 s | 3.4x | 3 / 2 |
| `paperback writer.mp3` | 34 s | 11 s | 3.1x | 3 / 3 |

Peak memory was 8.1 GB. Analysis is linear at roughly 2.5-3.4x realtime, so a
four-minute song takes about 90 s on an M1 Pro and 2-4 s on a modern GPU.

SongFormer predicts boundaries and labels with independent heads, so it often
emits a boundary where the label does not change (a repeated verse, for
example). Merging adjacent identical labels — the `merge_continuous_segments`
option in the authors' evaluation script — gives the useful view:

```
theone.mp3                        AV Man.mp3
  0.00  16.0  intro                 0.00  23.9  intro
 15.96  32.0  verse                23.88  24.1  verse
 48.00  31.9  chorus               48.00  23.9  chorus
 79.92  16.1  inst                 71.88  24.0  inst
 96.00  31.9  verse                95.88  48.0  verse
127.93  16.1  pre-chorus          143.89  48.1  inst
144.01  46.0  chorus
189.97   2.0  silence
```

`theone.mp3` comes out as a textbook pop form — intro, verse, chorus,
instrumental, verse, pre-chorus, chorus, silence. The pre-chorus detection is
notable: that is the kind of fine distinction the heuristic pipeline could not
make.

### Control test: are the boundaries real?

The 16- and 24-second section lengths in the two long tracks initially looked
like a fixed grid artefact, so this was tested directly by trimming the start of
a file and re-running. Coordinates are reported in the original file's timeline:

| Trim | First boundary | Second boundary |
| --- | --- | --- |
| 0 s | 11.88 | 29.76 |
| 4 s | 11.80 | 32.20 |
| 9 s | 11.88 | 32.16 |

The first boundary is locked to the audio content (it moves with the trim and
lands back at the same original timestamp within 0.08 s). The final
music-to-silence boundary drifts by up to 2.4 s, which suggests tail handling is
less stable than interior boundaries.

Conclusion: boundaries track content rather than a grid. The regular section
lengths appear to be genuine 8-bar/12-bar structure in these particular
electronic productions, not an artefact.

### What is still unmeasured

There is no ground truth here — no hand-labelled reference for these tracks — so
this demonstrates plausibility, stability and speed, not accuracy. Formal
evaluation would need annotated songs, ideally SongFormBench itself, which ships
300 expert-verified annotations.

### Setup gotchas (cost roughly an hour to work through)

These are not documented in the model card and are worth recording:

1. **transformers must be < 5.** With transformers 5.x, MuQ's constructor dies on
   a meta-device tensor mismatch. 4.57.6 works.
2. **The snapshot directory must be on `sys.path`,** and `SONGFORMER_LOCAL_DIR`
   set to it. The remote code imports its vendored siblings (`model`, `muq`,
   `musicfm`, `postprocessing`, ...) by bare name.
3. **Extra packages:** `omegaconf`, `ema-pytorch`, and `muq` (from PyPI — the MuQ
   source is *not* vendored in the checkpoint).
4. **`msaf` is imported unconditionally by `model.py`,** even though it is only
   used by an evaluation helper. It is an old package that breaks on modern
   scipy (`from scipy import inf`). Patching that one line to `from numpy import
   inf` fixes the import. A cleaner long-term fix is to vendor the model class
   without the evaluation dependency.
5. **MusicFM fetches `facebook/wav2vec2-conformer-rope-large-960h-ft`'s config
   at construction time,** so the first load needs network access even with the
   weights already downloaded.
6. Benign-looking `RuntimeWarning: invalid value encountered in divide` warnings
   are emitted during post-processing; they did not affect output.
7. Upstream's own integration notes say MPS is disabled by default, but it works
   here — subject to the memory cliff above.

### Reproducing

```bash
python3 -m venv .venv-songformer
.venv-songformer/bin/pip install torch torchaudio "transformers>=4.45,<5" \
    x-transformers einops soundfile numpy scipy librosa omegaconf ema-pytorch muq msaf
HF_HOME="$PWD/.hf-cache" .venv-songformer/bin/python -c \
  "from huggingface_hub import snapshot_download; \
   snapshot_download('ASLP-lab/SongFormer', local_dir='.hf-cache/SongFormer')"
```

Both the environment and the weights are gitignored.

## References

- SongFormer: [paper](https://arxiv.org/abs/2510.02797),
  [code](https://github.com/ASLP-lab/SongFormer),
  [weights](https://huggingface.co/ASLP-lab/SongFormer)
- All-In-One: [inference fork](https://github.com/openmirlab/all-in-one-infer)
- Beat This!: [code](https://github.com/CPJKU/beat_this)
- MuQ: [code](https://github.com/tencent-ailab/MuQ)
- MusicFM: [code](https://github.com/minzwon/musicfm)
- S-KEY: [code](https://github.com/deezer/skey)
- BTC: [code](https://github.com/jayg996/BTC-ISMIR19)
- MOSS-Music: [weights](https://huggingface.co/OpenMOSS-Team/MOSS-Music-8B-Thinking)
