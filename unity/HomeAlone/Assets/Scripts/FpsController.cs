using UnityEngine;

/// Minimal first-person controller on the legacy input manager.
/// WASD move, mouse look, Shift sprint, Space jump, HOLD C or Left Ctrl to crouch/crawl (can't stand under a low ceiling),
/// Esc/Tab releases cursor, click recaptures, R resets. G toggles Kevin (kid body, the default in Play) / adult;
/// H toggles the step bob + landing dip (motion-sickness switch). Footsteps are OFF by default (user Oct 19).
/// E interacts (each prompts on screen when you are close and looking at it): the front door opens/closes; the den movie chair sits/stands; Buzz's footlocker opens/closes (TrunkLid, within 1.5 m);
/// at the attic dormer rides the zipline, at the treehouse ladder climbs (ZipLine). N day/night, O cycles the day's weather sunny (film 4382, the default) / morning (film 1890) / overcast (film 6399) (HouseWeather;
/// it also drives the falling snow: off in sunny/morning, where F is ignored; on when overcast and at night),
/// M marks a walk note (FeelNotes). K hides everything off the McCallister lot (PropertyView). [ ] night white balance (HouseNightMode),
/// P cycles the render scale 100/75/50/38% (RenderScale: STP upscaling, for big full-screen windows). Music (BackgroundMusic): J pause, - / = volume, U track.
/// Footsteps by floor surface: Surface is read from the material/collider name under the feet (SurfaceFor); clips are Kenney Impact Sounds (CC0).
[RequireComponent(typeof(CharacterController))]
public class FpsController : MonoBehaviour
{
    public Transform cam;
    public float walkSpeed = 3.5f, sprintSpeed = 6f, crouchSpeed = 1.9f;
    public float jumpSpeed = 4f, gravity = 15f, lookSensitivity = 2f;
    public float standHeight = 1.8f, crouchHeight = 1.2f, eyeOffset = 0.15f;
    // Kevin: eye ~1.10 m (STATUS "scale the players"; Marina's camera rides at 1.0-1.2 m), crawls under ~0.45 m. Speeds are a kid's walk/run.
    public bool kid = true;
    public bool frozen;   // set by scripted moves (ZipLine: riding, climbing): look still works, walking and bob pause
    public float kidHeight = 1.30f, kidEye = 1.10f, kidCrouchHeight = 0.45f, kidRadius = 0.2f, kidWalk = 1.6f, kidSprint = 4f, kidCrouchSpeed = 0.9f;
    // Crouched, the eye rides 5 cm under the capsule top (kid: 0.40 m, under the 0.48 m bed rails; the capsule is the 0.45 m crouch of DEVIATIONS 72/81).
    public float crouchEyeDrop = 0.05f;
    // Step bob: one vertical dip per footfall, one side-to-side sway per two; strides in metres, amplitudes (half peak-to-peak) at walking pace.
    // Kid: short quick stride, ~1.8 cm bounce. Adult: longer slower stride, heavier ~3 cm.
    public bool headBob = true;
    public float kidStride = 0.65f, adultStride = 0.8f, kidBobAmp = 0.009f, adultBobAmp = 0.015f, kidSwayAmp = 0.006f, adultSwayAmp = 0.011f;
    // Footsteps: Kevin is light and quiet, the bandit heavy and low.
    public bool footsteps = false;   // off by default (user, Oct 19: "the walking noise sucks, we should lose it"); the code stays for better clips
    public float kidStepVolume = 0.35f, adultStepVolume = 0.75f;

    CharacterController cc;
    float pitch, vy;
    bool crouched;
    float adultRadius, adultWalk, adultSprint, adultCrouch, bobPhase, bobWeight;
    float curH, curEye, targetH, targetEye, landDip, stepDist;
    bool wasGrounded = true;
    // Below the basement/areaway: emergency recovery, never a substitute for ground collision.
    public float fallRecoveryY = -12f;
    Vector3 safePosition;
    Quaternion safeRotation;
    float safeSampleTimer;
    AudioSource audioSrc;
    static AudioClip[][] clips;
    int lastClip = -1;
    Vector3 eyeRest;
    Vector3 spawnPosition;
    Quaternion spawnRotation;

