using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Build Exterior Night Lighting")]
    public static void BuildExteriorNight()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var previous=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();
        if(previous){previous.SetNight(false);UnityEngine.Object.DestroyImmediate(previous.gameObject);}
        var control=new GameObject("Day and night - press N");var mode=control.AddComponent<HouseNightMode>();
        mode.interiorLights=GameObject.Find("FoyerNight").GetComponentsInChildren<Light>();
        mode.daytimeEnabled=mode.interiorLights.Select(l=>l.enabled).ToArray();
        var root=Child(control,"Exterior night lighting");mode.nightLayer=root;
        const string path="Assets/Materials/IntactFoyer/ExteriorNightVolume.asset";
        var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
        if(!profile){profile=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(profile,path);}
        foreach(var c in profile.components.ToArray())UnityEngine.Object.DestroyImmediate(c,true);profile.components.Clear();
        var env=profile.Add<VisualEnvironment>(true);env.skyType.value=(int)SkyType.Gradient;
        var sky=profile.Add<GradientSky>(true);sky.top.value=new Color(.001f,.002f,.006f);sky.middle.value=new Color(.008f,.012f,.025f);sky.bottom.value=new Color(.004f,.006f,.012f);
        var exposure=profile.Add<Exposure>(true);exposure.mode.value=ExposureMode.Fixed;exposure.fixedExposure.value=1;
        var tone=profile.Add<Tonemapping>(true);tone.mode.value=TonemappingMode.ACES;
        var bloom=profile.Add<Bloom>(true);bloom.intensity.value=.18f;bloom.scatter.value=.55f;
        foreach(var c in profile.components)AssetDatabase.AddObjectToAsset(c,profile);
        var volume=root.AddComponent<Volume>();volume.isGlobal=true;volume.priority=110;volume.sharedProfile=profile;
        var bulb=FoyerFinish("ExteriorWarmBulb",new Color(1,.8f,.47f),.3f);bulb.SetColor("_EmissiveColor",new Color(1,.65f,.28f)*30);HDMaterial.ValidateMaterial(bulb);
        var brass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/AntiqueBrass.mat");
        // Each window gets tiny visible bulbs; one local light supplies their combined spill.
        foreach(float y in new[]{2.87f,6.64f})foreach(float x in new[]{-4.77f,-2.49f,6.25f,8.53f}){
            float h=y<4?2.34f:1.62f,w=y<4?1.14f:.94f;
            for(int side=-1;side<=1;side+=2)for(int j=0;j<9;j++)NightBulb(root,new Vector3(x+side*(w*.5f+.035f),y-h*.5f+j*h/8,-2.81f),bulb);
            for(int j=1;j<5;j++)NightBulb(root,new Vector3(x-w*.5f+j*w/5,y+h*.5f,-2.81f),bulb);
            FoyerLamp(root,"Window decoration spill",new Vector3(x,y,-3.02f),20,2.1f);
        }
        foreach(var window in ExteriorWindowOpenings()){
            if(window.label=="Main front sash")continue;
            var facing=Quaternion.Euler(0,window.yaw,0)*Vector3.back;
            if(window.label.Contains("dormer")){
                FoyerLamp(root,"Dormer window spill",window.center+facing*.35f,15,2.3f);
                for(int side=-1;side<=1;side+=2)for(int j=0;j<8;j++)
                    NightBulb(root,window.center+Quaternion.Euler(0,window.yaw,0)*new Vector3(side*window.w*.5f,-window.h*.5f+j*window.h/7,-.25f),bulb);
            }
        }
        // Entry lantern below the existing porch; open cage preserves the sightline.
        var lantern=Child(root,"Front entrance lantern");
        Cyl(lantern,"Chain",1.9f,-3.45f,4.35f,4.65f,.012f,brass);
        foreach(float y in new[]{3.88f,4.35f})Cyl(lantern,"Lantern rim",1.9f,-3.45f,y,y+.035f,.16f,brass);
        foreach(float x in new[]{1.79f,2.01f})foreach(float z in new[]{-3.56f,-3.34f})Cyl(lantern,"Cage upright",x,z,3.90f,4.37f,.012f,brass);
        BedroomSoft(lantern,"Lantern flame",new Vector3(1.9f,4.1f,-3.45f),new Vector3(.055f,.14f,.055f),bulb);
        FoyerLamp(root,"Front lantern illumination",new Vector3(1.9f,4.1f,-3.45f),120,7);
        var moon=Child(root,"Cool moonlight").AddComponent<Light>();moon.type=LightType.Directional;
        moon.color=new Color(.72f,.8f,1);moon.intensity=.6f;moon.shadows=LightShadows.Soft;
        moon.gameObject.AddComponent<HDAdditionalLightData>();moon.transform.rotation=Quaternion.Euler(35,-25,0);
        // A tiny point source inside the cage overstates its silhouette; the lantern still illuminates the entry.
        foreach(var r in lantern.GetComponentsInChildren<Renderer>())r.shadowCastingMode=ShadowCastingMode.Off;
        // ponytail: grouped practical lights approximate bounce; bake GI after material/UV validation.
        foreach(var light in root.GetComponentsInChildren<Light>())if(light.name.Contains("spill"))light.shadows=LightShadows.None;
        StabilizeHousePointLights();
        BuildRoomLighting();mode.SetNight(true);AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static void StabilizeHousePointLights()
    {
        // User-confirmed isolation: disabling point shadows stops the exterior flicker.
        // Keep the working result; reintroduce bounded fixture shadows only after motion validation.
        foreach(var light in UnityEngine.Object.FindObjectsByType<Light>(FindObjectsInactive.Include))
            if(light.type==LightType.Point)light.shadows=LightShadows.None;
    }
    static void NightBulb(GameObject root,Vector3 p,Material material)
    {
        BedroomSoft(root,"Warm decorative bulb",p,Vector3.one*.025f,material);
    }
    public static string CheckExteriorNight()
    {
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();if(!mode)throw new InvalidOperationException("Missing night controller");
        bool old=mode.night;
        try{
            mode.SetNight(false);
            if(mode.nightLayer.activeSelf||(mode.dayLayer&&!mode.dayLayer.activeSelf)||mode.interiorLights.Where((l,i)=>l.enabled!=mode.daytimeEnabled[i]).Any())throw new InvalidOperationException("Day restoration failed");
            mode.SetNight(true);
            if(!mode.nightLayer.activeSelf||(mode.dayLayer&&mode.dayLayer.activeSelf)||mode.interiorLights.Any(l=>!l.enabled))throw new InvalidOperationException("Night activation failed");
            if(mode.nightLayer.GetComponentsInChildren<Collider>().Length!=0)throw new InvalidOperationException("Decoration blocks walking");
            if(UnityEngine.Object.FindObjectsByType<Light>().Any(l=>l.enabled&&l.type==LightType.Point&&l.shadows!=LightShadows.None))
                throw new InvalidOperationException("Point shadows reintroduced into confirmed stable lighting setup");
            return "PASS day/night round trip and collision-free lighting layer";
        }finally{mode.SetNight(old);}
    }
}
