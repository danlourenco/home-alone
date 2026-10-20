using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// FACADE SUN (walk note 2026-10-20T14:16:50, the porch: "why are the shadows on the lower floor? what is blocking the suns rays?? the tree
// makes sense, the big shades does not"; film 4382 has the ground-floor front sunlit apart from the shutters and trees). Points 3 cm in
// front of the lower front brick face (the exterior skin's FRONT_MAIN, spec/exterior_shell.json), grade + 0.45 m up to the upper sills,
// the portico's span left out (its own shade is real), each ray toward the sun against the shadow casters the sun uses while the player
// is on the ground floor: enabled renderers that cast and carry a layer of StoreyShadows.groundMask (temporary mesh colliders, as
// OpeningFaceCheck). A hit on anything outside the outdoor roots (Exterior, HouseShell: the film's skin, trees, shrubs, shutters) fails:
// that is an interior piece (Marina's upstairs strip, 1.2-1.5 m past the film's front, DEVIATIONS 1/45) shading the facade.
// Standalone on a saved scene: -executeMethod SpecGreybox.FacadeSunCheckScene (Library/FacadeSunCheck.txt).
public static partial class SpecGreybox
{
    public static void FacadeSunCheckScene()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/House_WallGrid.unity", OpenSceneMode.Single);
        var r = FacadeSunCheck();
        File.WriteAllText("Library/FacadeSunCheck.txt", r); Debug.Log(r);
    }

    static readonly HashSet<string> OutdoorRoots = new HashSet<string> { "Exterior", "HouseShell" };

    static string FacadeSunCheck()
    {
        var ss = Object.FindObjectsByType<StoreyShadows>(FindObjectsInactive.Include).FirstOrDefault();
        if (ss == null) return "Facade sun check: FAIL no sun with StoreyShadows\n";
        var sh = JObject.Parse(File.ReadAllText(Path.Combine(RepoRoot, "spec/exterior_shell.json")));
        float xf = (float)sh["front_main"], gf = (float)sh["ground_floor"], top = 0.464f - 0.10f;   // upper sills (exterior_shell UPPER_DY) less 10 cm
        var toSun = -ss.transform.forward; uint mask = ss.groundMask;
        var temp = new List<Collider>();
        foreach (var mr in Object.FindObjectsByType<MeshRenderer>())
            if (mr.enabled && mr.shadowCastingMode != ShadowCastingMode.Off && (mr.renderingLayerMask & mask) != 0 && mr.GetComponent<Collider>() == null
                && mr.GetComponent<MeshFilter>()?.sharedMesh is Mesh mesh)
            { var mc = mr.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mesh; temp.Add(mc); }
        Physics.SyncTransforms();
        string PathOf(Transform t) { var s = t.name; while (t.parent != null) { t = t.parent; s = t.name + "/" + s; } return s; }
        var bad = new Dictionary<string, int>(); var at = new Dictionary<string, (float z0, float z1, float y0, float y1, Vector3 h)>(); var ok = new Dictionary<string, int>(); int n = 0, shaded = 0;
        for (float z = 2.95f; z < 16.15f; z += 0.10f)
        {
            if (z > 8.2f && z < 11.25f) continue;   // the portico (columns 2.8 m apart on the door's axis z 9.716, entablature 1.3 m out)
            for (float y = gf + 0.45f; y <= top; y += 0.10f)
            {
                n++; var o = new Vector3(xf + 0.03f, y, -z) + toSun * 0.02f; bool any = false;
                // from the sun's side back to the point: a caster the point stands inside (a skin proud of the brick) is met on its sun-facing
                // face, which a ray starting inside it never reports
                foreach (var h in Physics.RaycastAll(o + toSun * 60f, -toSun, 60f, ~0, QueryTriggerInteraction.Ignore))
                {
                    var r = h.collider.GetComponent<MeshRenderer>();
                    if (r == null || !r.enabled || r.shadowCastingMode == ShadowCastingMode.Off || (r.renderingLayerMask & mask) == 0) continue;
                    any = true; var p = PathOf(h.collider.transform); string k = string.Join("/", p.Split('/').Take(3));
                    if (OutdoorRoots.Contains(p.Split('/')[0])) ok[k] = ok.GetValueOrDefault(k) + 1;
                    else { bad[k] = bad.GetValueOrDefault(k) + 1; var e = at.TryGetValue(k, out var e0) ? e0 : (99f, -99f, 99f, -99f, h.point); at[k] = (Mathf.Min(e.Item1, z), Mathf.Max(e.Item2, z), Mathf.Min(e.Item3, y), Mathf.Max(e.Item4, y), e.Item5); }
                }
                if (any) shaded++;
            }
        }
        foreach (var c in temp) Object.DestroyImmediate(c);
        Physics.SyncTransforms();
        int nb = bad.Values.DefaultIfEmpty(0).Sum();
        return $"Facade sun check: {n} points on the lower front, {shaded} shaded, {bad.Count} interior casters ({nb} ray hits) shading it (sun mask {mask})\n"
               + string.Concat(bad.OrderByDescending(kv => kv.Value).Take(20).Select(kv => $"SHADES  {kv.Key} ({kv.Value} rays; facade spec z {at[kv.Key].z0:F2}-{at[kv.Key].z1:F2}, y {at[kv.Key].y0:F2}-{at[kv.Key].y1:F2}; first hit at spec ({at[kv.Key].h.x:F2}, {at[kv.Key].h.y:F2}, {-at[kv.Key].h.z:F2}))\n"))
               + string.Concat(ok.OrderByDescending(kv => kv.Value).Take(8).Select(kv => $"outdoor {kv.Key} ({kv.Value} rays)\n"));
    }
}
