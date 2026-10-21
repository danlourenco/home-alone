using UnityEngine;

// The sun's shadow casters follow the storey the player is on (stop-gap for the upstairs overhang, SpecGreybox.FilmFront). On the
// ground floor the film's flush front casts and Marina's overhanging upstairs strip does not; from the stair up it is the other way
// round. HDRP gives only one directional light shadows, so one sun switches its shadow layers.
public class StoreyShadows : MonoBehaviour
{
    public uint groundMask, upperMask;
    public float switchY;
    Light sun;

    void Start() { sun = GetComponent<Light>(); }

    void Update()
    {
        var cam = Camera.main; if (cam == null || sun == null) return;
        // the split's state (with its hysteresis and envelope) when there is one: outside above switchY (the zipline) is the film's house
        bool up = HouseSplit.State >= 0 ? HouseSplit.State == 1 : cam.transform.position.y > switchY;
        uint m = up ? upperMask : groundMask;
        if ((uint)sun.renderingLayerMask != m) sun.renderingLayerMask = (int)m;
    }
}
