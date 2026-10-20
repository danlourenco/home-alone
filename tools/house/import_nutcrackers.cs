// Run through Unity CLI eval after purchased_nutcrackers.py; this file is outside Assets to avoid a Play-mode recompile.
var directory = "Assets/Purchased/Nutcrackers";
var report = Newtonsoft.Json.Linq.JObject.Parse(System.IO.File.ReadAllText(directory + "/import.json"));
var preview = UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
var indexPath = System.IO.Path.GetFullPath(UnityEngine.Application.dataPath + "/../../../sfm-work/props/index.json");
var index = System.IO.File.Exists(indexPath) ? Newtonsoft.Json.Linq.JObject.Parse(System.IO.File.ReadAllText(indexPath))
    : new Newtonsoft.Json.Linq.JObject { ["models"] = new Newtonsoft.Json.Linq.JArray() };
var models = (Newtonsoft.Json.Linq.JArray)index["models"];
var result = new Newtonsoft.Json.Linq.JArray();
try
{
    UnityEditor.AssetDatabase.ImportAsset(directory, UnityEditor.ImportAssetOptions.ImportRecursive | UnityEditor.ImportAssetOptions.ForceSynchronousImport);
    foreach (var variant in new[] { "Red", "Green" })
    {
        var materials = new System.Collections.Generic.Dictionary<string, UnityEngine.Material>();
        foreach (var property in ((Newtonsoft.Json.Linq.JObject)report[variant]["materials"]).Properties())
        {
            var data = property.Value;
            UnityEngine.Texture Load(string field, bool linear = false, bool normal = false)
            {
                if (data[field].Type == Newtonsoft.Json.Linq.JTokenType.Null) return null;
                var path = directory + "/" + (string)data[field];
                var importer = (UnityEditor.TextureImporter)UnityEditor.AssetImporter.GetAtPath(path);
                if (importer == null) throw new System.InvalidOperationException("Texture not imported: " + path);
                importer.sRGBTexture = !linear;
                importer.textureType = normal ? UnityEditor.TextureImporterType.NormalMap : UnityEditor.TextureImporterType.Default;
                importer.maxTextureSize = 2048; importer.mipmapEnabled = true; importer.anisoLevel = 8;
                importer.SaveAndReimport();
                return UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Texture2D>(path);
            }
            var baseMap = Load("base"); var mask = Load("mask", true); var normalMap = Load("normal", true, true);
            var path = directory + "/" + property.Name + ".mat";
            var material = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Material>(path);
            if (!material)
            {
                material = new UnityEngine.Material(UnityEngine.Shader.Find("HDRP/Lit"));
                UnityEditor.AssetDatabase.CreateAsset(material, path);
            }
            material.SetColor("_BaseColor", UnityEngine.Color.white);
            material.SetTexture("_BaseColorMap", baseMap); material.SetTexture("_MaskMap", mask); material.SetTexture("_NormalMap", normalMap);
            material.SetFloat("_Metallic", 1); material.SetFloat("_Smoothness", 1);
            material.SetFloat("_MetallicRemapMin", 0); material.SetFloat("_MetallicRemapMax", 1);
            material.SetFloat("_SmoothnessRemapMin", 0); material.SetFloat("_SmoothnessRemapMax", 1);
            material.SetFloat("_NormalScale", 0.65f);
            bool cutout = (bool)data["cutout"];
            material.SetFloat("_AlphaCutoffEnable", cutout ? 1 : 0); material.SetFloat("_AlphaCutoff", 0.3f);
            material.SetFloat("_DoubleSidedEnable", cutout ? 1 : 0); material.SetFloat("_CullMode", cutout ? 0 : 2);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(material);
            UnityEditor.EditorUtility.SetDirty(material); materials[property.Name] = material;
        }
        var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(directory + "/" + variant + ".glb");
        if (!model) throw new System.InvalidOperationException("Missing model: " + variant);
        var go = (UnityEngine.GameObject)UnityEditor.PrefabUtility.InstantiatePrefab(model, preview);
        UnityEditor.PrefabUtility.UnpackPrefabInstance(go, UnityEditor.PrefabUnpackMode.Completely, UnityEditor.InteractionMode.AutomatedAction);
        var renderers = go.GetComponentsInChildren<UnityEngine.Renderer>();
        foreach (var renderer in renderers)
            renderer.sharedMaterials = renderer.sharedMaterials.Select(m => materials[m.name.Replace(" (Instance)", "")]).ToArray();
        var bounds = renderers.Aggregate(renderers[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
        if (System.Math.Abs(bounds.size.y - 0.355f) > 0.001f) throw new System.InvalidOperationException("Wrong figure height: " + bounds);
        var prefabPath = directory + "/" + variant + ".prefab";
        UnityEditor.PrefabUtility.SaveAsPrefabAsset(go, prefabPath);
        var row = new Newtonsoft.Json.Linq.JObject { ["path"] = prefabPath, ["name"] = "Nutcracker " + variant,
            ["size"] = new Newtonsoft.Json.Linq.JArray(bounds.size.x, bounds.size.z, bounds.size.y) };
        foreach (var old in models.Where(m => (string)m["path"] == prefabPath).ToArray()) old.Remove();
        models.Add(row); result.Add(row.DeepClone());
        UnityEngine.Object.DestroyImmediate(go);
    }
    UnityEditor.AssetDatabase.SaveAssets();
    System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(indexPath));
    System.IO.File.WriteAllText(indexPath, index.ToString());
    System.IO.File.WriteAllText("/tmp/ha-nut-import-result.json", result.ToString());
}
finally
{
    UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(preview);
}
