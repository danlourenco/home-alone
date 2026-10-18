using UnityEngine;

// Kevin's zipline from the attic dormer to the treehouse (film 10922-11064; changes/2026-10-18-treehouse-zipline.json), plus the
// treehouse ladder. SpecGreybox.Treehouse fills the fields from spec/dressing/treehouse.json (world coordinates).
//   E at the dormer, facing out (within attachRadius of the window): ride. Kid body: hands on the handlebar trolley, ~5 m/s with
//     easing; adult (G): hand over hand at ~1 m/s. You land standing on the deck landInside metres inside the rail.
//   E at the ladder's foot / at its head on the deck: climb up / down.
//   C within cutRadius of the trunk turns: cut the rope; it swings down from the window as a pendulum. E at the dormer re-ties it.
// The span is a parabola through the two anchors with mid-span sag (ponytail: close to a catenary at this sag/span, 0.5 / 15.5 m).
public class ZipLine : MonoBehaviour
{
    public Vector3 window, trunk, dormerOut = Vector3.left;
    public float sag = 0.5f, kidSpeed = 5f, adultSpeed = 1f, easeIn = 1.5f, easeOut = 2.5f, kidHang = 0.7f, adultHang = 0.5f;
    public float attachRadius = 1f, cutRadius = 1.5f, grade = -3.39f, wallAngle = 0.48f;
    public Vector3 landPoint, railPoint; public float landYaw;
    public Vector3 ladderBase, ladderHigh, ladderDeck;   // feet: standing at the foot, at the top rung, on the deck
    public Transform trolley; public GameObject rider;
    public Material ropeMat;

    enum Mode { Idle, Blend, Ride, Climb }
    Mode mode;
    FpsController fps; CharacterController cc; LineRenderer line;
    float[] arc = new float[65]; float len, s, sEnd, speed, hang, blendT, blendDur;
    Vector3 blendFrom, blendTo; System.Action blendDone;
    Vector3[] climb; float climbS;
    bool cut; float theta, omega;
    string hint;

    public Vector3 Rope(float t) => Vector3.Lerp(window, trunk, t) + Vector3.down * (4f * sag * t * (1f - t));

    float TAt(float dist)
    {
        for (int i = 1; i < arc.Length; i++)
            if (arc[i] >= dist) return (i - 1 + Mathf.InverseLerp(arc[i - 1], arc[i], dist)) / (arc.Length - 1);
        return 1f;
    }

    void Start()
    {
        for (int i = 1; i < arc.Length; i++) arc[i] = arc[i - 1] + Vector3.Distance(Rope((i - 1f) / (arc.Length - 1)), Rope((float)i / (arc.Length - 1)));
        len = arc[arc.Length - 1];
        // stop where the rope's plan position is 0.6 m short of the rail; the last bit is the landing blend
        Vector3 h = Flat(trunk - window).normalized; float dRail = Vector3.Dot(Flat(railPoint - window), h) - 0.6f;
        sEnd = arc[0]; for (int i = 0; i < arc.Length; i++) if (Vector3.Dot(Flat(Rope((float)i / (arc.Length - 1)) - window), h) <= dRail) sEnd = arc[i];
        line = gameObject.AddComponent<LineRenderer>(); line.widthMultiplier = 0.022f; line.sharedMaterial = ropeMat;
        line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On; line.numCapVertices = 2;
        DrawRope(); PlaceTrolley(0f);
        if (rider) rider.SetActive(false);
    }

    static Vector3 Flat(Vector3 v) => new Vector3(v.x, 0f, v.z);

    void Update()
    {
        if (!fps) { fps = FindFirstObjectByType<FpsController>(); if (fps) cc = fps.GetComponent<CharacterController>(); if (!fps) return; }
        var p = fps.transform; hint = null;
        switch (mode)
        {
            case Mode.Idle: Idle(p); break;
            case Mode.Blend:
                blendT += Time.deltaTime / blendDur; float k = Mathf.SmoothStep(0f, 1f, Mathf.Min(blendT, 1f));
                p.position = Vector3.Lerp(blendFrom, blendTo, k) + Vector3.up * (0.25f * Mathf.Sin(Mathf.PI * k) * (blendDur > 0.3f ? 1f : 0f));
                if (blendT >= 1f) blendDone();
                break;
            case Mode.Ride:
                float ease = Mathf.Clamp(Mathf.Min((s + 0.2f) / easeIn, (sEnd - s) / easeOut + 0.3f), 0.15f, 1f);
                s = Mathf.Min(s + speed * ease * Time.deltaTime, sEnd);
                PlaceTrolley(s);
                float bob = fps.kid ? 0f : 0.03f * Mathf.Sin(s / 0.35f * Mathf.PI);   // hand over hand
                p.position = Rope(TAt(s)) + Vector3.down * (hang + Eye() + bob);
                if (s >= sEnd) Blend(p.position, landPoint, 0.45f, () => { p.rotation = Quaternion.Euler(0f, landYaw, 0f); Release(); });
                break;
            case Mode.Climb:
                climbS += 0.6f * Time.deltaTime;   // m/s along the path
                p.position = Along(climb, climbS, out bool end);
                if (end) Release();
                break;
        }
        if (cut) Swing(Time.deltaTime);
    }

    float Eye() => fps.cam ? fps.cam.localPosition.y : 1.1f;