    void Start()
    {
        spawnPosition = transform.position; spawnRotation = transform.rotation;
        safePosition = spawnPosition + Vector3.up*.05f; safeRotation = spawnRotation;
        cc = GetComponent<CharacterController>();
        adultRadius = cc.radius; adultWalk = walkSpeed; adultSprint = sprintSpeed; adultCrouch = crouchSpeed;
        audioSrc = gameObject.AddComponent<AudioSource>(); audioSrc.spatialBlend = 0; audioSrc.playOnAwake = false;
        SetBody(); curH = targetH; curEye = targetEye; ApplyHeight();
        SelfCheck();
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Tab)) ReleaseMouse();   // Tab too: on macOS Esc was not always reaching the game (user, Oct 16)
        if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked) { Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false; }
        bool wantCrouch = Input.GetKey(KeyCode.C) || Input.GetKey(KeyCode.LeftControl);
        if (wantCrouch != crouched && (wantCrouch || !HeadBlocked())) { crouched = wantCrouch; SetEye(); }
        if (Input.GetKeyDown(KeyCode.G)) { kid = !kid; SetBody(); curH = targetH; curEye = targetEye; ApplyHeight(); }
        if (curH != targetH || curEye != targetEye)   // ease the crouch/stand so it reads as a duck, not a teleport
        {
            curH = Mathf.MoveTowards(curH, targetH, Time.deltaTime * 2.5f); curEye = Mathf.MoveTowards(curEye, targetEye, Time.deltaTime * 2.5f); ApplyHeight();
        }
        if (Input.GetKeyDown(KeyCode.H)) headBob = !headBob;
        if (Input.GetKeyDown(KeyCode.F) && cam.Find("Snowfall") is Transform sf) sf.gameObject.SetActive(!sf.gameObject.activeSelf);   // falling snow on/off (SpecGreybox.ExteriorRealism)
        if (Input.GetKeyDown(KeyCode.R)) { cc.enabled = false; transform.SetPositionAndRotation(spawnPosition, spawnRotation); cc.enabled = true; vy = 0; pitch = 0; }

        if (Cursor.lockState == CursorLockMode.Locked)
        {
            transform.Rotate(0, Input.GetAxis("Mouse X") * lookSensitivity, 0);
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * lookSensitivity, -85, 85);
            cam.localRotation = Quaternion.Euler(pitch, 0, 0);
        }

        if (frozen) return;
        TickMotion(transform.right * Input.GetAxisRaw("Horizontal") + transform.forward * Input.GetAxisRaw("Vertical"),
            Input.GetKey(KeyCode.LeftShift), Input.GetKeyDown(KeyCode.Space), Time.deltaTime);
        Bob(Time.deltaTime);
    }

    void Bob(float dt)
    {
        if (!cam) return;
        var v = cc.velocity; float speed = new Vector2(v.x, v.z).magnitude;
        bool grounded = cc.isGrounded;
        if (grounded && !wasGrounded && vy < -1.8f)   // touched down: dip the eye (a step off the last stair ~1-2 cm, a jump ~5 cm) and thud
        {
            if (headBob) landDip = Mathf.Min(0.06f, (-vy - 1f) * 0.015f) * (kid ? 1f : 1.3f);
            Footstep(1.4f);
        }
        wasGrounded = grounded;
        landDip *= Mathf.Exp(-9f * dt);
        bool stepping = grounded && speed > 0.2f;
        float stride = (kid ? kidStride : adultStride) * (crouched ? 0.6f : 1f);
        if (stepping)
        {
            stepDist += speed * dt;
            if (stepDist >= stride) { stepDist -= stride; Footstep(Input.GetKey(KeyCode.LeftShift) && !crouched ? 1.25f : 1f); }
        }
        else stepDist = stride * 0.5f;   // first footfall half a stride after starting, in step with the bob's first dip
        bool bob = headBob && stepping;
        bobWeight = Mathf.MoveTowards(bobWeight, bob ? Mathf.Clamp(speed / walkSpeed, 0f, 1.4f) * (crouched ? 0.5f : 1f) : 0f, dt * 4f);
        if (bob) bobPhase += speed * dt / stride * Mathf.PI;   // pi per step
        else if (bobWeight == 0f) bobPhase = 0f;
        float amp = kid ? kidBobAmp : adultBobAmp, sway = kid ? kidSwayAmp : adultSwayAmp;
        cam.localPosition = eyeRest + new Vector3(Mathf.Sin(bobPhase) * sway, Mathf.Cos(2f * bobPhase) * amp, 0) * bobWeight - Vector3.up * landDip;
    }

    // ---- footsteps ----
    public enum Surface { Wood, Carpet, Stair, Tile, BathTile, Concrete, Snow }
    static readonly string[] clipPrefix = { "footstep_wood", "footstep_carpet", "stair", "tile", "tile", "footstep_concrete", "footstep_snow" };

    /// Pure name->surface table (see SelfCheck). name = collider name, path = its parent chain, mat = material name; all case-insensitive.
    public static Surface SurfaceFor(string name, string path, string mat)
    {
        string n = (name ?? "").ToLowerInvariant(), p = (path ?? "").ToLowerInvariant(), m = (mat ?? "").ToLowerInvariant();
        if (n.StartsWith("flight") || n.StartsWith("service_") || n.Contains("step") || n.Contains("tread") || m.Contains("stair") || m.Contains("tread")) return Surface.Stair;
        if (m.Contains("snow") || m.Contains("yard")) return Surface.Snow;
        if (m.Contains("rug") || m.Contains("runner") || m.Contains("carpet") || m.Contains("mat") && !m.Contains("material") || m.Contains("fringe")) return Surface.Carpet;
        if (m.Contains("tile_quarry") || m.Contains("kitchentile") || m.Contains("kitchengrout")) return Surface.Tile;
        if (p.Contains("ensuite") || p.Contains("bath") || m.Contains("bath")) return Surface.BathTile;
        if (m.Contains("basement") || m.Contains("concrete") || m.Contains("areaway") || p.Contains("basement")) return Surface.Concrete;
        return Surface.Wood;
    }

    Surface SurfaceUnderfoot()
    {
        if (!Physics.Raycast(transform.position + Vector3.up * 0.1f, Vector3.down, out var hit, 0.6f, ~0, QueryTriggerInteraction.Ignore)) return Surface.Wood;
        var t = hit.collider.transform; string path = t.name;
        for (var q = t.parent; q != null && path.Length < 120; q = q.parent) path = q.name + "/" + path;
        var r = hit.collider.GetComponent<Renderer>() ?? hit.collider.GetComponentInParent<Renderer>();
        var best = Surface.Wood; bool first = true;
        if (r) foreach (var mt in r.sharedMaterials)   // multi-material mesh: first material that is not plain wood
        {
            if (!mt) continue;
            var s = SurfaceFor(t.name, path, mt.name);
            if (first || best == Surface.Wood) best = s; first = false;
        }
        else best = SurfaceFor(t.name, path, "");
        return best;
    }

    void Footstep(float gain)
    {
        if (!footsteps || !audioSrc) return;
        if (clips == null)
        {
            var all = Resources.LoadAll<AudioClip>("Footsteps");
            clips = new AudioClip[clipPrefix.Length][];
            for (int i = 0; i < clips.Length; i++) clips[i] = System.Array.FindAll(all, c => c.name.StartsWith(clipPrefix[i]));
        }
        var surf = SurfaceUnderfoot(); var set = clips[(int)surf];
        if (set == null || set.Length == 0) return;
        int k = Random.Range(0, set.Length); if (k == lastClip && set.Length > 1) k = (k + 1) % set.Length; lastClip = k;
        audioSrc.pitch = (kid ? 1.12f : 0.85f) * (surf == Surface.BathTile ? 1.1f : 1f) * Random.Range(0.93f, 1.07f);
        float vol = (kid ? kidStepVolume : adultStepVolume) * gain * (crouched ? 0.4f : 1f) * Random.Range(0.85f, 1f);
        audioSrc.PlayOneShot(set[k], vol);
    }

    bool HeadBlocked()
    {
        float need = (kid ? kidHeight : standHeight) - curH, r = cc.radius * 0.9f;
        return need > 0.001f && Physics.SphereCast(transform.position + Vector3.up * (curH - r), r, Vector3.up, out _, need + 0.02f, ~0, QueryTriggerInteraction.Ignore);
    }

    static void SelfCheck()
    {
        Debug.Assert(SurfaceFor("Floor", "Ground/Floor", "HiFi_Runner") == Surface.Carpet);
        Debug.Assert(SurfaceFor("Floor", "Ground/Floor", "Tile_Quarry") == Surface.Tile);
        Debug.Assert(SurfaceFor("flight1_step03", "Stair/flight1_step03", "Wood_StairDark") == Surface.Stair);
        Debug.Assert(SurfaceFor("Floor", "Basement/Floor", "HiFi_BasementSlab") == Surface.Concrete);
        Debug.Assert(SurfaceFor("Floor", "Upstairs/ensuite/Floor", "Floor") == Surface.BathTile);
        Debug.Assert(SurfaceFor("Ground", "Yard/Ground", "Snow") == Surface.Snow);
        Debug.Assert(SurfaceFor("Floor", "Ground/Floor", "Floor") == Surface.Wood);
        Debug.Assert(SurfaceFor(null, null, null) == Surface.Wood);
    }

    // Shared by keyboard input and the deterministic stair traversal check.
    public void TickMotion(Vector3 direction, bool sprint, bool jump, float dt)
    {
        if (!cc) cc = GetComponent<CharacterController>();
        if (RecoverIfFallen()) return;
        safeSampleTimer -= dt;
        if (cc.isGrounded && safeSampleTimer <= 0f) {
            safeSampleTimer = .25f;
            if (SupportedFootprint()) { safePosition=transform.position+Vector3.up*.05f; safeRotation=transform.rotation; }
        }
        float speed = crouched ? crouchSpeed : (sprint ? sprintSpeed : walkSpeed);
        Vector3 move = direction.normalized * speed;
        if (cc.isGrounded) { vy = -1f; if (jump && !crouched) vy = jumpSpeed; }
        else vy -= gravity * dt;
        move.y = vy;
        cc.Move(move * dt);
        RecoverIfFallen();
    }

    bool SupportedFootprint()
    {
        // Keep the last stable location away from ledges: centre and four points inside the capsule footprint.
        float radius=cc.radius*.7f, minUp=Mathf.Cos(cc.slopeLimit*Mathf.Deg2Rad);
        for (int i=0;i<5;i++) {
            Vector3 offset=i==0?Vector3.zero:i==1?Vector3.right*radius:i==2?Vector3.left*radius:i==3?Vector3.forward*radius:Vector3.back*radius;
            if (!Physics.Raycast(transform.position+offset+Vector3.up*.1f,Vector3.down,out var hit,.3f,~0,QueryTriggerInteraction.Ignore)
                || hit.normal.y<minUp || hit.collider.attachedRigidbody && !hit.collider.attachedRigidbody.isKinematic) return false;
        }
        return true;
    }

    public bool RecoverIfFallen()
    {
        if (transform.position.y>=fallRecoveryY) return false;
        if (!cc) cc=GetComponent<CharacterController>();
        bool enabled=cc.enabled;cc.enabled=false;
        transform.SetPositionAndRotation(safePosition,safeRotation);vy=0;landDip=0;bobWeight=0;wasGrounded=true;
        cc.enabled=enabled;
        Debug.LogWarning("Fall recovery: returned to last supported position; report the missing ground collision.");
        return true;
    }

    void SetBody()
    {
        cc.radius = kid ? kidRadius : adultRadius;
        walkSpeed = kid ? kidWalk : adultWalk; sprintSpeed = kid ? kidSprint : adultSprint; crouchSpeed = kid ? kidCrouchSpeed : adultCrouch;
        SetEye();
    }

    // Sets the targets; Update eases curH/curEye toward them (SetBody snaps).
    void SetEye()
    {
        float stand = kid ? kidHeight : standHeight;
        targetH = crouched ? (kid ? kidCrouchHeight : crouchHeight) : stand;
        targetEye = crouched ? targetH - crouchEyeDrop : stand - (kid ? stand - kidEye : eyeOffset);
    }

    void ApplyHeight()
    {
        cc.height = curH; cc.center = new Vector3(0, curH / 2, 0);
        eyeRest = new Vector3(0, curEye, 0);
        if (cam) cam.localPosition = eyeRest;
    }

    static void ReleaseMouse() { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }

    // switching away from Unity (Cmd+Tab, clicking another app) always gives the mouse back; a click in the game view takes it again
    void OnApplicationFocus(bool focused) { if (!focused) ReleaseMouse(); }
}
