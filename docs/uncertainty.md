# Reasoning with uncertainty

The uncertainty demo requires Python 3.11 or newer. Update the package and start
the demo:

```bash
python -m pip install --upgrade ai9414
ai9414 demo uncertainty
```

## Manual belief updates

The default `two_doors` example has ten cells and doors at cells 2 and 6. Click
**Sense door**, **Move right**, then **Sense no door**. These buttons create the
updates; **Previous**, **Next** and **Play** replay the history afterwards.

The maxima are cells 2 and 6 after the first observation, then cells 3 and 7
after motion and after the final observation. Both final maxima have probability
approximately 0.241. The observations do not resolve the two-location ambiguity.
The display highlights every tied maximum, including all cells for a uniform
prior.

**Reset** clears the interactive history and restores the initial belief, true
position and seeded random stream while retaining the current model settings.
**Reload example** also restores the example's original model settings.
In live Python mode, **Reset** rewinds the returned trace for replay.

The `bad_sensor` example has hit rate 0.45 and false-alarm rate 0.50. It supplies
weak evidence in the reverse direction: a positive reading makes door cells less
likely. A sensor is uninformative when these rates are equal. The separate
`bad_sensor` exercise uses equal rates of 0.50 to demonstrate that case.

## Python exercise

Click **Download Python stub**, extract the ZIP and open its `ai9414` folder.
Install the live workflow's dependency:

```bash
python -m pip install -r requirements.txt
```

Implement these functions in `week7_bayes_filter_stub.py`:

- `normalise(values)`
- `sensor_update(belief, corridor, sensor, sees_door)`
- `motion_update_right(belief, motion)`

The functions use zero-based indices internally. `door_cells={1, 3}` denotes
student-facing cells 2 and 4. Motion beyond the corridor end stays in the final
cell. Use a fresh list for the motion result.

Check the implementation and run the standalone five-cell example:

```bash
python week7_bayes_filter_stub.py --check
python week7_bayes_filter_stub.py --demo
```

These two modes use only the Python standard library. The standalone example
has five cells and doors at cells 2 and 4, unlike the browser's default ten-cell
example.

## Connect the implementation to the browser

Start the local solver and leave the terminal running:

```bash
python week7_bayes_filter_stub.py
```

In another terminal, start `ai9414 demo uncertainty`, then click **Solve with
Python**. The browser sends its current corridor and the example's scripted
events to `http://127.0.0.1:9414/solve`. Use **Next** or **Play** to inspect the
returned belief trace. The solver reports unfinished functions and rejects
incorrect updates with an explanation. Save the script and restart the solver
after editing it.

The supplied adapter converts the selected landmark's cells to the exercise's
`Corridor` object, so door, sign and other landmark observations use the same
four-argument student function. Left moves use the built-in reference operation;
the motion exercise implements right moves.

Manual Sense and Move buttons use the built-in demo. **Solve with Python** runs
the example's scripted sequence using the student's functions, rather than
replaying manually added events.

The Python API writes the same starter file as the browser download:

```python
from ai9414.uncertainty import BayesFilterDemo

BayesFilterDemo().write_stub("week7_bayes_filter_stub.py")
```

## Version 0.2.1

- Fixed Reset retaining previous interactive events and random-stream state.
- Connected the downloaded starter to the live solver, retaining standalone
  checks and demonstration modes.
- Made the browser download and `write_stub` use one packaged source file.
- Reported and highlighted all tied maximum-probability cells, including in
  exported solution viewers. Existing singular fields remain available to API
  consumers and select the first tied cell.
- Corrected the two-door example description and distinguished reversed sensor
  evidence from an uninformative sensor.
- Checked student normalisation on unnormalised probability masses and rejected
  unnormalised sensor output instead of silently repairing it.
