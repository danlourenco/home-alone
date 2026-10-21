using Unity.Collections;
using UnityEngine;

/// The paint-can trap (film 10700-10724): a full gallon can on a rope tied to the upstairs gallery rail, swung down flight 1 into
/// the face of someone climbing it. Built by SpecGreybox.Traps from spec/dressing/traps.json; design in docs/paint-can-trap.md.
///
/// Physics: the rope is ONE distance limit (ConfigurableJoint, all three linear axes Limited = a sphere of radius ropeLength
/// round the tie point): it goes slack but never stretches. A 5 kg can on a ~0.05 kg rope is a 100:1 mass ratio, the case a
/// chain of jointed rope bodies cannot hold stiff at 50 Hz; the rope's own mass changes the swing by under 1%. The rope you see
/// is a verlet line pinned to the tie point and the bail (visual only). When the can swings in under the gallery the rope wraps
/// the floor's edge: the limit moves to that edge with the rope that is left.
///
/// Keys (Play; per can from spec/dressing/traps.json): P pulls both cans back to the release pose and holds them, L lets go Marv's,
/// K lets go Harry's, B an adult test dummy (1.80 m) climbs flight 1 to the step under the rail, T reset (cans at rest, dummy gone). Impact speed, energy and height are logged to the console.
public class PaintCanTrap : MonoBehaviour
{
    // OFF for now (user, Oct 20: "we can also disable the paint cans for the time being"; their pull key P also clashed with the render
    // scale's P). Play hides the whole Upstairs/Traps rig; the editor's batch gates (TrapTest, MotionShadow) and the perf tour's motion
    // step (-perfprobe) still run it. Turn back on: Enabled = true, or launch the app with -traps.
    public static bool Enabled = false;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Gate()
    {
        var a = System.Environment.GetCommandLineArgs();
        if (Enabled || System.Array.IndexOf(a, "-traps") >= 0 || System.Array.IndexOf(a, "-perfprobe") >= 0) return;
        var t = GameObject.Find("Upstairs/Traps"); if (t) t.SetActive(false);
    }

    public Rigidbody can;                  // origin = the bail's apex, where the rope is tied
    public LineRenderer rope;
    public Vector3 knot, pivot, edge;      // knot on the handrail; where the rope leaves the rail; the gallery floor's lower edge
    public float ropeLength, releaseDeg = 90f, comBelowBail, canRadius = 0.11f;
    public Vector3 swingDir = Vector3.left;   // horizontal, from the rail toward the landing
    public Rigidbody dummy; public float dummyHeight = 1.8f, dummyStartX, dummyMarkX, dummyFeetY, dummyZ, climbSpeed = 0.6f;   // one dummy, shared; only its owner has a climbKey
    public KeyCode pullKey = KeyCode.P, letGoKey = KeyCode.L, climbKey = KeyCode.B, resetKey = KeyCode.T;

    [System.NonSerialized] public string lastHit;   // read by the batch test (SpecGreybox.TrapTest)
    [System.NonSerialized] public bool wrapped;
    ConfigurableJoint joint; bool held, climbing, hit;
    Vector3 lastVel, lastPlayer; Vector3[] pts, prev; CharacterController player; Collider canCol, dummyCol;
    const int N = 24;

    void Awake() => Setup();
    void OnDestroy() => Physics.ContactEvent -= OnContacts;
    void Update()
    {
        if (Input.GetKeyDown(pullKey)) PullBack(releaseDeg, swingDir);
        if (Input.GetKeyDown(letGoKey)) LetGo();
        if (Input.GetKeyDown(climbKey)) StartClimb();
        if (Input.GetKeyDown(resetKey)) ResetRig();
        ShadowTick();
    }
    // the lamps' cached shadow maps redraw while the can (and its rope) or the dummy moves (ShadowRefresh queues and throttles them)
    public bool ShadowTick()
    {
        bool moved = false;
        if (can && (can.position - lastShadowAt).sqrMagnitude > 1e-6f) { moved = true; lastShadowAt = can.position; var b = new Bounds(can.position, Vector3.one * 0.3f); b.Encapsulate(knot); ShadowRefresh.Near(b); }
        if (dummy && dummy.gameObject.activeInHierarchy && (dummy.position - lastDummyAt).sqrMagnitude > 1e-6f) { moved = true; lastDummyAt = dummy.position; ShadowRefresh.Near(new Bounds(dummy.position, new Vector3(0.6f, dummyHeight, 0.6f))); }
        if (moved) lastMoveFrame = Time.frameCount;
        return moved;
    }
    int lastMoveFrame = -10;
    public bool Moving => Time.frameCount - lastMoveFrame <= 1;   // moved (> 1 mm) this frame or the last (PerfProbe's motion step)
    Vector3 lastShadowAt, lastDummyAt;
    void FixedUpdate() => Tick(Time.fixedDeltaTime);
    void LateUpdate() => DrawRope(Time.deltaTime);

