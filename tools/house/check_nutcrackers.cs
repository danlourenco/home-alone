// Copy to SCRATCH Assets/Editor only; execute SpecGreybox.CheckNutcrackers in batch mode. Never run in the walking editor.
using System;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static partial class SpecGreybox
{
    public static void CheckNutcrackers()
    {
        var scene = EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity");
        SeamRooms = JArray.Parse(File.ReadAllText("Library/SeamRooms.json")).Select(r =>
            (((JArray)r[2]).Select(p => new Vector2((float)p[0], (float)p[1])).ToList(), (float)r[0], (float)r[1])).ToList();
        float gy = (float)JObject.Parse(File.ReadAllText(GroundPath))["floor_y_m"];
        SeamRooms.AddRange(BasementRooms(gy).Select(r => (r.pts, r.y0, r.y1)));
        var source = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/LivingBuiltins.glb");
        var living = GameObject.Find("LivingBuiltins_HiFi");
        foreach (var renderer in living.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name.StartsWith("Nut_")))
        {
            var mesh = source.GetComponentsInChildren<MeshFilter>(true).FirstOrDefault(m => m.name == renderer.name);
            if (mesh) renderer.GetComponent<MeshFilter>().sharedMesh = mesh.sharedMesh;
            else renderer.enabled = false;
        }
        var names = JObject.Parse(File.ReadAllText(StorePropsPath))["pieces"].Where(p => ((string)p["name"]).StartsWith("LivingNutcracker_")).Select(p => (string)p["name"]).ToArray();
        if (names.Length != 6) throw new InvalidOperationException("Expected six replacements");
        var log = RefreshProps(string.Join(",", names));
        foreach (var name in names)
        {
            var go = GameObject.Find(name);
            if (!go || go.GetComponentsInChildren<Collider>().Length != 0) throw new InvalidOperationException("Missing prop or altered walking collision: " + name);
        }
        log += PropsCheck();
        var roots = new[] { GameObject.Find("Upstairs"), GameObject.Find("Ground") };
        // Production builds run these gates before adding the paint-can rigs. Match that scope, then restore before saving.
        var traps = roots[0].transform.Find("Traps");
        bool trapsActive = traps && traps.gameObject.activeSelf;
        if (traps) traps.gameObject.SetActive(false);
        Step("ZFightCheck"); log += ZFightCheck(roots.Append(GameObject.Find("HouseShell")).ToArray());
        Step("ClashCheck"); log += ClashCheck(roots);
        Step(null); log += TriangleBudget(roots);
        if (traps) traps.gameObject.SetActive(trapsActive);
        log += "Paint-can rigs excluded during surface checks, matching the production build; restored before save.\n";
        File.WriteAllText(Path.Combine(CaptureDir, "nutcracker-check.txt"), log);
        if (!log.Contains("6 store models, 0 problems") || !log.Contains("0 coplanar pairs") || !log.Contains("0 parts passing"))
            throw new InvalidOperationException("Nutcracker verification failed; see nutcracker-check.txt");
        if (!EditorSceneManager.SaveScene(scene)) throw new IOException("Could not save verified scratch scene");
        Debug.Log("Nutcracker check PASS; scratch scene updated with existing lighting preserved.");
    }
}
