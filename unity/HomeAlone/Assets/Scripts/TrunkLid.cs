using UnityEngine;

// Buzz's footlocker opens (walk note Oct 18 21:12 "would be cool if i knew how to open the chest"): look at it from within REACH and
// an on-screen prompt says "E: open"; E opens or closes the lid about its hinge (SpecGreybox.Trunk adds this to BuzzTrunk_HiFi). The
// lid's own collider moves with it; the lamps' cached shadows redraw while it swings (ShadowRefresh).
public class TrunkLid : MonoBehaviour
{
    public Transform lid;
    public float openDeg = 100f, speed = 160f, reach = 1.5f;
    float angle, target;
    Quaternion closed; Vector3 axis;
    bool aimed;

    void Start()
    {
        if (lid == null) { enabled = false; return; }
        closed = lid.rotation;
        var r = lid.GetComponentInChildren<Renderer>(); var b = r.bounds.size;
        axis = b.x >= b.z ? Vector3.right : Vector3.forward;               // the hinge runs along the box's length
        float y0 = r.bounds.center.y; lid.rotation = Quaternion.AngleAxis(20f, axis) * closed;
        if (r.bounds.center.y < y0) axis = -axis;                          // the way that lifts the lid
        lid.rotation = closed;
    }

    void Update()
    {
        var cam = Camera.main; if (cam == null) return;
        var c = lid.GetComponentInChildren<Renderer>().bounds.center;
        var to = c - cam.transform.position;
        aimed = to.magnitude < reach && Vector3.Angle(cam.transform.forward, to) < 25f;
        if (aimed && Input.GetKeyDown(KeyCode.E)) target = target > 0f ? 0f : openDeg;
        if (angle == target) return;
        angle = Mathf.MoveTowards(angle, target, speed * Time.deltaTime);
        lid.rotation = Quaternion.AngleAxis(angle, axis) * closed;
        ShadowRefresh.Near(new Bounds(c, Vector3.one * 1.5f));
    }

    void OnGUI()
    {
        if (!aimed) return;
        var st = new GUIStyle(GUI.skin.label) { fontSize = 18, alignment = TextAnchor.MiddleCenter }; st.normal.textColor = Color.white;
        GUI.Label(new Rect(0, Screen.height * 0.62f, Screen.width, 30), target > 0f ? "E: close the footlocker" : "E: open the footlocker", st);
    }
}
