using UnityEngine;

/// Falling snow (SpecGreybox.ExteriorRealism, Oct 18 2026) stays outside: while the camera this rides on stands inside the house
/// (the interior volume's skin boxes, 0.3 m in from the brick), its particle systems stop emitting and are not drawn.
public class SnowfallGate : MonoBehaviour
{
    public BoxCollider[] house;
    ParticleSystem[] systems; ParticleSystemRenderer[] renderers; bool wasInside;

    void Awake() { systems = GetComponentsInChildren<ParticleSystem>(true); renderers = GetComponentsInChildren<ParticleSystemRenderer>(true); }

    void LateUpdate()
    {
        bool inside = false; var p = transform.position;
        if (house != null) foreach (var b in house) if (b != null && b.bounds.Contains(p)) { inside = true; break; }
        if (inside == wasInside) return;
        wasInside = inside;
        foreach (var s in systems) { var e = s.emission; e.enabled = !inside; if (inside) s.Clear(); }
        foreach (var r in renderers) r.enabled = !inside;
    }
}
