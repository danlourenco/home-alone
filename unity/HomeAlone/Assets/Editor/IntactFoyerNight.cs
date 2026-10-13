using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    [MenuItem("HomeAlone/Reference/Set Foyer Night Scene")]
    public static void SetIntactFoyerNight()
    {
        if(EditorApplication.isPlaying || UnityEngine.SceneManagement.SceneManager.GetActiveScene().path!=IntactScene)
            throw new System.InvalidOperationException("Open IntactHouseReference outside Play mode.");
        var previous=GameObject.Find("FoyerNight");if(previous)Object.DestroyImmediate(previous);
        var root=new GameObject("FoyerNight");
        var wood=FoyerFinish("FurnitureWalnut",new Color(.13f,.055f,.025f),.42f);
        var red=FoyerFinish("ChairVelvet",new Color(.36f,.018f,.028f),.08f);
        var brass=FoyerFinish("AntiqueBrass",new Color(.42f,.26f,.085f),.55f);brass.SetFloat("_Metallic",.75f);
        var shade=FoyerFinish("Lampshade",new Color(.96f,.85f,.65f),.1f);
        // Right-wall console and chairs, facing the stairs. Native ground level is 1.31.
        var console=Child(root,"Wall console");
        var top=Cyl(console,"Oval walnut top",4.43f,5.85f,2.08f,2.15f,.5f,wood);
        top.transform.localScale=new Vector3(.64f,.035f,1.5f);
        Box(console,"Apron",4.2f,4.65f,5.26f,6.44f,1.94f,2.08f,wood);
        foreach(float x in new[]{4.22f,4.63f})foreach(float z in new[]{5.3f,6.4f})Cyl(console,"Turned leg",x,z,1.31f,2.04f,.027f,wood);
        foreach(float z in new[]{4.58f,7.1f})
        {
            var chair=Child(root,"Red side chair");
            Box(chair,"Seat frame",4.08f,4.64f,z-.27f,z+.27f,1.73f,1.79f,wood);
            Box(chair,"Velvet cushion",4.06f,4.63f,z-.26f,z+.26f,1.79f,1.87f,red);
            foreach(float x in new[]{4.13f,4.59f})foreach(float dz in new[]{-.21f,.21f})Cyl(chair,"Leg",x,z+dz,1.31f,1.74f,.024f,wood);
            foreach(float dz in new[]{-.24f,.24f})Box(chair,"Back post",4.57f,4.63f,z+dz-.025f,z+dz+.025f,1.75f,2.44f,wood);
            Box(chair,"Top rail",4.56f,4.64f,z-.26f,z+.26f,2.36f,2.45f,wood);
            Box(chair,"Central back splat",4.58f,4.62f,z-.07f,z+.07f,1.87f,2.38f,wood);
        }
        foreach(var p in new[]{new Vector3(4.43f,2.15f,5.85f)})
        {
            Cyl(root,"Lamp base",p.x,p.z,p.y,p.y+.05f,.12f,brass);
            Cyl(root,"Lamp stem",p.x,p.z,p.y+.05f,p.y+.32f,.025f,brass);
            Cyl(root,"Ivory shade",p.x,p.z,p.y+.28f,p.y+.59f,.19f,shade).GetComponent<Renderer>().shadowCastingMode=ShadowCastingMode.Off;
            FoyerLamp(root,"Table lamp",p+Vector3.up*.43f,100,4.5f);
        }
        foreach(float z in new[]{4.95f,6.72f})
        {
            Box(root,"Sconce backplate",4.68f,4.73f,z-.065f,z+.065f,2.99f,3.23f,brass);
            Box(root,"Sconce arm",4.43f,4.7f,z-.022f,z+.022f,3.02f,3.06f,brass);
            Cyl(root,"Candle sleeve",4.44f,z,3.04f,3.23f,.025f,shade);
            FoyerLamp(root,"Warm wall sconce",new Vector3(4.4f,3.28f,z),55,5);
        }
        FoyerChandelier(root,brass,shade);
        FoyerChandelier(root,brass,shade,true);
        // Rear recess fixture confirmed in IMG_3843; entrance location reported by user.
        foreach(var mount in new[]{new Vector3(2f,4.21f,10.1f),new Vector3(1.9f,4.92f,1.2f)})
        {
            string label=mount.z>5?"Rear arch ceiling light":"Entrance light (provisional)";
            var fixture=Child(root,label);
            Cyl(fixture,"Brass ceiling rim",mount.x,mount.z,mount.y-.05f,mount.y,.21f,brass);
            FixtureShade(fixture,label+" opal diffuser",mount,AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/FixtureOpalGlass.mat"),
                new[]{new Vector2(.015f,-.17f),new Vector2(.10f,-.15f),new Vector2(.17f,-.10f),new Vector2(.20f,-.035f)});
            FoyerLamp(root,label+" source",mount-Vector3.up*.22f,mount.z>5?45:65,5);
        }
        FoyerLamp(root,"Soft interior bounce",new Vector3(2.2f,3.75f,2),100,9);
        FoyerLamp(root,"Stair reflected light",new Vector3(.6f,4.2f,6),100,7);
        const string path="Assets/Materials/IntactFoyer/NightVolume.asset";
        var profile=AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
        if(!profile)
        {
            profile=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(profile,path);
            var env=profile.Add<VisualEnvironment>(true);env.skyType.value=(int)SkyType.Gradient;
            var sky=profile.Add<GradientSky>(true);sky.top.value=new Color(.002f,.004f,.012f);sky.middle.value=new Color(.009f,.014f,.03f);sky.bottom.value=new Color(.003f,.004f,.008f);
            var exposure=profile.Add<Exposure>(true);exposure.mode.value=ExposureMode.Fixed;exposure.fixedExposure.value=4;
            var tone=profile.Add<Tonemapping>(true);tone.mode.value=TonemappingMode.ACES;
            foreach(var component in profile.components)AssetDatabase.AddObjectToAsset(component,profile);
        }
        var volume=root.AddComponent<Volume>();volume.isGlobal=true;volume.priority=100;volume.sharedProfile=profile;
        if(GameObject.Find("Main front window assemblies"))RefineFilmRearLanding();
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    static void FoyerLamp(GameObject root,string name,Vector3 position,float intensity,float range)
    {
        var light=Child(root,name).AddComponent<Light>();light.type=LightType.Point;light.transform.position=position;
        light.color=new Color(1,.86f,.68f);light.intensity=intensity;light.range=range;light.shadows=LightShadows.None; // Point-shadow flicker confirmed in the exterior A/B test; keep these practical lights unshadowed.
        light.gameObject.AddComponent<HDAdditionalLightData>();
    }
}
