# Mission Config

## Purpose

This document defines the initial mission-data format for the simulator.

It exists to separate:
- scenario data that belongs in config files,
- from reusable rule logic that belongs in the domain engine.

The first concrete target is Mission 1.

## Scope

This document defines:
- the initial file format for mission configs;
- the coordinate convention used to transcribe printed maps;
- the minimum schema needed to represent Mission 1 faithfully;
- the transcription convention future missions should follow.

This document does not define:
- the final Python loader API;
- the full long-term mission schema for every later mechanic;
- the complete action/state model.

Those remain implementation concerns.

## File format

Mission files should initially use **TOML**.

Reasons:
- human-editable;
- structured enough for nested mission data;
- readable in diffs;
- loadable in Python without adding YAML-specific dependencies.

## Scenario data vs engine logic

Mission configs should contain scenario data such as:
- map cells and terrain;
- start hexes;
- hidden marker locations;
- pre-revealed enemy placements;
- mission-specific unit roster;
- mission-specific Orders Chart rows;
- mission-specific Enemy Unit Chart rows;
- mission objective text and machine-readable objective kind;
- mission-specific numeric modifiers.

Mission configs should **not** contain general rule logic such as:
- how reveal resolution works;
- how morale changes work;
- how a Fire Zone is computed;
- how doubles / rerolls work;
- how legal actions are generated.

Those rules belong in the domain engine.

## Coordinate convention

Printed maps should be transcribed using **flat-top axial coordinates** with
integer `(q, r)` hex coordinates.

Direction deltas are:

- `up_left = (-1, 0)`
- `up = (0, -1)`
- `up_right = (1, -1)`
- `down_right = (1, 0)`
- `down = (0, 1)`
- `down_left = (-1, 1)`

For British units, the rulebook's "forward" direction means:
- `up_left`
- `up`
- `up_right`

This convention is chosen because it matches the printed maps naturally:
- each hex has three forward neighbors toward the top of the page;
- each hex has three backward neighbors toward the bottom of the page.

## Transcription rule

When transcribing a printed map:

1. pick a stable anchor hex;
2. assign it an axial coordinate;
3. assign every other playable hex by adjacency;
4. record terrain on the hex itself;
5. record hidden `?` markers separately from terrain;
6. record start hexes separately from British units;
7. record blocked edges separately from hex terrain if rivers/bridges exist.

Recommended anchor rule:
- use the top-most central playable hex as `(0, 0)` when practical.

## Setup modeling rule

Mission configs should describe the **setup space**, not only one fixed setup
result.

That means:
- British roster should be listed as available units;
- start hexes should be listed as allowed setup hexes;
- unit placement should only be pre-filled in config when the mission itself
  forces it.

For Mission 1, setup is effectively deterministic because there is only one
start hex, but the schema should still preserve the distinction.

## Initial schema for Mission 1

The first mission config should contain these sections:

### Top-level metadata

- `schema_version`
- `mission_id`
- `name`

### Source metadata

- rulebook path
- briefing page
- map page

### Turn metadata

- turn limit
- whether turn 1 is already marked on the printed tracker

### Objective

- machine-readable objective kind
- human-readable description

### Map

- coordinate system id
- forward directions
- playable hex list with terrain
- start hex list
- hidden marker list

Optional later additions:
- blocked edges
- pre-revealed units
- labels / landmarks

### British roster

- concrete unit ids present in the mission
- mission-local unit-class data for the British classes used here
- mission-specific Orders Chart for those classes

### German mission data

- German unit-class data for the enemy classes used in this mission
- mission-specific Enemy Unit Chart rows

### Modifier table

- mission-specific numeric combat modifiers printed on the briefing page

## Mission 1 transcription

Mission 1 is transcribed using the top wooded hex as `(0, 0)`.

Playable hexes:

| q | r | terrain | note |
|---|---|---------|------|
| 0 | 0 | woods | top center |
| -1 | 1 | woods | upper left |
| 1 | 0 | woods | upper right |
| 0 | 1 | woods | hidden marker hex |
| -1 | 2 | woods | middle left |
| 1 | 1 | clear | middle right |
| 0 | 2 | clear | lower center |
| -1 | 3 | clear | lower left |
| 1 | 2 | woods | lower right |
| 0 | 3 | clear | start hex |

Mission 1 hidden markers:

- `(0, 1)`

Mission 1 start hexes:

- `(0, 3)`

## Current concrete file

The first concrete config file using this convention is:

- `configs/missions/mission_01_secure_the_woods_1.toml`

This file should be treated as the initial reference example for future mission
transcriptions.