    void Idle(Transform p)
    {
        Vector3 fwd = Flat(p.forward).normalized;
        bool atWindow = Flat(window - p.position).magnitude < attachRadius && Mathf.Abs(p.position.y - (window.y - 1.5f)) < 1.2f;
        if (atWindow && Vector3.Dot(fwd, dormerOut) > 0.5f)
        {
            hint = cut ? "E: tie the rope again" : fps.kid ? "E: ride the zipline" : "E: go hand over hand";
            if (Input.GetKeyDown(KeyCode.E))
            {
                if (cut) { Tie(); return; }
                StartRide();
            }
            return;
        }
        if (Flat(ladderBase - p.position).magnitude < 0.8f && Mathf.Abs(p.position.y - ladderBase.y) < 0.6f)
        {
            hint = "E: climb the ladder";
            if (Input.GetKeyDown(KeyCode.E)) StartClimb(true);
            return;
        }
        if (Flat(ladderDeck - p.position).magnitude < 0.8f && Mathf.Abs(p.position.y - ladderDeck.y) < 0.6f)
        {
            hint = "E: climb down";
            if (Input.GetKeyDown(KeyCode.E)) StartClimb(false);
        }
        if (!cut && (trunk - (p.position + Vector3.up * Eye())).magnitude < cutRadius)
        {
            hint = (hint != null ? hint + "   " : "") + "C: cut the rope";
            if (Input.GetKeyDown(KeyCode.C)) Cut();
        }
    }

    // public for the walk test (live eval) as well as the E key
    public bool Busy => mode != Mode.Idle;
    public void StartRide()
    {
        var p = fps.transform; Freeze(); speed = fps.kid ? kidSpeed : adultSpeed; hang = fps.kid ? kidHang : adultHang; s = 0f; PlaceTrolley(0f);
        Blend(p.position, Rope(0f) + Vector3.down * (hang + Eye()), 0.3f, () => mode = Mode.Ride);
    }
    public void Tie() { cut = false; DrawRope(); PlaceTrolley(0f); }
    public void StartClimb(bool up)
    {
        var p = fps.transform; Freeze(); climbS = 0f; mode = Mode.Climb;
        climb = up ? new[] { p.position, ladderBase, ladderHigh, ladderDeck } : new[] { p.position, ladderDeck, ladderHigh, ladderBase };
    }

    void Blend(Vector3 from, Vector3 to, float dur, System.Action done) { blendFrom = from; blendTo = to; blendDur = dur; blendT = 0f; blendDone = done; mode = Mode.Blend; }

    void Freeze() { fps.frozen = true; if (cc) cc.enabled = false; }
    void Release() { mode = Mode.Idle; if (cc) cc.enabled = true; fps.frozen = false; }

    static Vector3 Along(Vector3[] pts, float d, out bool end)
    {
        for (int i = 1; i < pts.Length; i++)
        {
            float l = Vector3.Distance(pts[i - 1], pts[i]);
            if (d <= l) { end = false; return Vector3.Lerp(pts[i - 1], pts[i], l > 0f ? d / l : 1f); }
            d -= l;
        }
        end = true; return pts[pts.Length - 1];
    }

    void PlaceTrolley(float dist)
    {
        if (!trolley) return;
        float t = TAt(dist); Vector3 d = Flat(trunk - window).normalized;
        trolley.SetPositionAndRotation(Rope(t), Quaternion.LookRotation(d) * Quaternion.Euler(0f, 90f, 0f));
    }

    public void Cut()
    {
        cut = true; Vector3 r = trunk - window; Vector3 h = Flat(r);
        theta = Mathf.Atan2(h.magnitude, -r.y); omega = 0f;
        if (trolley && mode == Mode.Idle) trolley.position = new Vector3(trolley.position.x, grade + 0.05f, trolley.position.z);
    }

    // the cut rope: a pendulum from the window anchor in the vertical plane toward the trunk; it stops against the house (film 11228-11256:
    // the riders slam into the rear wall) at wallAngle from vertical, which keeps the straight rope clear of the eave and the rear wall
    // (ponytail: one straight segment, no draping over the roof), and whatever reaches the yard lies on the snow
    void Swing(float dt)
    {
        float L = Vector3.Distance(window, trunk);
        omega += (-(9.81f / L) * Mathf.Sin(theta) - 0.25f * omega) * dt; theta += omega * dt;
        if (theta < wallAngle) { theta = wallAngle; omega = -0.3f * omega; }
        Vector3 h = Flat(trunk - window).normalized, dir = h * Mathf.Sin(theta) + Vector3.down * Mathf.Cos(theta);
        float toGround = dir.y < -1e-3f ? (window.y - grade - 0.02f) / -dir.y : float.MaxValue;
        if (toGround >= L) { line.positionCount = 2; line.SetPosition(0, window); line.SetPosition(1, window + dir * L); }
        else { var hit = window + dir * toGround; line.positionCount = 3; line.SetPosition(0, window); line.SetPosition(1, hit); line.SetPosition(2, hit + h * (L - toGround)); }
    }

    void DrawRope()
    {
        line.positionCount = 41;
        for (int i = 0; i <= 40; i++) line.SetPosition(i, Rope(i / 40f));
    }

    void OnGUI()
    {
        if (hint == null) return;
        var st = new GUIStyle(GUI.skin.label) { fontSize = 18, alignment = TextAnchor.MiddleCenter }; st.normal.textColor = Color.white;
        GUI.Label(new Rect(0, Screen.height * 0.62f, Screen.width, 30), hint, st);
    }
}
