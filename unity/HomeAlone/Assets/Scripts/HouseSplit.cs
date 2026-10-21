using System.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// The split (DEVIATIONS 1, 97): the exterior is the film's house on the measured ground floor; Marina's upstairs is bigger and stands
// outside it. While the camera is upstairs (above switchY and inside the upstairs storey's envelope) the upstairs and attic are drawn
// whole and the skin's upper storey and roofs are hidden; everywhere else (outside, ground floor) the skin is drawn and the upstairs
// pieces that reach outside it are hidden. Renderers only: colliders never change. Play mode follows Camera.main; in the editor
// everything stays drawn (the bake and the gates see the whole house) except around a batch render (SpecGreybox.RenderViews: ApplyFor /
// RestoreAll).
// The envelope (walk note Oct 20 20:56, parents' doorway: roof, gutter and icicles inside the room, its ceiling gone): the upstairs ROOM
// outlines alone left every wall and doorway out, so standing in a doorway flipped the camera "outside". The test is now the whole
// storey: the room outlines plus the upstairs floor plate's rectangles (walls and thresholds included) and the attic; the first
// roomPolys polygons are the rooms (kept apart for SplitCheck's before/after). Hysteresis: once upstairs, the camera stays upstairs until
// it is 0.10 m below switchY or 0.25 m outside the envelope (no flicker at the stair head or with the walking bob).
// The APV scenario follows the split (BakeLighting): the upstairs is baked with Marina's overhang strip ("Default" / "Night"), the
// film's house (ground floor, outside) without it ("DayFilm" / "NightFilm"; walk note Oct 20 20:58: the strip's baked light darkened
// the front facade in overcast).
public class HouseSplit : MonoBehaviour
{
    public Renderer[] skinUpper = new Renderer[0];   // the skin's upper storey, main roofs, dormers, chimney, portico
    public Renderer[] insideOnly = new Renderer[0];  // upstairs/attic pieces reaching outside the skin
    // lamps standing in Marina's upstairs outside the skin (Oct 21, user: "a glow along the second floor ... light leaking from the
    // inside?": the hall bath's sconces stand 0.4-0.8 m in front of the film's upper wall). Dimmed to 0 while the film's house is drawn
    // (dimmers, not enabled: HouseNightMode switches lamps on and off); out of the film bakes (BakeLighting); SpecGreybox.LampSplitCheck
    public Light[] insideLights = new Light[0];
    public float switchY;
    public Vector2[] rooms = new Vector2[0];         // envelope polygons (world x, z), concatenated: rooms first, then floor plate and attic
    public int[] roomStarts = new int[0];
    public int roomPolys;                            // how many of the polygons are room outlines (the pre-Oct 20 test)
    public const float StayBelow = 0.10f, StayOutside = 0.25f;
    public static int State { get; private set; } = -1;   // 1 upstairs, 0 ground floor / outside, -1 all drawn (StoreyShadows, HouseNightMode)
    public static bool ForceUpstairsBake, LegacyRoomsOnly;   // PerfProbe A/B "before": the upstairs bake everywhere; the rooms-only test
    int state = -1;
    // A capture has its own viewpoint. Camera.main may still be downstairs/outside.
    public bool captureViewpoint = true;
    readonly System.Collections.Generic.Stack<int> captureStates = new();
    void OnEnable() { RenderPipelineManager.beginCameraRendering += BeginCapture; RenderPipelineManager.endCameraRendering += EndCapture; }
    void OnDisable() { RenderPipelineManager.beginCameraRendering -= BeginCapture; RenderPipelineManager.endCameraRendering -= EndCapture; }
    void BeginCapture(ScriptableRenderContext context, Camera camera) {
        if (!captureViewpoint || camera.name!="TmpCam") return;
        captureStates.Push(state); ApplyFor(camera.transform.position);
    }
    void EndCapture(ScriptableRenderContext context, Camera camera) {
        if (camera.name!="TmpCam" || captureStates.Count==0) return;
        Set(captureStates.Pop());
    }

    // inside any of the first `count` polygons (all when count < 0), or within `grow` metres of one
    public bool InEnvelope(Vector2 q, float grow = 0f, int count = -1)
    {
        int n = count < 0 ? roomStarts.Length : Mathf.Min(count, roomStarts.Length);
        for (int r = 0; r < n; r++)
        {
            int a = roomStarts[r], b = r + 1 < roomStarts.Length ? roomStarts[r + 1] : rooms.Length;
            bool c = false;
            for (int i = a, j = b - 1; i < b; j = i++)
            {
                if ((rooms[i].y > q.y) != (rooms[j].y > q.y) && q.x < (rooms[j].x - rooms[i].x) * (q.y - rooms[i].y) / (rooms[j].y - rooms[i].y) + rooms[i].x) c = !c;
                if (grow > 0f) { var e = rooms[i] - rooms[j]; float t = Mathf.Clamp01(Vector2.Dot(q - rooms[j], e) / Mathf.Max(e.sqrMagnitude, 1e-8f)); if ((rooms[j] + e * t - q).sqrMagnitude < grow * grow) return true; }
            }
            if (c) return true;
        }
        return false;
    }

    // stateless (captures, gates): the camera at p is upstairs
    // 2 cm of grow: a camera exactly on a wall's outer face or a plate edge is upstairs (SplitCheck: 1033 such samples on the first build)
    public bool Upstairs(Vector3 p) => p.y > switchY && (LegacyRoomsOnly ? InEnvelope(new Vector2(p.x, p.z), 0f, roomPolys) : InEnvelope(new Vector2(p.x, p.z), 0.02f));
    // with hysteresis, from the current state
    public bool Upstairs(Vector3 p, bool wasUpstairs) =>
        wasUpstairs && !LegacyRoomsOnly ? p.y > switchY - StayBelow && InEnvelope(new Vector2(p.x, p.z), StayOutside) : Upstairs(p);

    void Set(int s)
    {
        state = s; State = s;
        foreach (var r in skinUpper) if (r) r.enabled = s != 1;
        foreach (var r in insideOnly) if (r) r.enabled = s != 0;
        foreach (var l in insideLights)
            if (l && l.TryGetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>(out var hd))
            { float d = s != 0 ? 1f : 0f; hd.lightDimmer = d; hd.volumetricDimmer = d; hd.shadowDimmer = d; }
    }

    public void ApplyFor(Vector3 p) => Set(Upstairs(p) ? 1 : 0);
    public void RestoreAll() => Set(-1);

    // the baked bounce light for this storey and time of day; scenarios missing from the set (an older bake) fall back to Default/Night
    public static void ApplyScenario(bool night)
    {
        var apv = ProbeReferenceVolume.instance; var set = apv.currentBakingSet; if (set == null) return;
        string s = State == 0 && !ForceUpstairsBake ? (night ? "NightFilm" : "DayFilm") : night ? "Night" : "Default";
        if (!set.lightingScenarios.Contains(s)) s = night && set.lightingScenarios.Contains("Night") ? "Night" : "Default";
        if (apv.lightingScenario != s) apv.lightingScenario = s;
    }

    void LateUpdate()
    {
        if (!Application.isPlaying) return;
        var cam = Camera.main; if (cam == null) return;
        int s = Upstairs(cam.transform.position, state == 1) ? 1 : 0;
        if (s == state) return;
        Set(s);
        var nm = FindAnyObjectByType<HouseNightMode>(); ApplyScenario(nm != null && nm.night);
        ShadowRefresh.Forget();   // lamp shadow maps drawn with the other set hidden are redrawn when next in view
    }
}
