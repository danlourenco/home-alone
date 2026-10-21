using UnityEngine;

// The ground's wetness follows the weather and the time of day (walk notes Oct 19 08:48/09:50/12:11; user Oct 20 "let's do it"):
// sunny/morning = film 1640 (weathered asphalt pale and mostly dry, damp patches), overcast = damper, night = film 10162/10170 (dark,
// wet, glinting). Built by SpecGreybox.FrontDrive: each surface kind has one material per state (tools/house/exterior_textures.py
// wet_slabs; gate tools/house/wet_check.py); on a change every listed renderer's slots are swapped to the state's material. Swapping
// shared materials (not a property block) keeps the SRP Batcher and static batching; it runs only when the state changes.
public class WetGround : MonoBehaviour
{
    public Renderer[] renderers = new Renderer[0];
    public Material[] asphalt = new Material[3], concrete = new Material[3], apron = new Material[3];   // Sunny, Overcast, Night
    HouseWeather weather; HouseNightMode nightMode; int shown = -1;

    void Start()
    {
        weather = FindAnyObjectByType<HouseWeather>(FindObjectsInactive.Include);
        nightMode = FindAnyObjectByType<HouseNightMode>(FindObjectsInactive.Include);
    }

    void LateUpdate()
    {
        int s = nightMode && nightMode.night ? 2 : weather && weather.state == HouseWeather.State.Overcast ? 1 : 0;
        if (s != shown) Show(s);
    }

    public void Show(int s)
    {
        shown = s;
        foreach (var r in renderers)
        {
            if (!r) continue;
            var ms = r.sharedMaterials; bool hit = false;
            for (int i = 0; i < ms.Length; i++)
                foreach (var set in new[] { asphalt, concrete, apron })
                    if (System.Array.IndexOf(set, ms[i]) >= 0 && ms[i] != set[s]) { ms[i] = set[s]; hit = true; }
            if (hit) r.sharedMaterials = ms;
        }
    }
}
