using System.IO;
using System.Linq;
using System.Text;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// Gameplay rigs from spec/dressing/traps.json (docs/paint-can-trap.md). Built AFTER BuildWallGrid's gates, on the Ignore Raycast
// layer (2): no walk, seam, clash, props or peek check sees them, and the dummy's foot ray skips the rig.
public static partial class SpecGreybox
{
    const int TrapLayer = 2;

    static void Traps(GameObject root, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/traps.json"));
        if (!File.Exists(fp)) return;
        var j = JObject.Parse(File.ReadAllText(fp));
        var spec = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var g = Child(root, "Traps"); Physics.SyncTransforms();
        int mask = ~(1 << TrapLayer);
        PaintCanTrap owner = null;   // the first can builds the shared dummy
        foreach (var t in j["paint_cans"])
        {
            string name = (string)t["name"]; float sz = (float)t["z"], z = -sz;
            // the gallery rail over the flight (geometry.json upstairs rail along spec z), PROBED in the built scene: its top (ray down),
            // its stairwell face (ray across, at the handrail), the floor's edge below it (ray across at -5 cm) and that edge's underside
            var rail = geo["upstairs"]["openings"].First(o => (string)o["kind"] == "rail" && (string)o["axis"] == "x" && (float)o["lo"] <= sz && sz <= (float)o["hi"]);
            float c = (float)rail["c"];
            if (!Physics.Raycast(new Vector3(c, 2.0f, z), Vector3.down, out var top, 1.5f, mask)) { Debug.LogWarning($"Traps {name}: no rail top at x {c}"); continue; }
            float railTop = top.point.y, railMid = railTop - 0.03f;
            float railFace = Physics.Raycast(new Vector3(c - 1.5f, railMid, z), Vector3.right, out var rf, 1.6f, mask) ? rf.point.x : c - 0.03f;
            float floorFace = Physics.Raycast(new Vector3(c - 1.5f, -0.05f, z), Vector3.right, out var ff, 1.6f, mask) ? ff.point.x : railFace;
            float edgeY = Physics.Raycast(new Vector3(floorFace + 0.03f, -1.5f, z), Vector3.up, out var eu, 1.6f, mask) ? eu.point.y : -0.2f;
            float ropeR = (float)t["rope_diameter_m"] / 2;
            var pivot = new Vector3(Mathf.Min(railFace, floorFace) - ropeR, railMid, z);   // the rope drops clear of the rail and the floor edge
            var knot = new Vector3(c, railTop + ropeR, z);
            var edge = new Vector3(floorFace, edgeY, z);
            // length: at the bottom of the arc the can's centre is at the face of an adult standing on the hit step
            var step = spec["stair"]["boxes"].First(b => (string)b["name"] == (string)t["hit_step"]);
            float feet = (float)step["y"][1], face = feet + (float)t["face_above_feet_m"];
            var cj = t["can"]; float dia = (float)cj["diameter_m"], h = (float)cj["height_m"], rise = (float)cj["bail_rise_m"];
            float comBelow = rise + h / 2, L = pivot.y - face - comBelow;
            Debug.Log($"Traps {name}: rail top {railTop:F3} (upper floor = 0; ground {railTop - gy:F3}), rail face x {railFace:F3}, floor edge x {floorFace:F3} y {edgeY:F3}; " +
                      $"pivot {pivot}; {(string)t["hit_step"]} tread {feet:F3}, face {face:F3}; rope {L:F3} m, pivot to can centre {L + comBelow:F3} m");

            var rig = Child(g, name);
            var canGo = new GameObject("Can"); canGo.transform.SetParent(rig.transform, false); canGo.transform.position = pivot + Vector3.down * L;
            Color Col(JToken a) => new Color((float)a[0], (float)a[1], (float)a[2]);
            // collision: an invisible cylinder the can's size (convex hull of Unity's built-in mesh: readable in any build)
            var body = GameObject.CreatePrimitive(PrimitiveType.Cylinder); body.name = "Collider";
            body.transform.SetParent(canGo.transform, false); body.transform.localPosition = Vector3.down * comBelow; body.transform.localScale = new Vector3(dia, h / 2, dia);
            Object.DestroyImmediate(body.GetComponent<Collider>()); Object.DestroyImmediate(body.GetComponent<MeshRenderer>()); body.AddComponent<MeshCollider>().convex = true;
            // the look: tools/house/hifi_paint_can.py (closed body with chime rims, sunk lid, label band, ears, wire bail); origin = bail apex
            var model = AssetDatabase.LoadAssetAtPath<GameObject>((string)t["model"]);
            if (model == null) Debug.LogWarning($"Traps {name}: {(string)t["model"]} not imported; the can is invisible");
            else
            {
                var vis = (GameObject)Object.Instantiate(model, canGo.transform); vis.name = "PaintCan"; vis.transform.localPosition = Vector3.zero; vis.transform.localRotation = Quaternion.identity;
                var mats = ((JObject)cj["colours"]).Properties().ToDictionary(q => q.Name, q => Mat($"Trap_{name}_{q.Name}", Col(q.Value)));   // film-sampled (traps.json)
                foreach (var r in vis.GetComponentsInChildren<MeshRenderer>())
                {
                    r.sharedMaterials = r.sharedMaterials.Select(m => m != null && mats.TryGetValue(m.name.Split(' ')[0], out var hm) ? hm : m).ToArray();
                    foreach (var cc in r.GetComponents<Collider>()) Object.DestroyImmediate(cc);
                }
                var mb = vis.GetComponentsInChildren<MeshRenderer>().Select(r => r.bounds).Aggregate((a, b) => { a.Encapsulate(b); return a; });
                Debug.Log($"Traps {name}: can model bounds {mb.size} (spec {dia} x {h + rise}), bottom {mb.min.y - canGo.transform.position.y:F3} below the tie");
            }
            var rb = canGo.AddComponent<Rigidbody>();
            rb.mass = (float)cj["mass_kg"]; rb.linearDamping = 0.005f; rb.angularDamping = 0.05f; rb.interpolation = RigidbodyInterpolation.Interpolate;
            rb.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;   // solver iterations: PaintCanTrap.Setup (runtime-only)
            var ropeLr = new GameObject("Rope").AddComponent<LineRenderer>(); ropeLr.transform.SetParent(rig.transform, false);
            ropeLr.useWorldSpace = true; ropeLr.widthMultiplier = 2 * ropeR; ropeLr.numCapVertices = 2; ropeLr.generateLightingData = true; ropeLr.shadowCastingMode = ShadowCastingMode.On;
            ropeLr.sharedMaterial = Mat("Trap_Rope", new Color(0.86f, 0.84f, 0.78f));
            ropeLr.positionCount = 3; ropeLr.SetPositions(new[] { knot, pivot, canGo.transform.position });

            var trap = rig.AddComponent<PaintCanTrap>();
            trap.can = rb; trap.rope = ropeLr; trap.knot = knot; trap.pivot = pivot; trap.edge = edge; trap.ropeLength = L; trap.comBelowBail = comBelow;
            trap.releaseDeg = (float)t["release_deg"];
            trap.pullKey = System.Enum.Parse<KeyCode>((string)t["pull_key"]); trap.letGoKey = System.Enum.Parse<KeyCode>((string)t["let_go_key"]); trap.swingDir = Vector3.left; trap.canRadius = Mathf.Sqrt(dia * dia / 4 + h * h / 4);
            if (owner == null && j["dummy"] is JObject dj)
            {   // the adult test body: a capsule, kinematic, walked up the flight's walk line to stand on the hit step under the rail
                float dh = (float)dj["height_m"], dr = (float)dj["radius_m"];
                var d = GameObject.CreatePrimitive(PrimitiveType.Capsule); d.name = "TrapDummy"; d.transform.SetParent(rig.transform, false);
                d.transform.localScale = new Vector3(2 * dr, dh / 2, 2 * dr);
                d.GetComponent<MeshRenderer>().sharedMaterial = Mat("Trap_Dummy", new Color(0.45f, 0.47f, 0.5f));
                var drb = d.AddComponent<Rigidbody>(); drb.isKinematic = true; drb.interpolation = RigidbodyInterpolation.Interpolate;
                trap.dummy = drb; trap.dummyHeight = dh; trap.dummyStartX = (float)dj["start_x"]; trap.climbSpeed = (float)dj["climb_speed_mps"];
                trap.dummyMarkX = ((float)step["x"][0] + (float)step["x"][1]) / 2; trap.dummyFeetY = gy; trap.dummyZ = -(float)dj["z"];
                d.transform.position = new Vector3(trap.dummyMarkX, feet + dh / 2, trap.dummyZ);
                d.SetActive(false); owner = trap;
            }
            else if (owner != null)
            {   // the other cans hit the same dummy; only the owner walks it (B)
                trap.dummy = owner.dummy; trap.dummyHeight = owner.dummyHeight; trap.dummyStartX = owner.dummyStartX; trap.climbSpeed = owner.climbSpeed;
                trap.dummyMarkX = owner.dummyMarkX; trap.dummyFeetY = owner.dummyFeetY; trap.dummyZ = owner.dummyZ; trap.climbKey = KeyCode.None;
            }
            foreach (var tr in rig.GetComponentsInChildren<Transform>(true)) tr.gameObject.layer = TrapLayer;
        }
    }

