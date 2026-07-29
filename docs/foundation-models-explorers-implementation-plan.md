# Foundation Models Explorers Implementation Plan

## Objective

Develop `TokenisationExplorer` and `DecodingExplorer` as two consecutive,
self-contained teaching views of the language-model pipeline:

```text
human-readable text -> token sequence -> precomputed model scores -> selected next token
                       TokenisationExplorer   DecodingExplorer
```

Both explorers must use the same terminology, token presentation, interaction
patterns, and visual states. They must remain deterministic and usable without a
downloaded or hosted language model.

## Product principles

- Keep the main teaching question visible without requiring students to infer
  which controls matter.
- Label simplified algorithms and illustrative quantities explicitly.
- Never imply that locally generated identifiers are real model vocabulary IDs.
- Use curated examples and precomputed scores so every calculation can be
  inspected and reproduced.
- Expose the same information to keyboard and assistive-technology users as to
  sighted mouse users.
- Retain the existing `ai9414` visual language while giving foundation-model
  demonstrations a layout suited to text, tokens, and distributions.

## Milestone 1: Correct TokenisationExplorer semantics and accessibility

Status: completed on 22 July 2026

### Semantics

- Include whitespace in the character-level tokeniser and display spaces, tabs,
  and line breaks with readable labels.
- Preserve whitespace boundaries in the simplified BPE representation by using
  a visible word-start marker. Make it clear that this is a teaching
  implementation rather than a production tokenizer.
- Remove misleading per-input token IDs from the primary UI. Retain the token
  index and add stable vocabulary IDs only if a real, fixed vocabulary is later
  introduced.
- Explain deterministic tie-breaking when several BPE pairs have the same
  frequency.
- Use one canonical BPE learning-state generator for both the public helper and
  the replay trace, avoiding duplicated implementations.
- Label the context figure as an illustrative token budget rather than a real
  model context limit.

### Accessibility

- Replace `role="img"` on rich foundation-model containers with labelled regions.
- Ensure the text editor, buttons, token sequence, merge state, and explanations
  remain exposed in the accessibility tree.
- Provide accessible text for whitespace tokens and BPE boundary markers.
- Announce replay explanations and status changes politely.
- Do not use colour as the sole indication of the active tokeniser or merge.
- Preserve visible keyboard focus and native keyboard behaviour.

### Acceptance criteria

- Character tokenisation round-trips all input characters, including whitespace.
- BPE output makes word starts visible and never silently loses whitespace.
- Token cards no longer claim to show vocabulary IDs.
- A tied BPE decision states the tie-break rule in both trace data and visible
  explanation.
- The Chrome accessibility tree exposes the editable textarea and its buttons.
- Existing API behaviour remains backwards compatible except for the explicitly
  corrected token semantics.
- Unit, API, and browser checks pass.

## Milestone 2: Introduce the shared foundation-model workbench

Status: completed on 22 July 2026

- Add a `foundation_models.explorer_kind` discriminator with `tokenisation` and
  `decoding` values.
- Replace the generic equal-height two-panel presentation for foundation models
  with a workbench containing:
  - a compact pipeline indicator;
  - one dominant teaching visual;
  - one contextual control area;
  - one explanation and replay strip.
- Use compact token chips instead of full-width cards for long sequences.
- Keep a single set of replay controls adjacent to the changing representation.
- Show corpus and merge controls only for learned BPE.
- Hide replay and playback-speed controls for static character and word modes.
- Move the illustrative token budget into a secondary “Why token count matters”
  disclosure.
- Remove nested scrolling and verify layouts at narrow, tablet, and desktop
  widths.

## Milestone 3: Build the DecodingExplorer model and trace

Status: completed on 22 July 2026

- Add validated `DecodingExample`, `DecodingProblem`, and `DecodingOptions`
  models.
- Store curated candidate tokens and precomputed logits, not generated text from
  a bundled LLM.
- Implement and test pure functions for:
  - numerically stable softmax;
  - temperature scaling;
  - greedy selection;
  - top-`k` filtering;
  - top-`p` filtering using the smallest prefix whose cumulative probability is
    at least `p`;
  - renormalisation;
  - seeded sampling.
- Build replay stages for model scores, temperature, filtering,
  renormalisation, and selection.
- Use the lecture mini-activity distribution as the default example and add
  peaked, flat, and long-tail distributions for comparison.
- Export `DecodingExplorer` from `ai9414.foundation_models` and add explicit CLI
  entries while retaining `ai9414 demo foundation-models` as a backwards-
  compatible TokenisationExplorer command.

## Milestone 4: Build the next-token DecodingExplorer interface

Status: planned

- Display context using the same token chips as TokenisationExplorer.
- Make the sorted candidate distribution the dominant visual.
- Provide a selection-rule control for Greedy, Sampling, Top-`k`, and Top-`p`.
- Treat temperature as a distribution transformation rather than a decoding
  method.
- Reveal `k` or `p` only for the corresponding rule.
- Show original probability, transformed probability, cumulative mass, retained
  status, renormalised probability, and selected token without relying on colour
  alone.
- Visualise the seeded random draw and its cumulative interval for sampling.
- State clearly that the candidate scores are precomputed and that arbitrary
  custom text cannot be passed to a model in this demo.
- Use an accessible data table as the semantic equivalent of the probability
  chart.

## Milestone 5: Sequence search and teaching extensions

Status: planned

- Add a separate Sequence Search view for greedy decoding and beam search.
- Use a small precomputed continuation tree with cumulative log-probabilities to
  demonstrate why a locally best token need not produce the best sequence.
- Add an optional repeated-sampling histogram to demonstrate variability without
  cluttering the primary next-token lesson.
- Provide cross-links between matching curated tokenisation and decoding
  examples without implying that arbitrary TokenisationExplorer input can
  produce model scores.
- Add instructor notes and a short student exercise API for each explorer.

## Verification strategy

### Algorithm tests

- Probabilities are finite, non-negative, and sum to one.
- Lower positive temperature reduces entropy and higher temperature increases
  entropy for a non-uniform distribution.
- Top-`k` retains exactly the permitted number of candidates.
- Top-`p` retains the smallest threshold-reaching prefix, including boundary
  cases and ties.
- Greedy selection is deterministic and seeded sampling is reproducible.
- Tokenisation preserves visible input boundaries and BPE learning is
  deterministic.

### Contract and API tests

- State and trace payloads carry the correct explorer discriminator.
- Invalid options return existing structured `AI9414Error` responses.
- Static tokenisers have no replay trace; learned BPE and decoding traces contain
  the expected stages.
- Static exported solution replays retain the same semantics as the live view.

### Interface and accessibility tests

- Mode-dependent controls are absent or disabled with an explanation.
- There is no `0 / 0` replay interface for static modes.
- Native inputs and buttons appear in the accessibility tree in logical order.
- Current state, retained candidates, and selected tokens have textual labels.
- Keyboard-only editing, replay, method selection, and sampling work.
- Screenshots are checked at approximately 320, 768, and 1440 CSS pixels.
- No dominant panel leaves a large unused column while related content continues
  far below it.

## Out of scope

- Bundling, downloading, or calling a pretrained language model.
- Presenting this simplified BPE implementation as equivalent to a particular
  production tokenizer.
- Generating next-token scores for arbitrary custom text.
- Redesigning unrelated `ai9414` search, planning, logic, CSP, or uncertainty
  demonstrations.