    public void Setup()
    {
        if (joint) return;
        joint = can.gameObject.AddComponent<ConfigurableJoint>();
        joint.autoConfigureConnectedAnchor = false; joint.anchor = Vector3.zero; joint.connectedAnchor = pivot;   // no body: world point
        joint.xMotion = joint.yMotion = joint.zMotion = ConfigurableJointMotion.Limited;
        joint.angularXMotion = joint.angularYMotion = joint.angularZMotion = ConfigurableJointMotion.Free;
        joint.linearLimit = new SoftJointLimit { limit = ropeLength, bounciness = 0f, contactDistance = 0f };   // hard: no spring
        joint.enablePreprocessing = false;
        can.solverIterations = 12; can.solverVelocityIterations = 4; can.maxAngularVelocity = 50f;   // runtime-only properties (not saved)
        canCol = can.GetComponentInChildren<Collider>(); canCol.providesContacts = true;
        if (dummy) dummyCol = dummy.GetComponent<Collider>();
        Physics.ContactEvent += OnContacts;
        var fps = FindAnyObjectByType<FpsController>(); player = fps ? fps.GetComponent<CharacterController>() : null;   // the player, not any controller
        if (player) foreach (var c in GetComponentsInChildren<Collider>(true)) Physics.IgnoreCollision(c, player);   // pushed by hand instead (PushByPlayer)
    }

    public void ResetRig()
    {
        held = climbing = hit = false; SetWrapped(false); lastHit = null; pts = null;
        can.isKinematic = false; Place(pivot + Vector3.down * ropeLength);
        can.linearVelocity = can.angularVelocity = Vector3.zero;
        if (dummy) dummy.gameObject.SetActive(false);
    }

    // held upright by hand with the rope taut at `deg` from hanging, toward `dir` (the release pose)
    public void PullBack(float deg, Vector3 dir)
    {
        hit = false; lastHit = null; SetWrapped(false); held = true; pts = null;
        float a = deg * Mathf.Deg2Rad;
        can.isKinematic = true; Place(pivot + (Mathf.Sin(a) * dir.normalized + Mathf.Cos(a) * Vector3.down) * ropeLength);
    }

    public void LetGo()
    {
        if (!held) return;
        held = false; can.isKinematic = false; can.linearVelocity = can.angularVelocity = Vector3.zero;
        float h = Vector3.Dot(pivot - can.position, Vector3.up) + ropeLength;   // drop of the bail to the bottom of the arc
        Debug.Log($"PaintCanTrap: let go, {h:F2} m above the bottom of the arc: ideal speed there {Mathf.Sqrt(2 * 9.81f * h):F2} m/s");
    }

    public void StartClimb()
    {
        if (!dummy) return;
        hit = false; lastHit = null; dummy.gameObject.SetActive(true);
        var p = new Vector3(dummyStartX, dummyFeetY + dummyHeight / 2, dummyZ);
        dummy.position = p; dummy.transform.position = p; climbing = true;
    }
    public bool Climbing => climbing;

    void Place(Vector3 p) { can.position = p; can.rotation = Quaternion.identity; can.transform.SetPositionAndRotation(p, Quaternion.identity); }

    public void Tick(float dt)
    {
        // the rope wraps the gallery floor's edge once the bail swings in under it (horizontal u: toward the gallery)
        Vector3 back = -swingDir.normalized, a = edge - pivot, b = can.position - pivot;
        bool under = Vector3.Dot(a, back) * b.y - a.y * Vector3.Dot(b, back) > 0f && can.position.y < edge.y;
        if (under != wrapped && !held) SetWrapped(under);
        if (climbing && dummy)
        {   // up the flight at climbSpeed, feet on whatever tread is under the body's axis (the rig itself is on Ignore Raycast)
            var p = dummy.position; float x = Mathf.MoveTowards(p.x, dummyMarkX, climbSpeed * dt), feet = p.y - dummyHeight / 2;
            if (Physics.Raycast(new Vector3(x, feet + 0.9f, p.z), Vector3.down, out var rh, 2f, ~(1 << 2), QueryTriggerInteraction.Ignore)) feet = rh.point.y;
            dummy.MovePosition(new Vector3(x, feet + dummyHeight / 2, p.z));
            if (x == dummyMarkX) climbing = false;
        }
        PushByPlayer(dt);
        // a real can on a rope settles (rail friction, air): damp it only while slow, so a nudge dies out and the body sleeps, while a
        // released trap (past 0.5 m/s within ~0.05 s, ~4 m/s at the hit) swings undamped. Undamped, an idle can swung forever and
        // redrew every nearby lamp's shadow map each frame (night, Oct 17: 209M -> 2.1M triangles, GPU 254 -> 45 ms with it still)
        can.linearDamping = can.linearVelocity.sqrMagnitude < 0.25f ? 1.5f : 0f;
        lastVel = can.linearVelocity;
        // at rest: below ~1 cm of swing left (energy per kg of the bail over the bottom of its arc < 2e-4 J: 0.02 mm of rise), stop it
        // dead and let it sleep. Damping alone only approaches rest, and each 1 mm move queued the lamps' shadow maps again (Oct 20)
        if (!held && !wrapped && !climbing && !can.isKinematic && !can.IsSleeping())
        {
            float rise = can.position.y - (pivot.y - ropeLength), e = 9.81f * Mathf.Max(rise, 0f) + 0.5f * can.linearVelocity.sqrMagnitude;
            if (e < 2e-4f && can.angularVelocity.sqrMagnitude < 0.04f) { can.linearVelocity = can.angularVelocity = Vector3.zero; can.Sleep(); }
        }
    }

