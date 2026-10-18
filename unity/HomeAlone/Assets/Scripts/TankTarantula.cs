using UnityEngine;

// Buzz's tarantula in its terrarium (SpecGreybox.BuzzProps): idles, and now and then walks slowly to a new spot on the soil, staying
// inside lo..hi (parent-space x/z bounds: the glass, less the leg span). The pack's clips are root motion; the position is driven here.
public class TankTarantula : MonoBehaviour
{
    public Vector3 lo, hi;
    public float speed = 0.012f;   // m/s: a slow amble
    Animator anim; Vector3 target; float until; bool walking;

    void Start() { anim = GetComponentInChildren<Animator>(); Rest(); }

    void Rest()
    {
        walking = false; until = Time.time + Random.Range(6f, 16f);
        if (anim) { anim.speed = 1f; anim.CrossFade("idle", 0.4f); }
    }

    void Update()
    {
        if (!walking)
        {
            if (Time.time < until) return;
            target = new Vector3(Random.Range(lo.x, hi.x), transform.localPosition.y, Random.Range(lo.z, hi.z));
            walking = true; if (anim) { anim.speed = 0.6f; anim.CrossFade("walk", 0.4f); }
            return;
        }
        var to = target - transform.localPosition; to.y = 0;
        if (to.magnitude < 0.004f) { Rest(); return; }
        var want = Quaternion.LookRotation(to.normalized, Vector3.up);
        transform.localRotation = Quaternion.RotateTowards(transform.localRotation, want, 45f * Time.deltaTime);
        if (Quaternion.Angle(transform.localRotation, want) > 30f) return;   // turn on the spot first
        var p = transform.localPosition + to.normalized * Mathf.Min(speed * Time.deltaTime, to.magnitude);
        transform.localPosition = new Vector3(Mathf.Clamp(p.x, lo.x, hi.x), p.y, Mathf.Clamp(p.z, lo.z, hi.z));
    }
}
