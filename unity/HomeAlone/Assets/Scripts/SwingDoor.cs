using UnityEngine;

// A double-acting (swing) door: it turns away from whoever walks into it and falls closed behind them. The leaf has no collider, so it
// never blocks a walk; the turn is visual. This transform sits on the hinge axis at the floor; local +z runs along the closed leaf to
// its latch edge and local +x is one face's normal.
public class SwingDoor : MonoBehaviour
{
    public Transform leaf;
    public float width = 0.7f, openAngle = 80f, openSpeed = 220f, closeSpeed = 90f, reach = 0.75f;
    float angle;

    void Update()
    {
        var cam = Camera.main; if (cam == null || leaf == null) return;
        var p = transform.InverseTransformPoint(cam.transform.position);
        // someone in the doorway band (along the leaf, close to its plane) pushes it away from their side
        bool pushing = p.z > -0.1f && p.z < width + 0.1f && Mathf.Abs(p.x) < reach;
        float target = pushing ? -Mathf.Sign(p.x) * openAngle : 0f;
        float speed = Mathf.Abs(target) > Mathf.Abs(angle) ? openSpeed : closeSpeed;
        angle = Mathf.MoveTowards(angle, target, speed * Time.deltaTime);
        leaf.localRotation = Quaternion.Euler(0f, angle, 0f);
    }
}
