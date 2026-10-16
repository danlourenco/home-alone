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
    void Update(){if(Input.GetKeyDown(KeyCode.N))SetNight(!night);}
    public void SetNight(bool enabled)
    {
        night=enabled;nightLayer.SetActive(enabled);if(dayLayer)dayLayer.SetActive(!enabled);
        for(int i=0;i<interiorLights.Length;i++)if(interiorLights[i])interiorLights[i].enabled=enabled||daytimeEnabled[i];
        var baked=FindFirstObjectByType<FoyerBakedLighting>();if(baked)baked.Apply(enabled);
        // baked bounce light: BakeLighting.Bake stores a "Night" scenario beside the day one ("Default")
        var apv=UnityEngine.Rendering.ProbeReferenceVolume.instance;
        if(apv.currentBakingSet!=null&&apv.currentBakingSet.lightingScenarios.Contains("Night"))apv.lightingScenario=enabled?"Night":"Default";
    }
}