    void SetWrapped(bool w)
    {
        wrapped = w; if (!joint) return;
        var e = new Vector3(edge.x, edge.y, pivot.z);
        joint.connectedAnchor = w ? e : pivot;
        joint.linearLimit = new SoftJointLimit { limit = w ? ropeLength - Vector3.Distance(pivot, e) : ropeLength };
    }

    // the player is a CharacterController (no rigidbody): it ignores the rig's colliders and shoves the can at its own speed instead,
    // so a hanging can never stops anyone on the stair
    void PushByPlayer(float dt)
    {
        if (!player || !player.enabled) return;
        var t = player.transform; float r = player.radius;
        var vp = (t.position - lastPlayer) / dt; lastPlayer = t.position;   // CharacterController.velocity is not kept outside Play
        if (held || can.isKinematic || vp.sqrMagnitude > 100f) return;     // > 10 m/s: a respawn, not a walk
        Vector3 lo = t.position + Vector3.up * r, hi = t.position + Vector3.up * (player.height - r), c = can.worldCenterOfMass;
        var q = lo + Vector3.Project(c - lo, hi - lo); q.y = Mathf.Clamp(q.y, lo.y, hi.y);
        var d = c - q; if (d.magnitude > r + canRadius || d.sqrMagnitude < 1e-8f) return;
        var n = d.normalized; float v = Vector3.Dot(vp - can.linearVelocity, n);
        if (v > 0f) can.AddForce(n * v, ForceMode.VelocityChange);
    }

    void OnContacts(PhysicsScene scene, NativeArray<ContactPairHeader>.ReadOnly headers)
    {
        if (hit || !dummyCol || !dummy.gameObject.activeInHierarchy) return;
        foreach (var h in headers)
            for (int i = 0; i < h.pairCount; i++)
            {
                ref readonly var p = ref h.GetContactPair(i);
                if (!((p.collider == canCol && p.otherCollider == dummyCol) || (p.collider == dummyCol && p.otherCollider == canCol)) || p.contactCount == 0) continue;
                var at = Vector3.zero; for (int k = 0; k < p.contactCount; k++) at += p.GetContactPoint(k).position; at /= p.contactCount;
                float above = at.y - (dummy.position.y - dummyHeight / 2), v = (lastVel - dummy.linearVelocity).magnitude, m = can.mass;
                hit = true; climbing = false;
                lastHit = $"{(above >= 1.5f ? "HEAD" : "BODY")} {above:F2} m above the feet; can {v:F2} m/s ({v * 3.6f:F1} km/h), {0.5f * m * v * v:F0} J, impulse {p.impulseSum.magnitude:F1} N s";
                Debug.Log($"PaintCanTrap {name}: hit " + lastHit);
                return;
            }
    }

    public void DrawRope(float dt)
    {
        if (!rope) return;
        Vector3 b = can.position;
        if (wrapped) { rope.positionCount = 4; rope.SetPositions(new[] { knot, pivot, new Vector3(edge.x, edge.y, pivot.z), b }); pts = null; return; }
        if (pts == null) { pts = new Vector3[N + 1]; prev = new Vector3[N + 1]; for (int i = 0; i <= N; i++) pts[i] = prev[i] = Vector3.Lerp(pivot, b, i / (float)N); }
        if (Vector3.Distance(pivot, b) > 0.98f * ropeLength) for (int i = 0; i <= N; i++) pts[i] = prev[i] = Vector3.Lerp(pivot, b, i / (float)N);   // taut
        else
        {   // slack: verlet, ends pinned, each segment held to its length
            float seg = ropeLength / N;
            for (int i = 1; i < N; i++) { var v = (pts[i] - prev[i]) * 0.98f; prev[i] = pts[i]; pts[i] += v + Physics.gravity * dt * dt; }
            pts[0] = pivot; pts[N] = b;
            for (int k = 0; k < 20; k++)
                for (int i = 0; i < N; i++)
                {
                    var d = pts[i + 1] - pts[i]; float len = d.magnitude; if (len < 1e-6f) continue;
                    var corr = d * ((len - seg) / len);
                    if (i == 0) pts[1] -= corr; else if (i + 1 == N) pts[i] += corr; else { pts[i] += corr * 0.5f; pts[i + 1] -= corr * 0.5f; }
                }
        }
        rope.positionCount = N + 2; rope.SetPosition(0, knot); for (int i = 0; i <= N; i++) rope.SetPosition(i + 1, pts[i]);
    }
}
