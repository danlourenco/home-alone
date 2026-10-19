using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// O cycles the day's weather for comparison (user Oct 19: "match the sun direction to the movie and let me toggle between sunny and
// overcast days"). Built by SpecGreybox.Daylight; lives in the day layer, so N (HouseNightMode) still turns the whole day off.
//  Sunny   film 4382 (~1 pm): the sun solved from the portico's shadow (tools/house/sun_solve.py: az 196.8, el 35), full strength, crisp
//          shadows, HDRP's physically based clear sky, and the clear-winter dome (Poly Haven Snowy Cemetery, CC0). The default: the
//          film's day exteriors are sunny (4382/4444, the departure morning 1560-1890); 6399 is the overcast one.
//  Morning film 1890 (departure): the SE faces lit, the SW front dark -> a low sun east of SE (az <= ~138: a bound, not a solve);
//          az 130 el 17 is Feb 15 1990 ~8:45 am CST. Lights the kitchen through its SE windows (user: the breakfast scenes).
//  Overcast film 6399: the Snowy Park dome, a grey gradient sky, the sun high, dim, wide (40 deg) and its shadows faint.
// LIMIT: the baked indirect light (APV "Default" scenario, BakeLighting) is ONE bake, made with the Sunny sun; Morning and Overcast
// change only the realtime sun, sky and dome. Add a scenario per state only if the difference reads glaringly wrong.
public class HouseWeather : MonoBehaviour
{
    public enum State { Sunny, Morning, Overcast }
    public State state = State.Sunny;
    public Light sun;
    public MeshRenderer dome;                       // WinterBackdrop_Day
    public Material clearDome, overcastDome;
    public Volume overcastSky;                      // gradient sky, only on when overcast
    public float frontAzimuth = 227.6f;             // compass bearing the front (+spec x) faces
    public float domeSunAzimuth = 196.8f;           // where the clear dome's photo sun was rolled to (tools/house/window_backdrop.py)

    [System.Serializable] public struct Look { public float az, el, lux, angularDiameter, shadowDimmer; }
    public Look sunny = new Look { az = 196.8f, el = 35f, lux = 100000f, angularDiameter = 0.5f, shadowDimmer = 1f };
    public Look morning = new Look { az = 130f, el = 17f, lux = 70000f, angularDiameter = 0.5f, shadowDimmer = 1f };
    public Look overcast = new Look { az = 196.8f, el = 65f, lux = 6000f, angularDiameter = 40f, shadowDimmer = 0.4f };
    Quaternion domeRot0; bool started;

    void Start() { if (dome) domeRot0 = dome.transform.rotation; started = true; Apply(state); }
    void Update() { if (Input.GetKeyDown(KeyCode.O)) Apply((State)(((int)state + 1) % 3)); }
    // falling snow (the camera's "Snowfall", SpecGreybox.ExteriorRealism; F toggles it, SnowfallGate hides it indoors) only where it makes
    // sense (user Oct 19: "the falling snow doesn't really make sense ... when the sky is sunny"): held off in Sunny and Morning, so F is
    // ignored there; on again when Overcast is chosen and at night (this sits in the day layer: N disables it)
    static Transform Snow() { var c = Camera.main; return c ? c.transform.Find("Snowfall") : null; }
    void LateUpdate() { var sf = Snow(); if (sf && state != State.Overcast && sf.gameObject.activeSelf) sf.gameObject.SetActive(false); }
    void OnDisable() { var sf = Snow(); if (sf) sf.gameObject.SetActive(true); }

    public static Vector3 ToSun(float az, float el, float front)
    {   // spec +x = the front's bearing; spec -z (world +z) = front - 90
        float rel = (az - front) * Mathf.Deg2Rad, e = el * Mathf.Deg2Rad;
        return new Vector3(Mathf.Cos(rel) * Mathf.Cos(e), Mathf.Sin(e), -Mathf.Sin(rel) * Mathf.Cos(e));
    }

    public void Apply(State s)
    {
        state = s;
        var k = s == State.Sunny ? sunny : s == State.Morning ? morning : overcast;
        if (sun)
        {
            sun.transform.rotation = Quaternion.LookRotation(-ToSun(k.az, k.el, frontAzimuth));
            var hd = sun.GetComponent<HDAdditionalLightData>();
            sun.intensity = k.lux;
            if (hd) { hd.angularDiameter = k.angularDiameter; hd.shadowDimmer = k.shadowDimmer; }
        }
        if (dome)
        {
            dome.sharedMaterial = s == State.Overcast ? overcastDome : clearDome;
            if (!started) domeRot0 = dome.transform.rotation;
            // a positive turn about world y raises the compass bearing: keep the photo's sun under the light's
            dome.transform.rotation = s == State.Morning ? Quaternion.Euler(0, k.az - domeSunAzimuth, 0) * domeRot0 : domeRot0;
        }
        if (overcastSky) overcastSky.enabled = s == State.Overcast;
        if (Application.isPlaying && Snow() is Transform sf) sf.gameObject.SetActive(s == State.Overcast);
    }
}
