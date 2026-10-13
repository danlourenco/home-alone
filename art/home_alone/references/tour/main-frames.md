# Main-floor frame index

29 frames decoded from the user-provided MP4. Click a timecode to open its original 640 × 360 PNG. Marina’s model is the fidelity target. The contact sheets are navigation previews; no source image was enlarged or AI-enhanced.

| ID | Time / original PNG | Reference |
| --- | --- | --- |
| M01 | [03:20](frames/M01-03m20s.png) | Entry and main stair |
| M02 | [03:40](frames/M02-03m40s.png) | Dining room |
| M03 | [03:50](frames/M03-03m50s.png) | Dining side opening |
| M04 | [05:40](frames/M04-05m40s.png) | Main stair |
| M05 | [05:50](frames/M05-05m50s.png) | Landing |
| M06 | [07:00](frames/M06-07m00s.png) | Living fireplace |
| M07 | [07:20](frames/M07-07m20s.png) | Living piano end |
| M08 | [09:30](frames/M08-09m30s.png) | Den TV wall |
| M09 | [09:50](frames/M09-09m50s.png) | Den window and desk |
| M10 | [13:10](frames/M10-13m10s.png) | Kitchen / breakfast plan |
| M11 | [14:30](frames/M11-14m30s.png) | Window-seat diagram |
| M12 | [14:40](frames/M12-14m40s.png) | Back door and sink |
| M13 | [14:50](frames/M13-14m50s.png) | Window seats |
| M14 | [15:00](frames/M14-15m00s.png) | Kitchen reverse |
| M15 | [15:10](frames/M15-15m10s.png) | Breakfast and stair |
| M16 | [16:40](frames/M16-16m40s.png) | Aligned room openings |
| M17 | [13:23](frames/M17-13m23s.png) | Kitchen area annotation |
| M18 | [15:25](frames/M18-15m25s.png) | Breakfast hutch and foyer opening |
| M19 | [15:40](frames/M19-15m40s.png) | Breakfast toward kitchen |
| M20 | [17:47](frames/M20-17m47s.png) | Foyer rear arch and stair |
| M21 | [18:05](frames/M21-18m05s.png) | L-shaped island and window-seat wall |
| M22 | [18:17](frames/M22-18m17s.png) | Kitchen sink and rear door |
| M23 | [18:34](frames/M23-18m34s.png) | Breakfast dining connection and stair |
| M24 | [18:45](frames/M24-18m45s.png) | Breakfast into dining |
| M25 | [19:05](frames/M25-19m05s.png) | Living room into den |
| M26 | [09:20](frames/M26-09m20s.png) | Den sofa and TV arrangement |
| M27 | [09:40](frames/M27-09m40s.png) | Den into living room |
| M28 | [19:35](frames/M28-19m35s.png) | Living room into foyer |
| M29 | [19:42](frames/M29-19m42s.png) | Foyer into dining room |

Source identity and video-stream information: [local-video.json](local-video.json). Selected timestamps and file paths: [keyframes.json](keyframes.json).

To reproduce a frame from the repository root (example: the onscreen area annotation):

```sh
ffmpeg -ss 803 -i 'Tour the Home Alone House_ Part 1, Main Floor [CG Tour].mp4' -map 0:0 -frames:v 1 -update 1 /tmp/kitchen-area.png
```

The explicit stream selection avoids extracting the embedded 1280 × 720 cover art. Part 2 has no local MP4 yet; its references remain storyboard thumbnails.

**2026-09-11:** the same 29 timestamps decoded from the user-provided 1920 × 1080 Part 1 file are in [frames-hd/](frames-hd/) (JPEG q92). Use those for detail work; the 640 × 360 PNGs above remain for provenance.
