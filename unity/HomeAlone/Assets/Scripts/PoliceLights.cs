using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// The Winnetka cruisers' roof bar (film 11574-11636, night): two tall MARS rotating beacons at the ends and two round flashers inside,
// ALL RED in the film (no blue on either car). Period rotating reflectors, so each lamp SWEEPS: it is brightest when its beam points
// at the camera and a dim glow otherwise (not an LED strobe). Two small UNSHADOWED point lights (left, right) pulse with the
// beacons' rotation so the red washes the snow, the wet road and the Murphys' facade as in 11581.
// Lamps: the prefab's Beacon_L/R and Flasher_L/R renderers (tools/house/purchased_vehicles.py), driven through one
// MaterialPropertyBlock (_EmissiveColor), so the shared material never changes. Cheap: no allocations per frame, 4 renderers,
// 2 lights with no shadows. "Off when the car isn't present": the car (night only) is a child of the night layer; disabling the
// GameObject disables this and its lights. Made at run time: never in a bake. Put it on the vehicle prefab's root.
[DisallowMultipleComponent]
public class PoliceLights : MonoBehaviour
{
    [Tooltip("Lamp glass colour (film: red). Set washRight to blue for a red/blue bar.")]
    public Color lampColor = new Color(1f, 0.05f, 0.02f);
    public Color washLeft = new Color(1f, 0.08f, 0.03f), washRight = new Color(1f, 0.08f, 0.03f);
    [Tooltip("Peak and idle emission of a lamp facing the camera, nits")]
    public float beaconNits = 6000f, flasherNits = 4000f;
    [Range(0f, 1f)] public float idle = 0.06f;
    [Tooltip("Reflector turns per minute (a MARS 888 ~ 80-90 flashes/min)")]
    public float rpm = 84f;
    [Tooltip("Beam tightness: the higher, the shorter the flash as the beam passes the viewer")]
    public float beamPower = 6f;
    public float washLumens = 2500f, washRange = 14f;
    [Range(0f, 1f)] public float washFloor = 0.25f;

    static readonly int EmissiveId = Shader.PropertyToID("_EmissiveColor");
    static readonly string[] Names = { "Beacon_L", "Beacon_R", "Flasher_L", "Flasher_R" };
    static readonly float[] Phase = { 0f, 0.5f, 0.25f, 0.75f };   // the four units turn out of step (film: never all lit at once)
    readonly Renderer[] lamps = new Renderer[4];
    readonly Light[] wash = new Light[2];
    MaterialPropertyBlock mpb;
    float t0;

    void Awake()
    {
        mpb = new MaterialPropertyBlock();
        foreach (var r in GetComponentsInChildren<Renderer>(true))
            for (int i = 0; i < Names.Length; i++)
                if (r.name == Names[i]) { lamps[i] = r; r.shadowCastingMode = ShadowCastingMode.Off; }
        for (int s = 0; s < 2; s++)
        {
            var b = lamps[s] != null ? lamps[s].bounds.center : transform.position + Vector3.up * 1.7f;
            var g = new GameObject(s == 0 ? "PoliceWash_L" : "PoliceWash_R");
            g.transform.SetParent(transform, false); g.transform.position = b + Vector3.up * 0.05f;
            var l = g.AddComponent<Light>(); g.AddComponent<HDAdditionalLightData>();
            l.type = LightType.Point; l.shadows = LightShadows.None; l.lightUnit = LightUnit.Lumen;
            l.range = washRange; l.color = s == 0 ? washLeft : washRight; l.intensity = 0f;
            wash[s] = l;
        }
        t0 = Random.value * 10f;   // two cars never flash in step
    }

    void OnEnable() { foreach (var l in wash) if (l) l.enabled = true; }

    void OnDisable()
    {
        foreach (var l in wash) if (l) l.enabled = false;
        foreach (var r in lamps) if (r) r.SetPropertyBlock(null);
    }

    void Update()
    {
        float turns = (Time.time + t0) * rpm / 60f;
        var cam = Camera.main;
        Vector3 camPos = cam ? cam.transform.position : transform.position + transform.forward * 10f;
        float washL = 0f, washR = 0f;
        for (int i = 0; i < 4; i++)
        {
            var r = lamps[i]; if (r == null) continue;
            float a = (turns + Phase[i]) * 2f * Mathf.PI;
            var beam = transform.TransformDirection(new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)));
            var to = camPos - r.bounds.center; to.y = 0f;
            float facing = to.sqrMagnitude > 1e-4f ? Mathf.Max(0f, Vector3.Dot(beam, to.normalized)) : 1f;
            float k = idle + (1f - idle) * Mathf.Pow(facing, beamPower);
            mpb.SetColor(EmissiveId, lampColor * ((i < 2 ? beaconNits : flasherNits) * k));
            r.SetPropertyBlock(mpb);
            // the spill: a turning beam sweeps the surroundings, so a point light on that side rises and falls once per turn
            float spill = 0.5f + 0.5f * Mathf.Cos(a);
            if ((i & 1) == 0) washL += spill; else washR += spill;
        }
        if (wash[0]) wash[0].intensity = washLumens * (washFloor + (1f - washFloor) * washL * 0.5f);
        if (wash[1]) wash[1].intensity = washLumens * (washFloor + (1f - washFloor) * washR * 0.5f);
    }
}
