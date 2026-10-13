using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SurveyBuilder
{
    static Bounds FoyerBenchmarkBounds=new Bounds(new Vector3(1.8f,4.8f,5.2f),new Vector3(6.5f,7.5f,12));
    public static string AuditFoyerBenchmark()
    {
        var meshes=GameObject.Find("IntactGLB").GetComponentsInChildren<MeshFilter>().Where(m=>m.GetComponent<Renderer>().enabled&&m.GetComponent<Renderer>().bounds.Intersects(FoyerBenchmarkBounds)).ToArray();
        return string.Join("\n",meshes.Select(m=>m.name+" vertices="+m.sharedMesh.vertexCount+" uv2="+m.sharedMesh.uv2.Length+" size="+m.GetComponent<Renderer>().bounds.size.ToString("F1")));
    }
    public static string PrepareFoyerBenchmark()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Leave Play first.");
        const string folder="Assets/Lighting/FoyerBenchmark";System.IO.Directory.CreateDirectory(folder);AssetDatabase.Refresh();
        var root=GameObject.Find("Foyer lighting benchmark")??new GameObject("Foyer lighting benchmark");
        var state=root.GetComponent<FoyerBakedLighting>()??root.AddComponent<FoyerBakedLighting>();
        var sources=new[]{GameObject.Find("IntactGLB"),GameObject.Find("FoyerNight"),GameObject.Find("Film rear landing"),GameObject.Find("Film linen closet door"),GameObject.Find("Film upper hall dressing")};
        var meshes=sources.Where(g=>g).SelectMany(g=>g.GetComponentsInChildren<MeshFilter>()).Where(m=>m.sharedMesh&&m.GetComponent<MeshRenderer>()&&m.GetComponent<MeshRenderer>().enabled&&m.GetComponent<Renderer>().bounds.Intersects(FoyerBenchmarkBounds)&&m.GetComponent<Renderer>().sharedMaterials.All(mat=>mat&&(!mat.HasProperty("_SurfaceType")||mat.GetFloat("_SurfaceType")==0))).ToArray();
        foreach(var mf in meshes){
            if(mf.sharedMesh.uv2.Length==0){
                string path=folder+"/UV_"+Guid.NewGuid().ToString("N")+".asset";
                var mesh=UnityEngine.Object.Instantiate(mf.sharedMesh);mesh.name=mf.name+" lightmap UV";
                if(!Unwrapping.GenerateSecondaryUVSet(mesh))throw new InvalidOperationException("UV unwrap failed: "+mf.name);
                AssetDatabase.CreateAsset(mesh,path);mf.sharedMesh=mesh;
            }
            // Day/night atlases have different UV offsets; static batching would burn one set into the mesh.
            GameObjectUtility.SetStaticEditorFlags(mf.gameObject,(GameObjectUtility.GetStaticEditorFlags(mf.gameObject)|StaticEditorFlags.ContributeGI)&~StaticEditorFlags.BatchingStatic);
            mf.GetComponent<MeshRenderer>().receiveGI=ReceiveGI.Lightmaps;
        }
        state.surfaces=meshes.Select(m=>(Renderer)m.GetComponent<MeshRenderer>()).ToArray();
        // Preparing changed geometry invalidates the old renderer-to-atlas assignments.
        // Retain copied textures on disk, but require fresh day and night bakes for this surface list.
        state.day=new FoyerBakedLighting.State();state.night=new FoyerBakedLighting.State();
        var settings=AssetDatabase.LoadAssetAtPath<LightingSettings>(folder+"/Settings.asset");
        if(!settings){settings=new LightingSettings();AssetDatabase.CreateAsset(settings,folder+"/Settings.asset");}
        settings.bakedGI=true;settings.realtimeGI=false;settings.lightmapper=LightingSettings.Lightmapper.ProgressiveGPU;
        settings.lightmapResolution=12;settings.lightmapMaxSize=1024;settings.lightmapPadding=4;settings.maxBounces=3;
        settings.mixedBakeMode=MixedLightingMode.IndirectOnly;LightmapSettings.lightmapsMode=LightmapsMode.CombinedDirectional;
        settings.ao=true;settings.aoMaxDistance=.25f;settings.aoExponentIndirect=1;settings.aoExponentDirect=.3f;
        Lightmapping.lightingSettings=settings;EditorUtility.SetDirty(settings);
        if(root.GetComponentsInChildren<ReflectionProbe>().Length==0){
            foreach(var p in new[]{new Vector3(2.2f,2.9f,4),new Vector3(2.1f,6.7f,7.4f)}){
                var go=Child(root,"Foyer room reflection");go.transform.position=p;
                var probe=go.AddComponent<ReflectionProbe>();probe.resolution=128;probe.mode=ReflectionProbeMode.Realtime;probe.size=new Vector3(6.2f,4.1f,11);
                var hd=go.AddComponent<HDAdditionalReflectionData>();hd.mode=ProbeSettings.Mode.Realtime;hd.realtimeMode=ProbeSettings.RealtimeMode.OnDemand;
                hd.influenceVolume.boxSize=probe.size;hd.influenceVolume.boxBlendDistancePositive=Vector3.one*.4f;hd.influenceVolume.boxBlendDistanceNegative=Vector3.one*.4f;hd.timeSlicing=true;
            }
        }
        state.reflections=root.GetComponentsInChildren<HDAdditionalReflectionData>();
        for(int i=0;i<state.reflections.Length;i++){
            var p=state.reflections[i];p.transform.position=new Vector3(1.85f,i==0?2.9f:6.7f,i==0?5.2f:5.5f);
            p.influenceVolume.boxSize=new Vector3(7.4f,4.4f,13);p.timeSlicing=false;p.PrepareCulling();
        }
        var wood=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/DarkWood.mat");
        wood.SetTexture("_NormalMap",AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Textures/wood_floor_normal.jpg"));wood.SetFloat("_NormalScale",.3f);wood.SetFloat("_Smoothness",.42f);HDMaterial.ValidateMaterial(wood);EditorUtility.SetDirty(wood);
        foreach(string name in new[]{"Damask","IvoryPaint","LinenDoorIvory"}){
            var mat=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/"+name+".mat");mat.SetFloat("_Smoothness",name=="Damask"?.055f:.25f);mat.doubleSidedGI=true;HDMaterial.ValidateMaterial(mat);EditorUtility.SetDirty(mat);
        }
        EditorUtility.SetDirty(state);AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        return "Prepared "+meshes.Length+" surfaces with secondary UVs, two on-demand room reflections, wood normal detail and matte wallpaper.";
    }
    public static string BeginFoyerBake(bool night)
    {
        if(EditorApplication.isPlaying||Lightmapping.isRunning)throw new InvalidOperationException("Leave Play and wait for any bake.");
        UnityEngine.Object.FindFirstObjectByType<HouseNightMode>().SetNight(night);
        foreach(var l in GameObject.Find("FoyerNight").GetComponentsInChildren<Light>()){
            l.lightmapBakeType=LightmapBakeType.Baked;l.shadows=LightShadows.Soft;
            if(l.name=="Soft interior bounce"||l.name=="Stair reflected light")l.intensity=0;
        }
        foreach(var l in UnityEngine.Object.FindObjectsByType<Light>())if(l.type==LightType.Directional)l.lightmapBakeType=LightmapBakeType.Mixed;
        EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        if(!Lightmapping.BakeAsync()){
            foreach(var l in GameObject.Find("FoyerNight").GetComponentsInChildren<Light>()){l.lightmapBakeType=LightmapBakeType.Realtime;l.shadows=LightShadows.None;}
            throw new InvalidOperationException("Unity did not start the light bake; restored realtime lights without shadows.");
        }
        return "Started "+(night?"night":"day")+" foyer bake";
    }
    public static string FinishFoyerBake(bool night)
    {
        if(Lightmapping.isRunning)throw new InvalidOperationException("Bake still running.");
        if(LightmapSettings.lightmaps.Length==0)throw new InvalidOperationException("Bake produced no lightmaps.");
        var state=UnityEngine.Object.FindFirstObjectByType<FoyerBakedLighting>();var set=night?state.night:state.day;
        string folder="Assets/Lighting/FoyerBenchmark/"+(night?"Night":"Day");System.IO.Directory.CreateDirectory(folder);AssetDatabase.Refresh();
        set.color=new Texture2D[LightmapSettings.lightmaps.Length];set.direction=new Texture2D[set.color.Length];
        for(int i=0;i<set.color.Length;i++){
            foreach(bool direction in new[]{false,true}){
                var tex=direction?LightmapSettings.lightmaps[i].lightmapDir:LightmapSettings.lightmaps[i].lightmapColor;
                if(!tex)continue;
                string src=AssetDatabase.GetAssetPath(tex),dst=AssetDatabase.GenerateUniqueAssetPath(folder+"/"+(direction?"Direction":"Color")+i+System.IO.Path.GetExtension(src));
                if(!AssetDatabase.CopyAsset(src,dst))throw new InvalidOperationException("Cannot preserve baked texture "+src);
                (direction?set.direction:set.color)[i]=AssetDatabase.LoadAssetAtPath<Texture2D>(dst);
            }
        }
        set.index=state.surfaces.Select(r=>r.lightmapIndex).ToArray();set.scaleOffset=state.surfaces.Select(r=>r.lightmapScaleOffset).ToArray();
        foreach(var l in GameObject.Find("FoyerNight").GetComponentsInChildren<Light>())l.shadows=LightShadows.None;
        state.Apply(night);EditorUtility.SetDirty(state);AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
        return "Saved "+set.color.Length+" "+(night?"night":"day")+" lightmaps; "+set.index.Count(i=>i>=0&&i<set.color.Length)+" mapped surfaces";
    }
    public static void RefineFoyerSurfaceResponse()
    {
        var state=UnityEngine.Object.FindFirstObjectByType<FoyerBakedLighting>();
        if(!state.nightExposure){
            var go=Child(state.gameObject,"Foyer night camera exposure");go.transform.position=new Vector3(1.8f,4.8f,5.2f);
            var box=go.AddComponent<BoxCollider>();box.isTrigger=true;box.size=new Vector3(6.2f,7.2f,11.2f);
            state.nightExposure=go.AddComponent<Volume>();state.nightExposure.isGlobal=false;state.nightExposure.priority=120;state.nightExposure.blendDistance=1.2f;
            var p=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(p,"Assets/Lighting/FoyerBenchmark/LocalNightExposure.asset");
            var e=p.Add<Exposure>(true);e.mode.value=ExposureMode.Fixed;e.fixedExposure.value=2.5f;AssetDatabase.AddObjectToAsset(e,p);state.nightExposure.sharedProfile=p;
        }
        state.nightExposure.sharedProfile.TryGet<Exposure>(out var nightCamera);nightCamera.fixedExposure.value=2.5f;EditorUtility.SetDirty(nightCamera);
        if(!state.dayExposure){
            state.dayExposure=state.nightExposure.gameObject.AddComponent<Volume>();state.dayExposure.isGlobal=false;state.dayExposure.priority=120;state.dayExposure.blendDistance=1.2f;
            var p=ScriptableObject.CreateInstance<VolumeProfile>();AssetDatabase.CreateAsset(p,"Assets/Lighting/FoyerBenchmark/LocalDayExposure.asset");
            var e=p.Add<Exposure>(true);e.mode.value=ExposureMode.Automatic;e.limitMin.value=4;e.limitMax.value=10;e.adaptationMode.value=AdaptationMode.Fixed;
            AssetDatabase.AddObjectToAsset(e,p);state.dayExposure.sharedProfile=p;
        }
        if(!state.dayExposure.sharedProfile.TryGet<IndirectLightingController>(out var indirect)){
            indirect=state.dayExposure.sharedProfile.Add<IndirectLightingController>();AssetDatabase.AddObjectToAsset(indirect,state.dayExposure.sharedProfile);
        }
        indirect.reflectionLightingMultiplier.Override(1);EditorUtility.SetDirty(indirect);
        // SSR masked valid local cubemaps with a blue sky wash in matched-camera A/B tests.
        // Use the captured room reflections inside this volume; exterior settings remain independent.
        foreach(var volume in new[]{state.dayExposure,state.nightExposure}){
            if(!volume.sharedProfile.TryGet<ScreenSpaceReflection>(out var ssr)){
                ssr=volume.sharedProfile.Add<ScreenSpaceReflection>();AssetDatabase.AddObjectToAsset(ssr,volume.sharedProfile);
            }
            ssr.enabled.Override(false);EditorUtility.SetDirty(ssr);
        }
        // Convert roughness data to HDRP's packed mask channels; no invented surface pattern.
        var rough=new Texture2D(2,2,TextureFormat.RGBA32,false,true);rough.LoadImage(System.IO.File.ReadAllBytes("Assets/Textures/wood_floor_rough.jpg"));
        var pixels=rough.GetPixels();for(int i=0;i<pixels.Length;i++)pixels[i]=new Color(0,1,1,1-pixels[i].r);
        rough.SetPixels(pixels);rough.Apply();string path="Assets/Lighting/FoyerBenchmark/WoodMask.png";System.IO.File.WriteAllBytes(path,rough.EncodeToPNG());UnityEngine.Object.DestroyImmediate(rough);
        AssetDatabase.ImportAsset(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);importer.sRGBTexture=false;importer.SaveAndReimport();
        var wood=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/IntactFoyer/DarkWood.mat");wood.SetTexture("_MaskMap",AssetDatabase.LoadAssetAtPath<Texture2D>(path));wood.SetFloat("_SmoothnessRemapMin",.20f);wood.SetFloat("_SmoothnessRemapMax",.60f);HDMaterial.ValidateMaterial(wood);EditorUtility.SetDirty(wood);
        state.Apply(UnityEngine.Object.FindFirstObjectByType<HouseNightMode>().night);EditorUtility.SetDirty(state);AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene());
    }
    public static string CheckFoyerBenchmark()
    {
        var s=UnityEngine.Object.FindFirstObjectByType<FoyerBakedLighting>();
        if(!s||s.day.color==null||s.night.color==null||s.day.color.Length==0||s.night.color.Length==0)throw new InvalidOperationException("Both lighting bakes are required.");
        foreach(var set in new[]{s.day,s.night}){
            if(set.color.Any(t=>!t)||set.direction.Any(t=>!t)||set.index.Length!=s.surfaces.Length||set.index.Any(i=>i<0||i>=set.color.Length))throw new InvalidOperationException("Invalid baked map/renderer assignment.");
        }
        if(s.surfaces.Any(r=>!r||r.GetComponent<MeshFilter>().sharedMesh.uv2.Length==0))throw new InvalidOperationException("Baked surface missing secondary UVs.");
        if(s.surfaces.Any(r=>r.isPartOfStaticBatch))throw new InvalidOperationException("Static batching prevents day/night lightmap offset changes.");
        return "PASS day/night lightmaps for "+s.surfaces.Length+" surfaces; secondary UVs and map assignments valid; "+CheckExteriorNight();
    }
    public static string CheckFoyerReflections()
    {
        var s=UnityEngine.Object.FindFirstObjectByType<FoyerBakedLighting>();
        foreach(var v in new[]{s.dayExposure,s.nightExposure})
            if(!v.sharedProfile.TryGet<ScreenSpaceReflection>(out var ssr)||!ssr.enabled.overrideState||ssr.enabled.value)throw new InvalidOperationException("Interior SSR override missing.");
        foreach(var p in s.reflections){
            if(!p.realtimeTexture||p.weight<=0)throw new InvalidOperationException("Room probe inactive.");
            var read=AsyncGPUReadback.Request(p.realtimeTexture,0,TextureFormat.RGBAFloat);read.WaitForCompletion();
            if(read.hasError)throw new InvalidOperationException("Probe GPU readback failed.");
            for(int face=0;face<6;face++){
                var data=read.GetData<Color>(face);float max=0;
                foreach(var c in data){if(float.IsNaN(c.r)||float.IsInfinity(c.r))throw new InvalidOperationException("Invalid probe pixel.");max=Mathf.Max(max,c.r,c.g,c.b);}
                if(max<=0)throw new InvalidOperationException("Empty room cubemap face "+face);
            }
        }
        foreach(var point in new[]{new Vector3(-1.15f,1.31f,4),new Vector3(2.1f,6.5f,1.71f)})
            if(!s.reflections.Any(p=>p.bounds.Contains(point)))throw new InvalidOperationException("Hall surface outside reflection coverage: "+point);
        return "PASS two room probes, all twelve HDR faces nonempty; local SSR disabled";
    }
}
