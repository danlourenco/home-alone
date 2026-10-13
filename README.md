# home-alone

A small Godot 4 experiment for asymmetric trap defense (Kevin) versus intrusion (Bandit).

## Blender house blockout

An editable [Blender model and reference notes](art/home_alone/README.md) are in
`art/home_alone`. Open `scenes/House_Blockout_Preview.tscn` and press F6 for a
standalone walkthrough of the ground floor, upstairs, and attic. The existing
multiplayer startup scene remains the MVP level.

## Marina house FPS walkthrough

Open `scenes/Marina_House_Walkthrough.tscn` in Godot and choose **Run Current Scene (F6)**, or launch directly on this Mac:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --path /Users/dlo/Dev/home-alone --scene res://scenes/Marina_House_Walkthrough.tscn
```

WASD moves, mouse looks, Shift sprints, Space jumps, C/Ctrl crouches, and R resets to the foyer. Esc releases the cursor; click to recapture. [Editable Blender source, controls and current limitations](art/home_alone/marina/README.md).

## Prerequisites
- Godot 4.2 or later (project targets the 4.2 feature set).
- A terminal for running multiple local instances (examples below use `godot4` on the PATH).

## Opening the project
1. Launch Godot 4 and choose **Import/Scan**.
2. Point the editor at this repository folder (or directly at `project.godot`).
3. Open `scenes/Main.tscn` as the startup scene if prompted; it already wires in the level and HUD.

## Running two local instances (Kevin hosts, Bandit joins)
Networking is driven by autoloaded scripts. Use the provided CLI flags to auto-host or auto-join:
- `--host [port]` starts a server on the given port (default 7000) and spawns Kevin.
- `--join <address> [port]` connects to a host and spawns the Bandit if that slot is free; further peers become spectators.

Example workflow on one machine:
1. **Host (Kevin):** In terminal 1, run `godot4 --path . --remote-debug 6007 -- --host 7000`.
2. **Client (Bandit):** In terminal 2, run `godot4 --path . --remote-debug 6008 -- --join 127.0.0.1 7000`.
3. **Third client (spectator):** A third launch with `--join` will connect for phase/budget updates but currently will not spawn a pawn or camera because only Kevin and the first Bandit are instantiated.

Tips:
- Use distinct `--remote-debug` ports per instance to avoid editor debug conflicts.
- If you change the port for the host, pass the same port to all joining clients.

## Controls
- **Move:** WASD (`move_forward`, `move_back`, `move_left`, `move_right`).
- **Sprint:** Shift (`sprint`).
- **Jump:** Space (`jump`).
- **Mouse look:** Move the mouse (captured on start).
- **Interact:** `E` to place a trap on a highlighted socket when playing Kevin (`interact`).
- **Trap selection (Kevin):** Number keys 1–4 (`trap_slot_1`–`trap_slot_4`).
- **Trap activation:** Traps automatically trigger when an actor enters their area.

## Implemented gameplay
- Kevin auto-hosts and Bandit auto-joins through the `--host` / `--join` flags; additional peers are assigned the spectator role. Spawning uses role-specific markers for Kevin and Bandit. Phase/budget selection state is synchronized to all peers.【F:scripts/net.gd†L6-L90】【F:scenes/Level_House_MVP.tscn†L44-L71】
- Match phases (Prep → Breach → End) tick on the server with timers, budget reset, and HUD updates. Time is broadcast periodically to clients.【F:scripts/match_manager.gd†L5-L96】
- Kevin can select traps via number keys, spend from a shared budget, and place them on empty sockets; placement is validated on the server before spawning the trap instance network-wide.【F:scripts/player.gd†L25-L98】【F:scripts/match_manager.gd†L21-L135】【F:scripts/traps/trap_socket.gd†L1-L22】
- Traps apply damage or status effects (slow, burn, stun, frozen) to bodies that enter their trigger areas, clearing themselves afterward.【F:scripts/traps/trap_base.gd†L1-L27】【F:scenes/traps/MicroMachines.tscn†L1-L24】【F:scenes/traps/BlowtorchDoor.tscn†L1-L24】【F:scenes/traps/PaintCan.tscn†L1-L24】【F:scenes/traps/IcySteps.tscn†L1-L24】

## Remaining gaps / known issues
- Spectator peers receive synchronized phase/budget state but are not spawned into the world; there is no spectator camera yet.【F:scripts/net.gd†L47-L90】【F:scripts/match_manager.gd†L140-L157】
- Player health/status effects are tracked but there is no win/loss condition or HUD feedback for damage; matches loop through phases indefinitely.【F:scripts/player.gd†L9-L119】【F:scripts/match_manager.gd†L55-L70】
- Networking is initiated only through command-line flags; there is no in-game UI for hosting or joining sessions.【F:scripts/net.gd†L6-L45】
