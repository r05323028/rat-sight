## ADDED Requirements

### Requirement: Non-obstructive citizen-report inspection

The dashboard SHALL present selected citizen-report details outside the map canvas. Desktop details
SHALL live in the control rail; narrow viewports SHALL use a collapsible sheet that preserves map
gestures and safe-area insets. Selecting a marker SHALL highlight it and open details without
starting a simulation. The run action SHALL stay explicit, and context-only categories SHALL keep it
disabled with an explanation.

#### Scenario: Selecting a marker shows details beside the map

- **WHEN** a user selects a published citizen-report cell on desktop
- **THEN** the cell is highlighted and the inspector renders in the control rail without covering the map
- **AND** no simulation request is sent until the user activates the explicit run action

#### Scenario: Mobile details stay collapsible

- **WHEN** a user selects a cell in a narrow viewport
- **THEN** the details appear in a bottom sheet that can be dismissed and does not block map gestures
- **AND** the run action remains reachable and the compact state does not cover most of the viewport

### Requirement: Stable map source and layer lifecycle

The map SHALL initialize once and keep stable source and layer identities for static geographic
data. Data changes SHALL use source updates, selection SHALL use filters or feature state, and
visibility SHALL use layout properties. Playback ticks, marker selection, viewport movement, and
React re-renders SHALL NOT remove and re-add static sources or layers; recreation SHALL happen only
on a style reload or teardown. Dynamic layers SHALL update without rebuilding static layers.

#### Scenario: Playback does not rebuild layers

- **WHEN** the user advances, pauses, or switches simulated playback steps
- **THEN** the simulation and network sources keep their identity and no layer is removed or re-added
- **AND** only presentation properties and dynamic layer data change

#### Scenario: Panning keeps the static layers

- **WHEN** the user pans or zooms with citizen markers and simulated routes displayed
- **THEN** static sources and layers are not reconstructed
- **AND** no simulation geometry is recomputed from the viewport change

### Requirement: Progressive simulated-route reveal

When a simulation response arrives, the dashboard SHALL reveal the simulated routes along the
returned trajectory geometry from the origin toward the traversed segments, rather than displaying
all routes at full intensity at once. The reveal SHALL use the original ordered geometry and SHALL
NOT draw straight shortcuts between graph nodes. After the reveal the routes SHALL settle into a
readable static state that identifies the source cell and the `SIMULATED` classification.

#### Scenario: Routes grow from the origin

- **WHEN** a simulation response is rendered
- **THEN** the simulated route layer becomes visible progressively from the origin along its geometry
- **AND** the final state shows the complete simulated edges with the origin and `SIMULATED` label intact

#### Scenario: New origin replaces the previous reveal

- **WHEN** the user runs a simulation for a different cell
- **THEN** any running reveal is stopped and the previous route presentation is replaced
- **AND** no tween from the previous response writes into the new visualization

### Requirement: Bounded route-flow indication

The aggregate route presentation SHALL support a subtle flow indication that follows the simulated
direction of travel, using a bounded number of animated positions. A bidirectional edge SHALL NOT be
rendered as one-way movement, and the visual speed SHALL NOT be presented as real rodent speed. The
flow SHALL be disabled when animation is disabled or reduced motion is requested.

#### Scenario: Flow follows simulated traversal

- **WHEN** the aggregate mode renders simulated edges with animation enabled
- **THEN** flowing markers move along the rendered edge geometry and not across empty space
- **AND** the number of animated markers stays bounded for the visible result

#### Scenario: Disabling animation removes the flow

- **WHEN** the user turns off the animation toggle or requests reduced motion
- **THEN** the flow markers are cleared and the static routes remain readable

### Requirement: Walker position playback

In individual trajectory mode the dashboard SHALL place a position marker for the selected walker
and move it along that walker's returned polyline, interpolating by geographic distance rather than
straight-line endpoints. The traversed portion SHALL be visually distinct from the upcoming portion,
playback SHALL stop at the last available step, and changing the selected walker, origin, or step
SHALL NOT leave a stale marker or tween. Playback speed SHALL affect visual timing only.

#### Scenario: Walker follows its own route

- **WHEN** the user selects a walker and advances playback
- **THEN** the marker moves along that walker's LineString through each returned step
- **AND** the traversed prefix is drawn distinctly from the upcoming path

#### Scenario: Changing walkers clears the old position

- **WHEN** the user selects a different walker or another origin
- **THEN** the previous marker and tween are removed
- **AND** the new selection starts from its own first available step

### Requirement: Animation control and reduced motion

The dashboard SHALL offer a small set of playback speeds, an animation enable/disable control, and
a note that playback speed is not real rodent movement speed. When `prefers-reduced-motion` is
requested, continuous animation SHALL default to disabled while static routes and step-by-step
inspection remain usable. Animation SHALL NOT require a React state update per frame, SHALL stop on
unmount, and SHALL clean up its listeners and tweens.

#### Scenario: Reduced motion keeps a usable result

- **WHEN** the user has reduced motion enabled
- **THEN** the animation control starts disabled, no continuous flow runs, and routes render statically
- **AND** previous, next, reset, and walker selection still work

#### Scenario: Speed and toggle are explicit

- **WHEN** the user changes the playback speed or animation toggle
- **THEN** the selected speed and state apply to subsequent playback without rerunning the simulation
- **AND** the explanatory note remains visible

### Requirement: Measured rendering performance

The change SHALL record before/after measurements on one machine, viewport, snapshot, and network,
covering frame timing, commits, source and layer rebuild counts, GeoJSON cost, network requests,
animation frames, payload, and approximate memory. Claims SHALL NOT use invented frame-rate targets,
and checks SHALL confirm that panning and playback do not rebuild static layers, animation follows
returned geometry, and no stale tween survives an origin change or unmount.

#### Scenario: Rebuild counts are part of the evidence

- **WHEN** the measurement harness plays back steps and pans with a simulation visible
- **THEN** the recorded source and layer rebuild deltas show no reconstruction during playback or panning
- **AND** the report compares those numbers with the baseline implementation

#### Scenario: Unmeasured hardware is disclosed

- **WHEN** the performance report is written
- **THEN** it names the machine, browser, viewport, snapshot, and network used
- **AND** it discloses hardware or browsers that were not measured instead of implying coverage
