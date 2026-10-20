// Old colour meshes share nutcrackers with other decorations. Preview their regenerated remainders without moving static batches.
var root = UnityEngine.GameObject.Find("LivingBuiltins_HiFi");
UnityEditor.AssetDatabase.ImportAsset("Assets/Models/Foyer/LivingBuiltins.glb", UnityEditor.ImportAssetOptions.ForceUpdate | UnityEditor.ImportAssetOptions.ForceSynchronousImport);
var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Models/Foyer/LivingBuiltins.glb");
if (!root || !model) throw new System.InvalidOperationException("Living built-ins not found");
var oldParts = root.GetComponentsInChildren<UnityEngine.MeshRenderer>(true).Where(r => r.name.StartsWith("Nut_")).ToArray();
foreach (var old in oldParts)
{
    var previous = old.transform.parent.Find("NutRemainder_" + old.name);
    if (previous) UnityEngine.Object.DestroyImmediate(previous.gameObject);
    var source = model.GetComponentsInChildren<UnityEngine.MeshFilter>(true).FirstOrDefault(m => m.name == old.name);
    if (source)
    {
        var go = new UnityEngine.GameObject("NutRemainder_" + old.name);
        go.transform.SetParent(old.transform.parent, false);
        go.transform.localPosition = old.transform.localPosition;
        go.transform.localRotation = old.transform.localRotation;
        go.transform.localScale = old.transform.localScale;
        go.AddComponent<UnityEngine.MeshFilter>().sharedMesh = source.sharedMesh;
        var renderer = go.AddComponent<UnityEngine.MeshRenderer>();
        renderer.sharedMaterials = old.sharedMaterials;
        renderer.shadowCastingMode = old.shadowCastingMode;
        renderer.receiveShadows = old.receiveShadows;
        renderer.lightProbeUsage = old.lightProbeUsage;
        renderer.reflectionProbeUsage = old.reflectionProbeUsage;
        renderer.enabled = true;
    }
    old.enabled = false;
}
foreach (var renderer in root.GetComponentsInChildren<UnityEngine.MeshRenderer>(true))
    if (System.Text.RegularExpressions.Regex.IsMatch(renderer.name, "^Nutcracker[0-9]{2}_")) renderer.enabled = false;
System.IO.File.WriteAllText("/tmp/ha-nut-preview-ready.txt", "Old shared meshes hidden; non-nutcracker remainders restored.");
