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
    void Update(){if(Input.GetKeyDown(KeyCode.N))SetNight(!night);var cam=Camera.main;if(night&&cam)ShadowRefresh.Warm(cam);}   // lamp shadow maps drawn when first in view (ShadowRefresh)
    public void SetNight(bool enabled)
    {
        night=enabled;nightLayer.SetActive(enabled);ShadowRefresh.Forget();if(dayLayer)dayLayer.SetActive(!enabled);
        for(int i=0;i<interiorLights.Length;i++)if(interiorLights[i])interiorLights[i].enabled=enabled||daytimeEnabled[i];
        var baked=FindFirstObjectByType<FoyerBakedLighting>();if(baked)baked.Apply(enabled);
        // baked bounce light: BakeLighting.Bake stores a "Night" scenario beside the day one ("Default")
        var apv=UnityEngine.Rendering.ProbeReferenceVolume.instance;
        if(apv.currentBakingSet!=null&&apv.currentBakingSet.lightingScenarios.Contains("Night"))apv.lightingScenario=enabled?"Night":"Default";
        ApplyReflections(enabled);
        var block=new MaterialPropertyBlock();
        foreach(var r in glowRenderers){ if(!r) continue; if(enabled) r.SetPropertyBlock(null); else { r.GetPropertyBlock(block); block.SetColor("_EmissiveColor",Color.black); r.SetPropertyBlock(block); } }
    }
}
