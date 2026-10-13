# Kevin and Jeff bedroom furnishing pass

## September 14 placement correction

Re-reviewed [5:55](part2-355s.jpg), [6:05](part2-365s.jpg), [6:15](part2-375s.jpg), and [6:25](part2-385s.jpg) from the archived Marina Part2 tour. Reading chair adjoins the dresser at the east window; desk occupies the opposite west window beside the trunk/entry wall. The initial Unity furnishing had these reversed. Moved the entire desk assembly−2.75mX and chair+3.30mX; unchanged sizes, bunk, dresser, bookcase and walls. Relative arrangement weight3; absolute historical coordinates weight1. These translations are model corrections, not measured film dimensions.

Saved through `ReconcileKevinWindowFurniture()`, also invoked by full furnishing builder. Expanded walking check to16 checkpoints including relocated desk and chair approaches; passes. Settled `Assets/Captures/IntactHouseReference/kevin-window-layout.png` inspected; material/lighting quality remains provisional. Earlier12-point check below is historical.

References extracted from the locally archived Part 2 CG tour:

- 335s: production-set view showing small-pattern wallpaper and decorative upper border.
- 355–385s: Marina reconstruction showing wooden bunk beds, green bedding, dresser/mirror, pale reading chair, bookcase, window desk/banker lamp, checked curtains, pinboard and toy trunk.
- 310s: film family photograph, contextual only; not room geometry evidence.

Unity's intact bedroom has interior bounds approximately X4.92–9.86, Z−2.30–2.01, floor Y5.21. Entrance is near X5.94/Z2.1. Walls and existing windows are retained. Bunk head sits at the back wall beside the entry; dresser is on the adjoining east wall. Desk and bookcase use the front windows. This is an adapted furnishing arrangement, not a measured replica of Marina's room.

KevinBedroom.cs creates KevinBedroomDetails and dedicated finish assets. Existing wall renderers object81 and window-wall infill object80 receive a small-motif material; original GLB is unchanged. Wallpaper and checked fabric are simple authored repeats inspired by the reference, not scans of the historic prints. Green bedding lacks the reference's detailed lower-quilt pattern. Dresser mirror uses environment reflection. Decorative border, dartboard, detailed toys/art and functioning bunk ladder remain unimplemented.

Existing shoes (object15) moved beside the trunk and football (object0) beside the window to clear circulation; all original collision meshes retained. Twelve real-controller checkpoints pass from the hall through the room, along both sides of the bunk, to desk/bookcase approaches and back. Walking check does not claim bunk climbing. Scene stays in daytime.
