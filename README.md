# Home Alone house

A faithful, walkable Unity recreation of the McCallister house from *Home Alone* (1990), built as the setting for a game:
Kevin (kid-scale) against the bandits (adults). A personal hobby project.

- **Engine:** Unity 6000.6.0f1, HDRP, project in `unity/HomeAlone` (main scene `Assets/Scenes/House_WallGrid.unity`).
- **Where things stand:** [docs/RESUME.md](docs/RESUME.md) (current state, queue), [docs/STATUS.md](docs/STATUS.md) (the long log).
- **How it is built:** geometry from structure-from-motion on Marina Coates's CG tour videos, checked against the film
  (film first, Marina as the fallback); see [docs/RECONCILIATION.md](docs/RECONCILIATION.md). Every departure from measurement is in
  [docs/DEVIATIONS.md](docs/DEVIATIONS.md).
- **Rules for agents and contributors:** [AGENTS.md](AGENTS.md) (verification gates, one builder at a time, skills index).

## Build and walk
```sh
git config core.hooksPath .githooks          # once per clone: the change gate runs on commit
HA_SCRATCH=$HOME/.cache/home-alone-2 tools/house/unity_pipeline.sh preflight   # cheap gates
HA_SCRATCH=$HOME/.cache/home-alone-2 tools/house/unity_pipeline.sh all         # build + bake + load into the open editor, Play
```
In Play: WASD + mouse, Shift sprint, C crouch, G kid/adult, E interact (doors, the den seat, Buzz's footlocker, the zipline),
N day/night, O weather (sunny / morning / overcast), K hide everything off the lot, F snow, M leave a walk note. Full list in
`unity/HomeAlone/Assets/Scripts/FpsController.cs`.

Third-party assets and their licences: [CREDITS.md](CREDITS.md). Purchased and store assets are gitignored, as are the film frames.