    // Batch physics test of the built rig (no play mode): -executeMethod SpecGreybox.TrapTest -> spec/captures/paint-can-test.txt,
    // the trajectory in ~/.cache/home-alone/paint-can-traj.csv and renders in spec/captures/views/traps/
    public static void TrapTest()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        var all = GameObject.Find("Upstairs/Traps").GetComponentsInChildren<PaintCanTrap>(true).OrderBy(q => q.name).ToArray();
        var mode = Physics.simulationMode; Physics.simulationMode = SimulationMode.Script;   // a project setting: restored below
        var rep = new StringBuilder(); var csv = new StringBuilder("can,test,t,x,y,z,speed,stretch,wrapped\n");
        try { foreach (var t in all) t.Setup(); for (int i = 0; i < all.Length; i++) TrapRun(all[i], all, rep, csv, i == 0); }
        finally { Physics.simulationMode = mode; }
        File.WriteAllText(Path.Combine(CaptureDir, "paint-can-test.txt"), rep.ToString());
        File.WriteAllText(Path.Combine(System.Environment.GetFolderPath(System.Environment.SpecialFolder.UserProfile), ".cache/home-alone/paint-can-traj.csv"), csv.ToString());
        Debug.Log("SpecGreybox.TrapTest\n" + rep);
    }
    // the tests for one can; the others hang at rest beside it and are simulated too (they can be knocked)
    static void TrapRun(PaintCanTrap trap, PaintCanTrap[] all, StringBuilder rep, StringBuilder csv, bool shared)
    {
        Physics.SyncTransforms();
        const float dt = 0.02f; const float g = 9.81f;
        var can = trap.can; float L = trap.ropeLength, Lc = L + trap.comBelowBail;
        rep.Append($"PAINT-CAN TRAP TEST {trap.name} (fixed dt {Time.fixedDeltaTime:F3} s, run at {dt}; solver {can.solverIterations}/{can.solverVelocityIterations}; {all.Length} cans)\n" +
            $"pivot {trap.pivot} rope {L:F3} m, pivot to can centre {Lc:F3} m, can {can.mass} kg, floor edge {trap.edge}\n");
        void ResetAll() { foreach (var t in all) t.ResetRig(); }
        float maxStretch = 0, maxSpeed = 0; bool nan = false;
        void Step(string test, float t)
        {
            foreach (var q in all) q.Tick(dt); Physics.Simulate(dt); foreach (var q in all) q.DrawRope(dt);
            var p = can.position; float lim = trap.wrapped ? L - Vector3.Distance(trap.pivot, new Vector3(trap.edge.x, trap.edge.y, trap.pivot.z)) : L;
            var anchor = trap.wrapped ? new Vector3(trap.edge.x, trap.edge.y, trap.pivot.z) : trap.pivot;
            float stretch = Vector3.Distance(anchor, p) - lim, v = can.linearVelocity.magnitude;
            maxStretch = Mathf.Max(maxStretch, stretch); maxSpeed = Mathf.Max(maxSpeed, v); nan |= float.IsNaN(p.x) || float.IsNaN(v);
            csv.AppendLine($"{trap.name},{test},{t:F2},{p.x:F4},{p.y:F4},{p.z:F4},{v:F3},{stretch:F4},{(trap.wrapped ? 1 : 0)}");
        }
        // energy per unit mass of the can's centre (potential from the bottom of the arc + kinetic)
        float E() => g * (can.worldCenterOfMass.y - (trap.pivot.y - Lc)) + 0.5f * can.linearVelocity.sqrMagnitude;

        // tests 1-3: this can alone (the other hangs only 2.5 cm away: a swing across the flight would hit it)
        foreach (var o in all) if (o != trap) o.can.gameObject.SetActive(false);
        // 1. at rest 10 s: no creep, no jitter
        ResetAll(); Physics.SyncTransforms(); var rest = can.position; float drift = 0, restV = 0;
        for (int i = 0; i < 500; i++) { Step("rest", i * dt); drift = Mathf.Max(drift, Vector3.Distance(can.position, rest)); restV = Mathf.Max(restV, can.linearVelocity.magnitude); }
        rep.AppendLine($"1 REST 10 s: max drift {drift * 1000:F2} mm, max speed {restV * 1000:F2} mm/s");

        // 2. small swing ACROSS the flight (along z: the rope stays clear of the floor edge), 10 deg: period vs the pendulum formula
        ResetAll(); trap.PullBack(10f, Vector3.back); trap.LetGo(); Physics.SyncTransforms();
        var cross = new System.Collections.Generic.List<float>(); float prevZ = can.position.z - rest.z, e0 = E(), eMax = e0;
        for (int i = 1; i <= 1000; i++)
        {
            Step("period", i * dt); float zz = can.position.z - rest.z, eNow = E(); eMax = Mathf.Max(eMax, eNow);
            if (prevZ < 0 && zz >= 0) cross.Add((i - 1 + -prevZ / (zz - prevZ)) * dt);
            prevZ = zz;
        }
        float T = cross.Count > 1 ? (cross[cross.Count - 1] - cross[0]) / (cross.Count - 1) : float.NaN, th = 10f * Mathf.Deg2Rad;
        float T0 = 2 * Mathf.PI * Mathf.Sqrt(Lc / g) * (1 + th * th / 16);
        rep.AppendLine($"2 PERIOD (10 deg across the flight, {cross.Count - 1} periods): {T:F3} s vs simple pendulum to the can's centre {T0:F3} s ({(T / T0 - 1) * 100:+0.0;-0.0}%); energy rise max {(eMax / e0 - 1) * 100:F2}%, after 20 s {(E() / e0 - 1) * 100:F1}%");

        // 3. the film's release: rope taut toward the landing, let go, no one on the stair
        ResetAll(); trap.PullBack(trap.releaseDeg, trap.swingDir); trap.LetGo(); Physics.SyncTransforms();
        float comDrop = can.worldCenterOfMass.y - (trap.pivot.y - Lc);   // held upright: the centre starts 0.175 m below the rope's line
        e0 = E(); eMax = e0; float tBottom = -1, vBottom = 0, uMax = -9, yMax = -9; bool wrappedEver = false; maxStretch = 0; maxSpeed = 0;
        for (int i = 1; i <= 400; i++)
        {
            float u0 = trap.pivot.x - can.position.x; Step("release", i * dt); float u1 = trap.pivot.x - can.position.x;
            eMax = Mathf.Max(eMax, E()); wrappedEver |= trap.wrapped;
            if (tBottom < 0 && u0 > 0 && u1 <= 0) { tBottom = (i - 1 + u0 / (u0 - u1)) * dt; vBottom = can.linearVelocity.magnitude; }
            if (tBottom > 0) { uMax = Mathf.Max(uMax, -u1); yMax = Mathf.Max(yMax, can.worldCenterOfMass.y); }
        }
        float a0 = trap.releaseDeg * Mathf.Deg2Rad, k = Mathf.Sin(a0 / 2), K = Mathf.PI / 2 * (1 + k * k / 4 + 9 * Mathf.Pow(k, 4) / 64 + 25 * Mathf.Pow(k, 6) / 256 + 1225 * Mathf.Pow(k, 8) / 16384);
        float tQ = Mathf.Sqrt(Lc / g) * K, vIdeal = Mathf.Sqrt(2 * g * comDrop);
        rep.AppendLine($"3 RELEASE {trap.releaseDeg:F0} deg toward the landing, stair empty: reaches the bottom in {tBottom:F3} s (pendulum quarter period {tQ:F3} s), " +
            $"{vBottom:F2} m/s there (free fall of its centre {comDrop:F3} m: {vIdeal:F2}; the rest spins the can on its bail); swings on {uMax:F2} m past the rail under the gallery, centre up to {yMax - trap.pivot.y:+0.00;-0.00} m vs the tie point; " +
            $"rope wrapped the floor edge: {wrappedEver}; max speed {maxSpeed:F2} m/s; energy never above start: {(eMax / e0 - 1) * 100:F2}%; max rope stretch {maxStretch * 1000:F1} mm; NaN {nan}");

        foreach (var o in all) o.can.gameObject.SetActive(true);
        // 4. the hit: P pulls every can back (as in Play), the dummy climbs from the foyer to the step under the rail, then THIS can is let go
        var walker = all.First(t => t.climbKey != KeyCode.None);   // the dummy's owner walks it
        ResetAll(); foreach (var o in all) o.PullBack(o.releaseDeg, o.swingDir); walker.StartClimb(); Physics.SyncTransforms();
        int n = 0; while (walker.Climbing && n < 1500) Step("climb", n++ * dt);
        var dpos = trap.dummy.position; float feetY = dpos.y - trap.dummyHeight / 2;
        rep.AppendLine($"4 HIT: dummy climbed {n * dt:F1} s to x {dpos.x:F3}, feet {feetY:F3} (ground +{feetY - trap.dummyFeetY:F3}), head top {feetY + trap.dummyHeight:F3}");
        var cam = new GameObject("TrapCam").AddComponent<Camera>(); cam.gameObject.AddComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>();
        var rt = new RenderTexture(1920, 1080, 24); cam.targetTexture = rt; cam.nearClipPlane = 0.05f; cam.fieldOfView = 60f;
        void View(string nm, Vector3 at, Vector3 look) { cam.transform.position = at; cam.transform.LookAt(look); cam.Render(); cam.Render(); Shot(cam, rt, "views/traps/" + nm); }
        var mid = new Vector3(trap.pivot.x - 0.4f, trap.pivot.y - Lc + 0.3f, trap.pivot.z);
        View($"held-dummy-side-{trap.name}", new Vector3(5.2f, -1.3f, -8.1f), mid);
        trap.LetGo(); float tHit = -1;
        for (int i = 1; i <= 150; i++)
        {
            Step("hit", i * dt);
            if (trap.lastHit != null && tHit < 0) { tHit = i * dt; View($"hit-side-{trap.name}", new Vector3(5.2f, -1.3f, -8.1f), mid); View($"hit-foyer-{trap.name}", new Vector3(7.9f, gyOf(trap) + 1.2f, -10.83f), mid); }
        }
        rep.AppendLine($"  {(trap.lastHit != null ? $"hit {tHit:F2} s after letting go: {trap.lastHit}" : "NO HIT")}");

        // 5. at rest for the stills: dangling from the rail (no dummy), from the foyer like film 10706 and from the side
        ResetAll(); float vAll = 0, tilt = 0;
        for (int i = 0; i < 250; i++) { Step("still", i * dt); foreach (var o in all) { vAll = Mathf.Max(vAll, o.can.linearVelocity.magnitude); tilt = Mathf.Max(tilt, Vector3.Angle(o.can.transform.up, Vector3.up)); } }
        rep.AppendLine($"5 BOTH AT REST 5 s after a reset: max speed of any can {vAll * 1000:F2} mm/s, max tilt {tilt:F2} deg");
        if (shared) View("dangling-foyer", new Vector3(7.9f, gyOf(trap) + 1.2f, -10.83f), trap.pivot + Vector3.down * 0.9f);
        if (shared) View("dangling-side", new Vector3(5.2f, -1.3f, -8.1f), trap.pivot + Vector3.down * 0.8f);
        {   // close-ups of the model (user, Oct 16: "have a bottom"): from below and from the side, 40 deg lens
            var cc0 = can.worldCenterOfMass; cam.fieldOfView = 40f;
            View($"closeup-below-{trap.name}", cc0 + new Vector3(0.25f, -0.45f, 0.2f), cc0); View($"closeup-side-{trap.name}", cc0 + new Vector3(0.45f, 0.12f, 0.15f), cc0 + Vector3.up * 0.04f);
            cam.fieldOfView = 60f;
        }

        if (!shared) { RenderTexture.active = null; rt.Release(); return; }
        // 6. the player (CharacterController, 1.85 m) walks up flight 1 through the hanging can: it must reach the landing
        var pl = GameObject.Find("Player").GetComponent<FpsController>(); var cc = pl.GetComponent<CharacterController>();   // the build names it Player
        pl.gameObject.SetActive(true); ResetAll();
        foreach (var t in all) foreach (var col in t.GetComponentsInChildren<Collider>(true)) Physics.IgnoreCollision(col, cc);
        // the walk line, between the two cans
        cc.enabled = false; pl.transform.position = new Vector3(7.3f, trap.dummyFeetY + 0.05f, trap.dummyZ); cc.enabled = true; Physics.SyncTransforms();
        float pushed = 0; int s = 0;
        for (; s < 600 && pl.transform.position.x > 3.1f; s++) { pl.TickMotion(Vector3.left, false, false, dt); Step("player", s * dt); pushed = Mathf.Max(pushed, all.Max(t => Vector3.Distance(t.can.position, t.pivot + Vector3.down * t.ropeLength))); }
        rep.AppendLine($"6 PLAYER up flight 1 between the hanging cans: reached x {pl.transform.position.x:F2} (landing edge 2.985) in {s * dt:F1} s at y {pl.transform.position.y:F2}; cans pushed up to {pushed:F2} m from rest");

        RenderTexture.active = null; rt.Release();
    }
    static float gyOf(PaintCanTrap t) => t.dummyFeetY;
}
