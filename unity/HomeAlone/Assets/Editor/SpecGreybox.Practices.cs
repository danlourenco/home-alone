using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

// Practices check (Oct 20, user: "stick to Unity 6 best practices for anything you're generating yourself"): the scene-level half of
// tools/house/unity_practices.py (which checks sources, .mat files and texture imports). Counts, over the built scene:
//  (a) meshes drawn >= 8 times by renderers outside any LODGroup (repeated vegetation and props want LODs / a cull distance)
//  (b) MeshColliders on foliage-named objects (foliage takes no collider, or a box/capsule)
//  (c) renderers using a material instance ("(Instance)" in the name, or a material that is not an asset): per-renderer copies break
//      SRP Batcher sharing and are lost on the next build
//  (d) shaders in use that HDRP's SRP Batcher rejects, read through UnityEditor.ShaderUtil's internal compatibility code when this
//      Unity exposes it (reflection); otherwise the line says it is skipped
// Like the other gates, a count that is new against HEAD's report is a failure until explained.
public static partial class SpecGreybox
{
    static readonly Regex PracticeFoliage = new Regex("(?i)(shrub|foliage|hedge|grass|ivy|needle|bush|fern|leaves|plant|boxwood|yew|_leaf|_ball|fir)");

    static string PracticesCheck()
    {
        var rs = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include);
        string Top(System.Collections.Generic.IEnumerable<string> names) => string.Join(", ", names.Take(6));

        // (a)
        var inLod = new System.Collections.Generic.HashSet<Renderer>(Object.FindObjectsByType<LODGroup>(FindObjectsInactive.Include)
            .SelectMany(g => g.GetLODs().SelectMany(l => l.renderers)).Where(r => r != null));
        var repeats = rs.Where(r => !inLod.Contains(r)).Select(r => r.GetComponent<MeshFilter>()?.sharedMesh).Where(m => m != null)
            .GroupBy(m => m).Select(g => (mesh: g.Key.name, n: g.Count())).Where(x => x.n >= 8).OrderByDescending(x => x.n).ToList();
        // (b)
        var colliders = Object.FindObjectsByType<MeshCollider>(FindObjectsInactive.Include).Where(c => PracticeFoliage.IsMatch(c.name)).Select(c => c.name).ToList();
        // (c)
        var inst = rs.Where(r => r.sharedMaterials.Any(m => m != null && (m.name.Contains("(Instance)") || !AssetDatabase.Contains(m))))
            .Select(r => r.name + ":" + r.sharedMaterials.First(m => m != null && (m.name.Contains("(Instance)") || !AssetDatabase.Contains(m))).name).ToList();
        // (d)
        string d;
        var code = typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityCode", BindingFlags.Static | BindingFlags.NonPublic | BindingFlags.Public);
        if (code == null) d = "(d) SRP Batcher: skipped (this Unity exposes no compatibility API)";
        else
        {
            var shaders = rs.SelectMany(r => r.sharedMaterials).Where(m => m != null && m.shader != null).Select(m => m.shader).Distinct().ToList();
            int failed = 0; var bad = new System.Collections.Generic.List<string>();
            foreach (var s in shaders)
            {
                try { if (System.Convert.ToInt32(code.Invoke(null, new object[] { s, 0, 0 })) != 0) bad.Add(s.name); }
                catch { failed++; }
            }
            d = failed == shaders.Count ? $"(d) SRP Batcher: skipped (ShaderUtil.GetSRPBatcherCompatibilityCode did not answer for any of {shaders.Count} shaders)"
                : $"(d) {bad.Count} of {shaders.Count} shaders not SRP Batcher compatible (pass 0)" + (bad.Count > 0 ? " (" + Top(bad) + ")" : "") + (failed > 0 ? $", {failed} unanswered" : "");
        }
        return $"Practices check: (a) {repeats.Count} meshes drawn >= 8 times outside a LODGroup" + (repeats.Count > 0 ? " (" + Top(repeats.Select(x => $"{x.mesh} x{x.n}")) + ")" : "")
            + $"; (b) {colliders.Count} MeshColliders on foliage" + (colliders.Count > 0 ? " (" + Top(colliders) + ")" : "")
            + $"; (c) {inst.Count} renderers on material instances" + (inst.Count > 0 ? " (" + Top(inst) + ")" : "")
            + "; " + d + "\n";
    }
}
