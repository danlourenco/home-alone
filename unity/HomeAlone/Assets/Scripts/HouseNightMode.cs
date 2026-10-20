using System.Linq;
using UnityEngine;

// The lighting layer is separate from the house; N restores the saved daytime light states.
public class HouseNightMode : MonoBehaviour
{
    public GameObject nightLayer;
    public GameObject dayLayer;
    public Light[] interiorLights;
    public bool[] daytimeEnabled;
    public bool night;
    // lamp bulbs and shades: their own emission at night, dark by day (a property block, so the shared material never changes)
    public Renderer[] glowRenderers = new Renderer[0];
    // never sunlit by day (SpecGreybox.SunCull: the outer shell shades every point of them for every weather's sun): no shadows by day, so
    // the sun's cascades skip them; their own mode back at night for the lamps
    public Renderer[] sunlessCasters = new Renderer[0];
    public UnityEngine.Rendering.ShadowCastingMode[] sunlessModes = new UnityEngine.Rendering.ShadowCastingMode[0];
    void Start(){SetNight(night);}
    // each room's baked reflection probe and its image per scenario (BakeLighting)
    public UnityEngine.Rendering.HighDefinition.HDAdditionalReflectionData[] reflectionProbes = new UnityEngine.Rendering.HighDefinition.HDAdditionalReflectionData[0];
    public Texture[] dayReflections = new Texture[0], nightReflections = new Texture[0];
    public void ApplyReflections(bool atNight)
    {
        var set = atNight ? nightReflections : dayReflections;
        for (int i = 0; i < reflectionProbes.Length && i < set.Length; i++)
            if (reflectionProbes[i] && set[i]) reflectionProbes[i].bakedTexture = set[i];
    }
    void Update()
    {
        if(Input.GetKeyDown(KeyCode.N))SetNight(!night);var cam=Camera.main;if(night&&cam)ShadowRefresh.Warm(cam);   // lamp shadow maps drawn when first in view (ShadowRefresh)
        if(Input.GetKeyDown(KeyCode.LeftBracket))SetWhiteBalance(WbTemperature-WbStep,true);
        if(Input.GetKeyDown(KeyCode.RightBracket))SetWhiteBalance(WbTemperature+WbStep,true);
    }

    // NIGHT WHITE BALANCE (Oct 20; tools/house/night_wb.py): the lamps are 2700 K, the film was shot on tungsten-balanced stock, so its
    // night interiors read near-white (hall bath tile R/B 1.07 in film 336; ours 2.99). An HDRP White Balance inside the house only (a
    // second Volume on InteriorRestoreVolume: its trigger boxes are the inside of the brick skin), at night only, so the street's view of
    // warm windows (ExteriorLook_Night, Pietro) is untouched. [ and ] nudge it while walking (saved, PlayerPrefs); 0 = the lamps as built,
    // film match (night_wb.py, median of 5 rooms) = -57. THE DEFAULT for a fresh install: WbDefault.
    public const float WbDefault=-28f, WbStep=4f; const string WbKey="NightWhiteBalance";
    public static float WbTemperature=WbDefault;
    static UnityEngine.Rendering.HighDefinition.WhiteBalance wb; static UnityEngine.Rendering.Volume wbVol; static float wbShownUntil; static bool atNight;
    void Awake()
    {
        WbTemperature=PlayerPrefs.GetFloat(WbKey,WbDefault);
        var inside=GameObject.Find("InteriorRestoreVolume");
        if(!inside){Debug.LogWarning("HouseNightMode: no InteriorRestoreVolume, night white balance off");return;}
        var prof=ScriptableObject.CreateInstance<UnityEngine.Rendering.VolumeProfile>();
        wb=prof.Add<UnityEngine.Rendering.HighDefinition.WhiteBalance>(true);
        var iv=inside.GetComponent<UnityEngine.Rendering.Volume>();
        wbVol=inside.AddComponent<UnityEngine.Rendering.Volume>();   // the same GameObject: a local Volume uses its GameObject's colliders
        wbVol.isGlobal=false;wbVol.priority=26f;wbVol.blendDistance=iv?iv.blendDistance:0.6f;wbVol.sharedProfile=prof;
        SetWhiteBalance(WbTemperature,false);
    }
    // PerfProbe's variant wb=T sets it without saving
    public static void SetWhiteBalance(float t,bool save)
    {
        WbTemperature=Mathf.Clamp(Mathf.Round(t),-100f,100f);
        if(save){PlayerPrefs.SetFloat(WbKey,WbTemperature);PlayerPrefs.Save();wbShownUntil=Time.unscaledTime+3f;}
        if(wb)wb.temperature.value=WbTemperature;
        if(wbVol)wbVol.weight=atNight?1f:0f;
    }
    void OnGUI()
    {
        if(Time.unscaledTime>wbShownUntil)return;
        var st=new GUIStyle(GUI.skin.label){fontSize=18};st.normal.textColor=Color.white;
        GUI.Label(new Rect(14,14,900,30),$"Night white balance (inside): {WbTemperature:+0;-0;0}   [ cooler  ] warmer   (0 = lamps as built, -57 = film){(night?"":"   (applies at night: N)")}",st);
    }
    public void SetNight(bool enabled)
    {
        night=enabled;nightLayer.SetActive(enabled);atNight=enabled;if(wbVol)wbVol.weight=enabled?1f:0f;ShadowRefresh.Forget();if(dayLayer)dayLayer.SetActive(!enabled);
        for(int i=0;i<interiorLights.Length;i++)if(interiorLights[i])interiorLights[i].enabled=enabled||daytimeEnabled[i];
        var baked=FindFirstObjectByType<FoyerBakedLighting>();if(baked)baked.Apply(enabled);
        // baked bounce light: BakeLighting.Bake stores a "Night" scenario beside the day one ("Default")
        var apv=UnityEngine.Rendering.ProbeReferenceVolume.instance;
        if(apv.currentBakingSet!=null&&apv.currentBakingSet.lightingScenarios.Contains("Night"))apv.lightingScenario=enabled?"Night":"Default";
        ApplyReflections(enabled);
        for(int i=0;i<sunlessCasters.Length&&i<sunlessModes.Length;i++)if(sunlessCasters[i])sunlessCasters[i].shadowCastingMode=enabled?sunlessModes[i]:UnityEngine.Rendering.ShadowCastingMode.Off;
        var block=new MaterialPropertyBlock();
        foreach(var r in glowRenderers){ if(!r) continue; if(enabled) r.SetPropertyBlock(null); else { r.GetPropertyBlock(block); block.SetColor("_EmissiveColor",Color.black); r.SetPropertyBlock(block); } }
    }
}
