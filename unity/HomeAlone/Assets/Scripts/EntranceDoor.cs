using UnityEngine;

// One physical, two-sided leaf. Frame and sidelights never move. A closed door blocks
// the opening; the leaf's own collider follows it throughout the swing.
public class EntranceDoor : MonoBehaviour
{
    public Transform leaf;
    public BoxCollider leafCollider;
    public bool locked;
    public float openAngle = 100f, speed = 95f, reach = 2f;
    public bool IsOpen => target > 0f;
    float angle, target;
    bool aimed;
    Quaternion closed = Quaternion.identity;
    bool initialized;
    void Initialize() { if (!initialized && leaf) { closed=leaf.localRotation; initialized=true; } }
    void Start() => Initialize();
    public void SetInstant(bool value) { Initialize(); target=angle=value?openAngle:0f; leaf.localRotation=closed*Quaternion.Euler(0,angle,0); Physics.SyncTransforms(); }
    public bool SetOpen(bool value)
    {
        Initialize();
        if (value && locked) return false;
        target = value ? openAngle : 0f;
        return true;
    }
    void Update()
    {
        if (!leaf || !leafCollider) return;
        Initialize();
        var camera = Camera.main;
        var handle = leaf.TransformPoint(new Vector3(0, 1.0f, -0.74f));
        aimed = camera && Vector3.Distance(camera.transform.position, handle) < reach &&
            Vector3.Angle(camera.transform.forward, handle-camera.transform.position) < 38f;
        if (aimed && Cursor.lockState == CursorLockMode.Locked && Input.GetKeyDown(KeyCode.E)) SetOpen(!IsOpen);
        float next = Mathf.MoveTowards(angle, target, speed*Time.deltaTime);
        if (next == angle) return;
        leaf.localRotation = closed * Quaternion.Euler(0,next,0);
        Physics.SyncTransforms();
        // Never swing through the player. The door pauses until they leave its swept volume.
        var player = FindFirstObjectByType<FpsController>();
        var cc = player ? player.GetComponent<CharacterController>() : null;
        if (cc && cc.enabled && Physics.ComputePenetration(leafCollider,leafCollider.transform.position,leafCollider.transform.rotation,
            cc,cc.transform.position,cc.transform.rotation,out _,out _))
        { leaf.localRotation = closed * Quaternion.Euler(0,angle,0); Physics.SyncTransforms(); return; }
        angle = next;
        ShadowRefresh.Near(leafCollider.bounds);
    }
    void OnGUI()
    {
        if (!aimed) return;
        var style = new GUIStyle(GUI.skin.label) { fontSize=18, alignment=TextAnchor.MiddleCenter };
        GUI.Label(new Rect(0,Screen.height*.62f,Screen.width,30), locked && !IsOpen ? "Front door locked" : IsOpen ? "E: close the front door" : "E: open the front door",style);
    }
}
