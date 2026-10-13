using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    public static void BuildRoomLighting()
    {
        if(EditorApplication.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)throw new InvalidOperationException("Open intact scene outside Play.");
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();if(!mode)throw new InvalidOperationException("Build day/night controller first.");
        bool night=mode.night;mode.SetNight(false);
        if(!mode.dayLayer){
            mode.dayLayer=Child(mode.gameObject,"Daylight environment");
            var volume=mode.dayLayer.AddComponent<Volume>();volume.isGlobal=true;volume.priority=90;
            volume.sharedProfile=AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/HouseVolume.asset");
            var sun=Child(mode.dayLayer,"Daylight sun").AddComponent<Light>();sun.type=LightType.Directional;sun.intensity=20000;sun.color=new Color(1,.96f,.88f);sun.shadows=LightShadows.Soft;
            sun.gameObject.AddComponent<HDAdditionalLightData>();sun.transform.rotation=Quaternion.Euler(35,-25,0);
        }
        const string dayPath="Assets/Materials/IntactFoyer/RoomDayVolume.asset";
        var day=AssetDatabase.LoadAssetAtPath<VolumeProfile>(dayPath);
        if(!day){
            day=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(day,dayPath);
            foreach(var c in AssetDatabase.LoadAssetAtPath<VolumeProfile>("Assets/Settings/HouseVolume.asset").components){
                var copy=UnityEngine.Object.Instantiate(c);AssetDatabase.AddObjectToAsset(copy,day);day.components.Add(copy);
            }
        }
        var dayExposure=day.components.OfType<Exposure>().First();dayExposure.mode.value=ExposureMode.Automatic;
        dayExposure.limitMin.value=10;dayExposure.limitMax.value=14;dayExposure.compensation.value=-.5f;dayExposure.adaptationMode.value=AdaptationMode.Fixed;
        EditorUtility.SetDirty(dayExposure);EditorUtility.SetDirty(day);mode.dayLayer.GetComponent<Volume>().sharedProfile=day;
        foreach(var l in mode.nightLayer.GetComponentsInChildren<Light>(true))
            if(l.name=="Warm front room"||l.name=="Upper centre room"||l.name.EndsWith(" interior light"))UnityEngine.Object.DestroyImmediate(l.gameObject);
        var old=mode.nightLayer.transform.Find("Room practical lighting");if(old)UnityEngine.Object.DestroyImmediate(old.gameObject);
        var root=Child(mode.nightLayer,"Room practical lighting");
        // Named room sources replace window-indexed fill lights. Geometry and point-shadow policy stay intact.
        foreach(var s in new[]{
            ("Living room",new Vector3(-3.7f,4.10f,4.4f),160f,8f),
            ("Dining room",new Vector3(7.4f,4.05f,1.8f),130f,6f),
            ("Study",new Vector3(-8.9f,4.15f,2.3f),90f,6f),
            ("East ground room",new Vector3(12.7f,4.15f,2.3f),65f,6f),
            ("Kitchen",new Vector3(13.5f,4.20f,14.4f),170f,7f),
            ("Rear bedroom",new Vector3(-3.7f,7.75f,7.1f),75f,5.5f),
            ("West upper wing",new Vector3(-8.9f,7.75f,3),65f,6f),
            ("Kevin room",new Vector3(7.4f,7.75f,.2f),65f,5f),
            ("Hall bathroom",new Vector3(1.9f,7.75f,-.5f),40f,3.5f),
            ("Parents dressing area",new Vector3(12.7f,7.75f,2.3f),60f,5.5f),
            ("Front attic west",new Vector3(-2.5f,10.7f,.0f),55f,5f),
            ("Front attic east",new Vector3(6.2f,10.7f,.0f),55f,5f),
            ("Rear attic",new Vector3(1.9f,10.7f,8.7f),55f,5f)}){
            FoyerLamp(root,s.Item1+" ceiling source",s.Item2,s.Item3,s.Item4);
        }
        // These lamps already have visible fixtures in the furnished bedrooms.
        foreach(float x in new[]{10.96f,14.18f})FoyerLamp(root,"Parents bedside practical",new Vector3(x,6.22f,6.76f),45,4);
        FoyerLamp(root,"Buzz bedside practical",new Vector3(-1.72f,6.30f,-1.65f),65,5);
        foreach(var light in mode.nightLayer.GetComponentsInChildren<Light>(true)){
            if(light.name=="Window decoration spill"||light.name=="Dormer window spill")light.intensity=3;
        }
        // Room lighting handles the window glow; decorative bulbs only accent the exterior trim.
        var foyer=GameObject.Find("FoyerNight");
        foreach(var l in foyer.GetComponentsInChildren<Light>(true))if(l.name=="Soft interior bounce"||l.name=="Stair reflected light")l.intensity=30;
        var prior=mode.interiorLights.Select((l,i)=>(l,i)).Where(p=>p.l).ToDictionary(p=>p.l,p=>mode.daytimeEnabled[p.i]);
        mode.interiorLights=UnityEngine.Object.FindObjectsByType<Light>(FindObjectsInactive.Include).Where(l=>l.type==LightType.Point&&!l.transform.IsChildOf(mode.transform)).ToArray();
        mode.daytimeEnabled=mode.interiorLights.Select(l=>prior.TryGetValue(l,out bool enabled)?enabled:l.enabled).ToArray();
        BuildBuzzDayExposure();StabilizeHousePointLights();mode.SetNight(night);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static void BuildBuzzDayExposure()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play before saving room exposure.");
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();
        if(!mode||!mode.dayLayer)throw new InvalidOperationException("Daylight environment missing.");
        var existing=mode.dayLayer.transform.Find("Buzz daylight exposure");
        var go=existing?existing.gameObject:Child(mode.dayLayer,"Buzz daylight exposure");
        go.transform.position=new Vector3(-3.63f,6.8f,-.2f);
        var box=go.GetComponent<BoxCollider>();if(!box)box=go.AddComponent<BoxCollider>();
        box.isTrigger=true;box.size=new Vector3(4.8f,3.1f,4.1f);
        var volume=go.GetComponent<Volume>();if(!volume)volume=go.AddComponent<Volume>();
        volume.isGlobal=false;volume.priority=130;volume.blendDistance=.6f;
        const string path="Assets/Materials/IntactFoyer/BuzzDayExposure.asset";
        var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
        if(!profile){profile=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(profile,path);}
        if(!profile.TryGet<Exposure>(out var exposure)){exposure=profile.Add<Exposure>();AssetDatabase.AddObjectToAsset(exposure,profile);}
        // Outdoor EV10–14 crushed this interior. Clamp its day exposure while retaining
        // the global Automatic mode so the doorway blends without a mode switch.
        exposure.mode.Override(ExposureMode.Automatic);exposure.limitMin.Override(7);exposure.limitMax.Override(7);
        exposure.compensation.Override(0);exposure.adaptationMode.Override(AdaptationMode.Progressive);
        exposure.adaptationSpeedDarkToLight.Override(3);exposure.adaptationSpeedLightToDark.Override(1.5f);
        volume.sharedProfile=profile;EditorUtility.SetDirty(exposure);EditorUtility.SetDirty(profile);
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static string CheckRoomLighting()
    {
        var mode=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>();var root=mode.nightLayer.transform.Find("Room practical lighting");
        if(!root||root.GetComponentsInChildren<Light>(true).Length!=16)throw new InvalidOperationException("Missing room practical lights.");
        if(!mode.dayLayer||!mode.dayLayer.GetComponent<Volume>().sharedProfile)throw new InvalidOperationException("Daylight environment missing.");
        if(mode.nightLayer.GetComponentsInChildren<Light>(true).Any(l=>l.name.EndsWith(" interior light")||l.name=="Warm front room"))throw new InvalidOperationException("Window helper lights remain.");
        return "PASS 16 room/bedside sources; per-window interior helpers removed; "+CheckExteriorNight();
    }
}
