using UnityEngine;

/// Minimal first-person controller on the legacy input manager.
/// WASD move, mouse look, Shift sprint, Space jump, C crouch toggle, Esc releases cursor, click recaptures.
[RequireComponent(typeof(CharacterController))]
public class FpsController : MonoBehaviour
{
    public Transform cam;
    public float walkSpeed = 3.5f, sprintSpeed = 6f, crouchSpeed = 1.9f;
    public float jumpSpeed = 4f, gravity = 15f, lookSensitivity = 2f;
    public float standHeight = 1.8f, crouchHeight = 1.2f, eyeOffset = 0.15f;

    CharacterController cc;
    float pitch, vy;
    bool crouched;
    Vector3 spawnPosition;
    Quaternion spawnRotation;

    void Start()
    {
        spawnPosition = transform.position; spawnRotation = transform.rotation;
        cc = GetComponent<CharacterController>();
        cc.height = standHeight; cc.center = new Vector3(0, standHeight / 2, 0);
        SetEye();
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Tab)) ReleaseMouse();   // Tab too: on macOS Esc was not always reaching the game (user, Oct 16)
        if (Input.GetMouseButtonDown(0) && Cursor.lockState != CursorLockMode.Locked) { Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false; }
        if (Input.GetKeyDown(KeyCode.C) || Input.GetKeyDown(KeyCode.LeftControl)) { crouched = !crouched; SetEye(); }
        if (Input.GetKeyDown(KeyCode.R)) { cc.enabled = false; transform.SetPositionAndRotation(spawnPosition, spawnRotation); cc.enabled = true; vy = 0; pitch = 0; }

        if (Cursor.lockState == CursorLockMode.Locked)
        {
            transform.Rotate(0, Input.GetAxis("Mouse X") * lookSensitivity, 0);
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * lookSensitivity, -85, 85);
            cam.localRotation = Quaternion.Euler(pitch, 0, 0);
        }

        TickMotion(transform.right * Input.GetAxisRaw("Horizontal") + transform.forward * Input.GetAxisRaw("Vertical"),
            Input.GetKey(KeyCode.LeftShift), Input.GetKeyDown(KeyCode.Space), Time.deltaTime);
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

    void SetEye()
    {
        float h = crouched ? crouchHeight : standHeight;
        cc.height = h; cc.center = new Vector3(0, h / 2, 0);
        if (cam) cam.localPosition = new Vector3(0, h - eyeOffset, 0);
    }

    static void ReleaseMouse() { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }

    // switching away from Unity (Cmd+Tab, clicking another app) always gives the mouse back; a click in the game view takes it again
    void OnApplicationFocus(bool focused) { if (!focused) ReleaseMouse(); }
}
