using UnityEngine;

/// Minimal first-person controller on the legacy input manager.
/// WASD move, mouse look, Shift sprint, Space jump, C crouch toggle, Esc releases cursor, click recaptures.
/// G toggles Kevin (kid body, the default in Play) / adult; H toggles the step bob.
[RequireComponent(typeof(CharacterController))]
public class FpsController : MonoBehaviour
{
    public Transform cam;
    public float walkSpeed = 3.5f, sprintSpeed = 6f, crouchSpeed = 1.9f;
    public float jumpSpeed = 4f, gravity = 15f, lookSensitivity = 2f;
    public float standHeight = 1.8f, crouchHeight = 1.2f, eyeOffset = 0.15f;
    // Kevin: eye ~1.10 m (STATUS "scale the players"; Marina's camera rides at 1.0-1.2 m), crawls under ~0.45 m. Speeds are a kid's walk/run.
    public bool kid = true;
    public float kidHeight = 1.30f, kidEye = 1.10f, kidCrouchHeight = 0.45f, kidRadius = 0.2f, kidWalk = 1.6f, kidSprint = 4f;
    // Step bob: one vertical dip per footfall, one side-to-side sway per two; strides in metres, amplitudes at walking pace.
    public bool headBob = true;
    public float kidStride = 0.65f, adultStride = 0.8f, bobHeight = 0.03f, bobSway = 0.015f;

    CharacterController cc;
    float pitch, vy;
    bool crouched;
    float adultRadius, adultWalk, adultSprint, bobPhase, bobWeight;
    Vector3 eyeRest;
    Vector3 spawnPosition;
    Quaternion spawnRotation;

    void Start()
    {
        spawnPosition = transform.position; spawnRotation = transform.rotation;
        cc = GetComponent<CharacterController>();
        adultRadius = cc.radius; adultWalk = walkSpeed; adultSprint = sprintSpeed;
        SetBody();
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Tab)) ReleaseMouse();   // Tab too: on macOS Esc was not always reaching the game (user, Oct 16)
        if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked) { Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false; }
        if (Input.GetKeyDown(KeyCode.C) || Input.GetKeyDown(KeyCode.LeftControl)) { crouched = !crouched; SetEye(); }
        if (Input.GetKeyDown(KeyCode.G)) { kid = !kid; SetBody(); }
        if (Input.GetKeyDown(KeyCode.H)) headBob = !headBob;
        if (Input.GetKeyDown(KeyCode.R)) { cc.enabled = false; transform.SetPositionAndRotation(spawnPosition, spawnRotation); cc.enabled = true; vy = 0; pitch = 0; }

        if (Cursor.lockState == CursorLockMode.Locked)
        {
            transform.Rotate(0, Input.GetAxis("Mouse X") * lookSensitivity, 0);
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * lookSensitivity, -85, 85);
            cam.localRotation = Quaternion.Euler(pitch, 0, 0);
        }

        TickMotion(transform.right * Input.GetAxisRaw("Horizontal") + transform.forward * Input.GetAxisRaw("Vertical"),
            Input.GetKey(KeyCode.LeftShift), Input.GetKeyDown(KeyCode.Space), Time.deltaTime);
        Bob(Time.deltaTime);
    }

    void Bob(float dt)
    {
        if (!cam) return;
        var v = cc.velocity; float speed = new Vector2(v.x, v.z).magnitude;
        bool stepping = headBob && cc.isGrounded && speed > 0.2f;
        bobWeight = Mathf.MoveTowards(bobWeight, stepping ? Mathf.Clamp(speed / walkSpeed, 0f, 1.4f) : 0f, dt * 4f);
        if (stepping) bobPhase += speed * dt / (kid ? kidStride : adultStride) * Mathf.PI;   // pi per step
        else if (bobWeight == 0f) bobPhase = 0f;
        cam.localPosition = eyeRest + new Vector3(Mathf.Sin(bobPhase) * bobSway, Mathf.Cos(2f * bobPhase) * bobHeight, 0) * bobWeight;
    }

    // Shared by keyboard input and the deterministic stair traversal check.
    public void TickMotion(Vector3 direction, bool sprint, bool jump, float dt)
    {
        if (!cc) cc = GetComponent<CharacterController>();
        float speed = crouched ? crouchSpeed : (sprint ? sprintSpeed : walkSpeed);
        Vector3 move = direction.normalized * speed;
        if (cc.isGrounded) { vy = -1f; if (jump && !crouched) vy = jumpSpeed; }
        else vy -= gravity * dt;
        move.y = vy;
        cc.Move(move * dt);
    }

    void SetBody()
    {
        cc.radius = kid ? kidRadius : adultRadius;
        walkSpeed = kid ? kidWalk : adultWalk; sprintSpeed = kid ? kidSprint : adultSprint;
        SetEye();
    }

    void SetEye()
    {
        float stand = kid ? kidHeight : standHeight, h = crouched ? (kid ? kidCrouchHeight : crouchHeight) : stand;
        float eye = h - (kid ? stand - kidEye : eyeOffset);
        cc.height = h; cc.center = new Vector3(0, h / 2, 0);
        eyeRest = new Vector3(0, eye, 0);
        if (cam) cam.localPosition = eyeRest;
    }

    static void ReleaseMouse() { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }

    // switching away from Unity (Cmd+Tab, clicking another app) always gives the mouse back; a click in the game view takes it again
    void OnApplicationFocus(bool focused) { if (!focused) ReleaseMouse(); }
}
