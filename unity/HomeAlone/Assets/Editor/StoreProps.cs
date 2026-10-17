using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// Asset Store furniture (spec/dressing/store_props.json) fitted into measured boxes. The packs are gitignored (licence: use, not
// redistribution), so a missing prefab only warns and the grey-box dressing box stays.
public static partial class SpecGreybox
{
    static void StoreProps(GameObject root, GameObject groot, float gy)
    {
        var fp = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/store_props.json"));
        if (!File.Exists(fp)) return;
        var gUp = Child(root, "StoreProps"); var gGround = Child(groot, "StoreProps"); PropRecords.Clear(); Converted.Clear();
        foreach (var p in JObject.Parse(File.ReadAllText(fp))["pieces"])
        {
            string name = (string)p["name"], path = (string)p["prefab"];
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab == null) { Debug.LogWarning($"StoreProps: {name}: {path} not imported; the grey-box box stays"); continue; }
            bool upper = (string)p["floor"] == "upper";   // spec y above the upper floor (0) instead of the ground floor
            var g = upper ? gUp : gGround; float fy = upper ? 0f : gy;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, g.transform);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.name = name;
            foreach (var c in go.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
            foreach (var mb in go.GetComponentsInChildren<MonoBehaviour>()) Object.DestroyImmediate(mb);   // pack scripts (door openers etc.): visuals only
            foreach (var hp in p["hide_parts"] ?? new JArray())   // parts of the pack's model left out (the tree's warm-white mini lights: the film's are C7s)
                foreach (var t in go.GetComponentsInChildren<Transform>().Where(t => t != null && t.name == (string)hp).ToList()) Object.DestroyImmediate(t.gameObject);
            var rs = go.GetComponentsInChildren<Renderer>();
            if (rs.Length == 0) { Debug.LogWarning($"StoreProps: {name}: no renderers"); Object.DestroyImmediate(go); continue; }
            // target box in Unity coordinates (z = -spec z), feet on y0 above the ground floor
            float x0 = (float)p["x"][0], x1 = (float)p["x"][1], z0 = -(float)p["z"][1], z1 = -(float)p["z"][0];
            go.transform.localScale = Vector3.one;
            float yaw = p["yaw"] != null ? (float)p["yaw"] : Orient(go, x1 - x0 > z1 - z0, Back((string)p["back"]));   // "yaw": a free-standing piece (no wall behind it) turned by hand
            go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.Euler(0, yaw, 0));
            var b = rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
            float h = (float)p["height"], y0 = (float)p["y0"] + fy;
            var s = new Vector3((x1 - x0) / b.size.x, h / b.size.y, (z1 - z0) / b.size.z);   // world axes
            if (Mathf.RoundToInt(yaw / 90f) % 2 == 1) s = new Vector3(s.z, s.y, s.x);          // turned 90/270: local x lies along world z
            go.transform.localScale = s;
            b = rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
            go.transform.position += new Vector3((x0 + x1) / 2 - b.center.x, y0 - b.min.y, (z0 + z1) / 2 - b.center.z);
            if (p["open"] != null)
            {   // bake the uneven fit into the parts (an unstretched holder, world sizes kept): turning a part inside a non-uniformly
                // scaled parent shears it (the open leaf came out 0.41 m wide, Oct 16)
                var holder = new GameObject(name); holder.transform.SetParent(g.transform, false);
                foreach (var t in go.transform.Cast<Transform>().ToList()) t.SetParent(holder.transform, true);
                Object.DestroyImmediate(go); go = holder; rs = go.GetComponentsInChildren<Renderer>();
            }
            foreach (var r in rs)
            {
                r.sharedMaterials = r.sharedMaterials.Select(HdrpOrConvert).ToArray();
                r.shadowCastingMode = ShadowCastingMode.On;
            }
            foreach (var t in go.GetComponentsInChildren<Transform>()) t.gameObject.isStatic = true;
            if (p["collide"] != null && (bool)p["collide"])
            {   // one box for the walk layer, the size of what is drawn
                b = rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
                var col = new GameObject(name + "_Collider"); col.transform.parent = g.transform;
                var bc = col.AddComponent<BoxCollider>(); bc.center = b.center; bc.size = b.size;
            }
            // hide the placeholders it replaces: renderers of that name touching the piece's box (their colliders stay: walking unchanged)
            var reach = new Bounds { min = new Vector3(x0, y0, z0), max = new Vector3(x1, y0 + h, z1) }; reach.Expand(0.1f);
            foreach (var hn in p["hides"] ?? new JArray())
                foreach (var r in Object.FindObjectsByType<MeshRenderer>())
                    if (r.name == (string)hn && !r.transform.IsChildOf(go.transform) && r.bounds.Intersects(reach)) r.enabled = false;
            var fb = rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
            // a walk-through doorway: the leaf ("leaf" child, default "Door") stands open by `open` degrees into the room (toward `back`),
            // hinged on the `hinge` end of the opening ("lo"/"hi" along the wall, spec), 1.2 cm inside it (no face flush with the cut)
            Transform swung = null;
            if (p["open"] != null)
            {
                swung = go.GetComponentsInChildren<Transform>().FirstOrDefault(t => t.name == ((string)p["leaf"] ?? "Door"));
                if (swung == null) Debug.LogWarning($"StoreProps {name}: no leaf to open");
                else
                {
                    var lb = swung.GetComponentsInChildren<Renderer>().Aggregate((Bounds?)null, (a, r) => { if (a == null) return r.bounds; var q = a.Value; q.Encapsulate(r.bounds); return q; }).Value;
                    var bk = Back((string)p["back"]); bool wallAlongZ = Mathf.Abs(bk.x) > 0.5f;   // the wall runs along z when the back faces x
                    bool hiEnd = (string)p["hinge"] == "hi";   // spec "hi" end; Unity z = -spec z flips it on z-walls
                    float edge = wallAlongZ ? (hiEnd ? lb.min.z : lb.max.z) : (hiEnd ? lb.max.x : lb.min.x);
                    float inset = 0.012f * (wallAlongZ ? (hiEnd ? 1 : -1) : (hiEnd ? -1 : 1));
                    var face = Vector3.Dot(lb.center, bk) - Vector3.Dot(lb.extents, new Vector3(Mathf.Abs(bk.x), 0, Mathf.Abs(bk.z)));
                    var pivot = wallAlongZ ? new Vector3(lb.center.x, 0, edge + inset) : new Vector3(edge + inset, 0, lb.center.z);
                    float ang = (float)p["open"];
                    var start = swung.position; var startRot = swung.rotation;
                    swung.RotateAround(pivot, Vector3.up, ang);
                    float plus = Vector3.Dot(swung.GetComponentsInChildren<Renderer>()[0].bounds.center, bk);
                    swung.SetPositionAndRotation(start, startRot); swung.RotateAround(pivot, Vector3.up, -ang);
                    float minus = Vector3.Dot(swung.GetComponentsInChildren<Renderer>()[0].bounds.center, bk);
                    if ((string)p["swing"] == "out") (plus, minus) = (minus, plus);   // swings into the hall, away from `back`
                    if (plus > minus) { swung.SetPositionAndRotation(start, startRot); swung.RotateAround(pivot, Vector3.up, ang); }
                    var sb = swung.GetComponentsInChildren<Renderer>().Aggregate((Bounds?)null, (a, r) => { if (a == null) return r.bounds; var q = a.Value; q.Encapsulate(r.bounds); return q; }).Value;
                    Debug.Log($"StoreProps {name}: leaf open {ang} deg at {pivot}, now {sb.min} .. {sb.max}");
                }
            }
            PropRecords.Add((name, go, new Bounds { min = new Vector3(x0, y0, z0), max = new Vector3(x1, y0 + h, z1) }, Back((string)p["back"]), g, swung));
            Debug.Log($"StoreProps {name}: yaw {yaw}, scale {go.transform.localScale}, bounds {fb.min} .. {fb.max}");
        }
    }

    static readonly System.Collections.Generic.List<(string name, GameObject go, Bounds box, Vector3 back, GameObject root, Transform swung)> PropRecords = new();

    // Props check (a build gate, Oct 16): every assumption made placing a store model, measured on what was built.
    //  fit   - drawn bounds within 1 cm of the measured box on every face (caught the 90-degree axis swap)
    //  back  - the flat back 0-3 cm from the DRAWN wall (rays from the back face; plan faces lie: wainscot caps, panels)
    //  feet  - the lowest point within 1 cm of the drawn floor under it (carpet, landing)
    //  mats  - every material HDRP, with a base colour map unless transparent (URP packs import with the error shader)
    static string PropsCheck()
    {
        var bad = new System.Collections.Generic.List<string>(); Physics.SyncTransforms();
        foreach (var (name, go, box, back, root, swung) in PropRecords)
        {
            if (go == null) continue;
            var rs = go.GetComponentsInChildren<Renderer>();
            var fixedRs = rs.Where(r => swung == null || !r.transform.IsChildOf(swung)).ToArray();   // an open leaf leaves its box by design
            var b = fixedRs.Aggregate(fixedRs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
            var d0 = b.min - box.min; var d1 = b.max - box.max;
            float fit = new[] { d0.x, d0.y, d0.z, d1.x, d1.y, d1.z }.Max(Mathf.Abs);
            if (fit > 0.01f) bad.Add($"{name}: drawn bounds {fit * 100:F1} cm off its box");
            // rays hit what is DRAWN: temporary mesh colliders on every visible renderer near the piece (carpet, cap rail and
            // wainscot have none of their own); the piece itself and the hidden placeholder it replaces don't count
            var temp = new System.Collections.Generic.List<Collider>(); var near = b; near.Expand(1.2f);
            foreach (var r in Object.FindObjectsByType<MeshRenderer>())
                if (r.enabled && !r.transform.IsChildOf(go.transform) && r.bounds.Intersects(near) && r.GetComponent<MeshFilter>()?.sharedMesh != null)
                { var mc = r.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = r.GetComponent<MeshFilter>().sharedMesh; temp.Add(mc); }
            Physics.SyncTransforms();
            bool Mine(RaycastHit hit) => hit.collider.transform.IsChildOf(go.transform)   // the piece itself; other props are drawn surfaces (a lamp on a table)
                || !(hit.collider.TryGetComponent<Renderer>(out var hr) && hr.enabled);   // only what is drawn counts (not walk-layer boxes or hidden placeholders)
            float Cast(Vector3 o, Vector3 d, float len) =>
                Physics.RaycastAll(o, d, len, ~0, QueryTriggerInteraction.Ignore).Where(hh => !Mine(hh)).Select(hh => hh.distance).DefaultIfEmpty(float.NaN).Min();
            if (back != Vector3.zero)
            {   // rays every 2 cm up the back, at 3 points across, from just inside the back face: the nearest drawn surface counts
                var side = Vector3.Cross(Vector3.up, back); float half = Mathf.Abs(Vector3.Dot(b.extents, side)) * 0.8f;
                var face = b.center + back * (Mathf.Abs(Vector3.Dot(b.extents, back)) - 0.01f);
                var gaps = (from u in new[] { -half, 0, half } from v in Enumerable.Range(1, Mathf.Max(3, Mathf.CeilToInt(b.size.y / 0.02f)) - 1).Select(i => i * 0.02f / b.size.y)
                            select Cast(face + side * u + Vector3.up * (b.min.y + b.size.y * v - b.center.y), back, 0.5f) - 0.01f).Where(q => !float.IsNaN(q)).ToList();
                if (gaps.Count == 0) bad.Add($"{name}: no wall behind it within 0.5 m");
                else if (gaps.Min() < -0.005f || gaps.Min() > 0.03f) bad.Add($"{name}: back {gaps.Min() * 100:F1} cm from the drawn wall (want 0-3)");
            }
            float drop = Cast(new Vector3(b.center.x, b.min.y + 0.05f, b.center.z), Vector3.down, 0.5f) - 0.05f;
            if (float.IsNaN(drop) || Mathf.Abs(drop) > 0.01f) bad.Add($"{name}: feet {(float.IsNaN(drop) ? "over no floor" : $"{drop * 100:F1} cm above the floor")}");
            foreach (var c in temp) Object.DestroyImmediate(c); Physics.SyncTransforms();
            int empty = rs.Sum(r => r.sharedMaterials.Count(m => m == null));   // a deleted or missing material draws magenta
            if (empty > 0) bad.Add($"{name}: {empty} empty material slots");
            foreach (var m in rs.SelectMany(r => r.sharedMaterials).Where(m => m != null && !m.name.StartsWith("HiFi_")).Distinct())   // our own generated parts on a piece (the den TV's video screen) are not pack materials
            {
                if (!m.shader.name.StartsWith("HDRP/")) bad.Add($"{name}: material {m.name} on {m.shader.name}");
                else if (m.HasProperty("_BaseColorMap") && m.GetTexture("_BaseColorMap") == null && (!m.HasProperty("_SurfaceType") || m.GetFloat("_SurfaceType") == 0))
                    bad.Add($"{name}: material {m.name} has no base colour map");
            }
        }
        return $"Props check: {PropRecords.Count} store models, {bad.Count} problems" + (bad.Count > 0 ? " (" + string.Join("; ", bad.Take(10)) + ")" : "") + "\n";
    }

    // "+x" / "-x" / "+z" / "-z" in SPEC axes -> the Unity direction the piece's flat back must face (Unity z = -spec z)
    static Vector3 Back(string s) => s switch { "+x" => Vector3.right, "-x" => Vector3.left, "+z" => Vector3.back, "-z" => Vector3.forward, _ => Vector3.zero };

    // the turn (0/90/180/270) that lays the model's long horizontal side along the box's long side and puts its flattest side
    // (most vertices within 2 cm of that extreme: a demilune's straight back, a clock's back board) toward `back`
    static float Orient(GameObject go, bool longAlongX, Vector3 back)
    {
        var mfs = go.GetComponentsInChildren<MeshFilter>().Where(m => m.sharedMesh != null).ToArray();
        float best = 0, bestScore = float.MinValue;
        foreach (float yaw in new[] { 0f, 90f, 180f, 270f })
        {
            go.transform.rotation = Quaternion.Euler(0, yaw, 0);
            var v = mfs.SelectMany(m => m.sharedMesh.vertices.Select(m.transform.TransformPoint)).ToArray();
            float sx = v.Max(q => q.x) - v.Min(q => q.x), sz = v.Max(q => q.z) - v.Min(q => q.z);
            float score = (sx > sz) == longAlongX ? 1e6f : 0f;
            if (back != Vector3.zero)
            {
                float ext = v.Max(q => Vector3.Dot(q, back));
                score += v.Count(q => ext - Vector3.Dot(q, back) < 0.02f);
            }
            if (score > bestScore) { bestScore = score; best = yaw; }
        }
        go.transform.rotation = Quaternion.identity;
        return best;
    }

    // a pack material on a non-HDRP shader (Built-in/URP) becomes an HDRP Lit copy with the same maps
    // one conversion per source material per build: a second one deleted the copy the first renderer already held (magenta, Oct 16)
    static readonly System.Collections.Generic.Dictionary<Material, Material> Converted = new();
    static Material HdrpOrConvert(Material m)
    {
        if (m == null || m.shader.name.StartsWith("HDRP/")) return m;
        if (Converted.TryGetValue(m, out var done)) return done;
        // saved beside the source material, inside the pack's (gitignored) folder
        string src = AssetDatabase.GetAssetPath(m), dst = Path.ChangeExtension(src, null) + "_HDRP.mat";
        AssetDatabase.DeleteAsset(dst);   // rebuilt every build: a stale copy (e.g. saved before its textures were found) must not linger
        var n = new Material(Shader.Find("HDRP/Lit")) { name = m.name + "_HDRP" };
        var envs = new SerializedObject(m).FindProperty("m_SavedProperties.m_TexEnvs");
        Texture T(params string[] ks)
        {
            for (int i = 0; envs != null && i < envs.arraySize; i++)
            {
                var e = envs.GetArrayElementAtIndex(i);
                if (ks.Contains(e.FindPropertyRelative("first").stringValue))
                {
                    var t = e.FindPropertyRelative("second.m_Texture").objectReferenceValue as Texture;
                    if (t != null) return t;
                }
            }
            return null;
        }
        var albedo = T("_BaseMap", "_MainTex"); if (albedo) n.SetTexture("_BaseColorMap", albedo);
        if (m.HasProperty("_BaseColor")) n.SetColor("_BaseColor", m.GetColor("_BaseColor")); else if (m.HasProperty("_Color")) n.SetColor("_BaseColor", m.GetColor("_Color"));
        var nrm = T("_BumpMap", "_NormalMap"); if (nrm) n.SetTexture("_NormalMap", nrm);
        n.SetFloat("_Smoothness", m.HasProperty("_Smoothness") ? m.GetFloat("_Smoothness") : 0.4f);
        // alpha-tested foliage (Built-in Standard "Cutout", or an alpha-clip keyword): keep the cut-out and draw both sides (the tree's needle cards)
        if (m.IsKeywordEnabled("_ALPHATEST_ON") || (m.HasProperty("_Mode") && Mathf.Approximately(m.GetFloat("_Mode"), 1f)) || m.renderQueue == 2450)
        {
            n.SetFloat("_AlphaCutoffEnable", 1f); n.SetFloat("_AlphaCutoff", m.HasProperty("_Cutoff") ? m.GetFloat("_Cutoff") : 0.5f);
            n.SetFloat("_DoubleSidedEnable", 1f); n.SetFloat("_CullMode", 0f);
        }
        UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(n);
        if (src.StartsWith("Assets/")) AssetDatabase.CreateAsset(n, dst);
        Converted[m] = n;
        Debug.Log($"StoreProps: converted {m.name} ({m.shader.name}) to HDRP/Lit");
        return n;
    }
}
