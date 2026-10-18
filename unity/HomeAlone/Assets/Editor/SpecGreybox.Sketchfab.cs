using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

// The user's Sketchfab downloads (CC-BY, CREDITS.md; gitignored under Assets/Purchased/Sketchfab, a clone without them skips each
// piece) placed as props (props lane, overnight 10, Oct 18, not walked): uniform scale to a real size, turned by hand, placed by eye
// from the film. Buzz: the BB gun on two brass hooks over the bed (film 2766, Marina p2 556 s) with its sling, the glove and
// a second bat at the shelves (film 478/480), two trophies on the boards (film 478-502), the corkboard over the desk (film 530; its
// pinned papers are hifi_buzz_props.py's), a Hershey bar in the footlocker. Den: the Astro glass-top table replaces the squashed
// Poly Haven pedestal table (film 2850). Recoloured maps: tools/house/sketchfab_recolour.py.
public static partial class SpecGreybox
{
    const string SF = "Assets/Purchased/Sketchfab/";

    // spec metres in, Unity out: at = (spec x, bottom y in world, spec z) of the bounds' centre; rot = a world turn applied over the import's
    static GameObject Sketchfab(GameObject parent, string glb, string name, Quaternion rot, float longest, Vector3 at, string[] keep = null, string[] drop = null)
    {
        var a = AssetDatabase.LoadAssetAtPath<GameObject>(SF + glb + ".glb");
        if (a == null) { Debug.Log($"Sketchfab: {glb} not present, no {name}"); return null; }
        var go = (GameObject)Object.Instantiate(a, parent.transform); go.name = name;
        foreach (var c in go.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        foreach (var r in go.GetComponentsInChildren<Renderer>().ToList())
            if ((keep != null && !keep.Contains(r.name)) || (drop != null && drop.Contains(r.name))) Object.DestroyImmediate(r.gameObject);
        go.transform.rotation = rot * a.transform.rotation; go.transform.localScale = Vector3.one;
        var b = RendererBounds(go); go.transform.localScale = Vector3.one * (longest / Mathf.Max(b.size.x, b.size.y, b.size.z));
        b = RendererBounds(go); go.transform.position += new Vector3(at.x - b.center.x, at.y - b.min.y, -at.z - b.center.z);
        foreach (var r in go.GetComponentsInChildren<Renderer>())
        {
            r.sharedMaterials = r.sharedMaterials.Select(m => m != null && m.HasProperty("baseColorFactor") && m.GetColor("baseColorFactor").a < 0.5f ? mGlass : HdrpOrConvert(m)).ToArray();
            r.shadowCastingMode = ShadowCastingMode.On; r.gameObject.isStatic = true;
        }
        foreach (var r in go.GetComponentsInChildren<Renderer>()) r.transform.SetParent(go.transform, true);   // one level: the clash check allows a model's own parts
        b = RendererBounds(go); Debug.Log($"Sketchfab {name}: scale {go.transform.localScale.x:F5}, bounds {b.min:F3} .. {b.max:F3}");
        return go;
    }

    // a per-piece copy of each material (whose name starts with `mat`) with a new map and/or colour, saved beside the tints
    static void Restyle(GameObject go, string mat, string map = null, Color? color = null, float metallic = -1, float smooth = -1)
    {
        if (go == null) return;
        foreach (var r in go.GetComponentsInChildren<Renderer>())
            r.sharedMaterials = r.sharedMaterials.Select(m =>
            {
                if (m == null || !m.name.Contains(mat)) return m;   // HdrpOrConvert's copies are named after their file: <glb>_<mat>_HDRP
                var path = $"Assets/Materials/Greybox/SF_{go.name}_{mat.Replace(' ', '_').Replace('.', '_')}.mat";
                var t = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (t == null) { t = new Material(m); AssetDatabase.CreateAsset(t, path); } else t.CopyPropertiesFromMaterial(m);
                if (map != null) { var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(SF + map); if (tex != null) t.SetTexture("_BaseColorMap", tex); else Debug.LogWarning($"Sketchfab: {map} missing (run sketchfab_recolour.py)"); }
                if (color != null) t.SetColor("_BaseColor", color.Value);
                if (metallic >= 0) t.SetFloat("_Metallic", metallic);
                if (smooth >= 0) t.SetFloat("_Smoothness", smooth);
                UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(t); EditorUtility.SetDirty(t); return t;
            }).ToArray();
    }

    static GameObject SfBox(GameObject parent, string name, float x0, float x1, float y0, float y1, float z0, float z1, Material m)
    {   // Unity world box
        var c = GameObject.CreatePrimitive(PrimitiveType.Cube); c.name = name; Object.DestroyImmediate(c.GetComponent<Collider>());
        c.transform.SetParent(parent.transform, true);
        c.transform.position = new Vector3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); c.transform.localScale = new Vector3(x1 - x0, y1 - y0, z1 - z0);
        c.GetComponent<MeshRenderer>().sharedMaterial = m; c.isStatic = true; return c;
    }

    static void SketchfabProps(GameObject root, float gy)
    {
        var g = Child(root, "SketchfabProps");
        var turn = Quaternion.Euler(0, 90, 0);   // the import's long +z to +x

        // --- the BB gun (Henry lever-action, recoloured Daisy-like): door wall over the bed's headboard (Marina p2 556 s: between the
        // posters, stock toward the door; film 2766: stock left, two brass J hooks at 1/3 and 4/5 of the length, the sling hanging below).
        // 0.90 m long (the paper's ruler in changes/2026-10-18-buzz-bed.json), barrel line ~1.67 m, 4.5 cm off the wall (face z 11.57).
        const float WALL = 11.57f;
        var gun = Sketchfab(g, "henry_lever-action_rifle", "buzz_bb_gun", turn, 0.90f, new Vector3(9.45f, 1.513f, WALL + 0.045f), drop: new[] { "Object023tr_pat1_0", "Object037_bullets2_0" });
        if (gun != null)
        {
            var barrel = gun.GetComponentsInChildren<Renderer>().FirstOrDefault(r => r.name == "Object_rifle_0");
            var gb = RendererBounds(gun);
            if (barrel != null && barrel.bounds.center.x < gb.center.x) { gun.transform.RotateAround(gb.center, Vector3.up, 180); Debug.Log("Sketchfab: gun turned, muzzle to +x"); }
            Restyle(gun, "rifle", map: "Recoloured/rifle.png", smooth: 0.45f);
            gb = RendererBounds(gun);
            // the gun's underside at x: rays up through temporary mesh colliders, across its depth (a long tube has vertices only at its ends)
            var cols = gun.GetComponentsInChildren<MeshFilter>().Select(mf => { var mc = mf.gameObject.AddComponent<MeshCollider>(); mc.sharedMesh = mf.sharedMesh; return (Collider)mc; }).ToList();
            Physics.SyncTransforms();
            float Under(float x) => Enumerable.Range(0, 9).Select(k => Mathf.Lerp(gb.min.z, gb.max.z, k / 8f))
                .SelectMany(z => cols.Select(c => c.Raycast(new Ray(new Vector3(x, gb.min.y - 0.05f, z), Vector3.up), out var h, 0.5f) ? h.point.y : float.MaxValue))
                .DefaultIfEmpty(float.MaxValue).Min() is var y && y < float.MaxValue ? y : gb.min.y;
            float front = gb.min.z, back = gb.max.z;   // Unity z: the room side is -z
            var brass = BrassMat();
            foreach (var t in new[] { 0.33f, 0.80f })
            {
                float hx = gb.min.x + t * gb.size.x, y = Under(hx) - 0.002f;
                SfBox(g, "buzz_gun_hook_plate", hx - 0.007f, hx + 0.007f, y - 0.03f, y + 0.03f, -WALL - 0.005f, -WALL, brass);
                SfBox(g, "buzz_gun_hook_arm", hx - 0.006f, hx + 0.006f, y - 0.006f, y, front - 0.008f, -WALL - 0.005f, brass);
                SfBox(g, "buzz_gun_hook_lip", hx - 0.006f, hx + 0.006f, y - 0.006f, y + 0.02f, front - 0.014f, front - 0.008f, brass);
                Debug.Log($"Sketchfab: gun hook at x {hx:F3}, gun underside {y + 0.002f:F3}");
            }
            // the sling: a 28 mm webbing strap from the stock's underside by the butt to the barrel by the front hook, sagging 0.20 m
            float ax = gb.min.x + 0.07f, bx = gb.min.x + 0.80f * gb.size.x - 0.035f;
            Vector3 A = new Vector3(ax, Under(ax) - 0.006f, 0), B = new Vector3(bx, Under(bx) - 0.012f, 0);
            const int N = 32; const float W = 0.014f, SAG = 0.20f; float sz = -WALL - 0.016f;
            var pts = Enumerable.Range(0, N + 1).Select(i => { float s = i / (float)N; var p = Vector3.Lerp(A, B, s); p.y -= SAG * 4 * s * (1 - s); p.z = sz; return p; }).ToArray();
            var verts = new Vector3[2 * (N + 1)]; var tris = new System.Collections.Generic.List<int>();
            for (int i = 0; i <= N; i++)
            {
                var d = (pts[Mathf.Min(i + 1, N)] - pts[Mathf.Max(i - 1, 0)]).normalized; var nrm = new Vector3(-d.y, d.x, 0);
                verts[2 * i] = pts[i] + nrm * W; verts[2 * i + 1] = pts[i] - nrm * W;
                if (i < N) tris.AddRange(new[] { 2 * i, 2 * i + 2, 2 * i + 1, 2 * i + 1, 2 * i + 2, 2 * i + 3 });
            }
            var mesh = new Mesh { name = "buzz_gun_sling", vertices = verts, triangles = tris.ToArray() }; mesh.RecalculateNormals(); mesh.RecalculateBounds();
            var sl = new GameObject("buzz_gun_sling"); sl.transform.SetParent(g.transform, false); sl.isStatic = true;
            sl.AddComponent<MeshFilter>().sharedMesh = mesh;
            var web = Mat("HiFi_SlingWebbing", new Color(0.13f, 0.12f, 0.075f)); web.SetFloat("_DoubleSidedEnable", 1f); web.SetFloat("_CullMode", 0f); web.SetFloat("_Smoothness", 0.15f);
            UnityEditor.Rendering.HighDefinition.HDShaderUtils.ResetMaterialKeywords(web);
            var mr = sl.AddComponent<MeshRenderer>(); mr.sharedMaterial = web; mr.shadowCastingMode = ShadowCastingMode.TwoSided;
            AssetDatabase.CreateAsset(mesh, "Assets/Materials/Greybox/buzz_gun_sling.asset");
            foreach (var c in cols) Object.DestroyImmediate(c);
            Debug.Log($"Sketchfab: gun {gb.min:F3} .. {gb.max:F3}, sling {A:F3} -> {B:F3}");
        }

        // --- the shelves (boards x 7.488-7.773; board tops 0.657 / 1.004 / 1.41): film 478 board 1 holds the brown glove (by the
        // baseball), trophies on boards 0 and 2 (film 478: a gold figure on board 0 by the tank; 496-502: trophies)
        var glove = Sketchfab(g, "baseball_glove-2", "buzz_glove", turn, 0.27f, new Vector3(7.64f, 1.004f, 13.84f));
        Restyle(glove, "default", map: "Recoloured/glove.png", smooth: 0.3f);
        // (the set's helmet is left out: a blocky low-poly shape that reads as a black box, build 2)
        Restyle(Sketchfab(g, "golden_trophy", "buzz_trophy_a", turn, 0.25f, new Vector3(7.63f, 0.657f, 14.45f)), "Material", metallic: 0.8f, smooth: 0.6f);
        Restyle(Sketchfab(g, "golden_trophy", "buzz_trophy_b", turn, 0.22f, new Vector3(7.63f, 1.41f, 14.66f)), "Material", metallic: 0.8f, smooth: 0.6f);
        // a second bat (the set's), barrel down, leaning on the shelves wall (face x 7.473) past the Fadnn bat (film 478: bats there)
        var bat = Sketchfab(g, "baseball_bat_and_helmet", "buzz_bat_2", Quaternion.Euler(0, 0, 16f) * Quaternion.Euler(180, 0, 0), 0.70f, new Vector3(7.62f, 0f, 15.70f), keep: new[] { "Circle_Material.001_0", "Circle_Material.002_0" });
        if (bat != null)
        {
            var bb = RendererBounds(bat); bat.transform.position += new Vector3(7.476f - bb.min.x, 0, 0);
            Restyle(bat, "Material.001", color: new Color(0.62f, 0.45f, 0.27f), smooth: 0.45f);
        }

        // --- the framed corkboard over the desk (film 530: right of the window, over the typewriter), 0.90 m wide, back on the desk wall
        // (face z 15.998, 1 mm off); the import's identity turn stands it facing z
        var cork = Sketchfab(g, "framed_corkboard__crafted_by_jerovdl", "buzz_corkboard", Quaternion.Inverse(AssetDatabase.LoadAssetAtPath<GameObject>(SF + "framed_corkboard__crafted_by_jerovdl.glb")?.transform.rotation ?? Quaternion.identity),
                             0.90f, new Vector3(9.40f, 1.15f, 15.997f - 0.0079f));
        // --- a Hershey bar on the Playboy in the footlocker (cover top y 0.022; hifi_buzz_props.py)
        Sketchfab(g, "hersheys_chocolate_bar_unwrapped", "buzz_hershey", Quaternion.Inverse(AssetDatabase.LoadAssetAtPath<GameObject>(SF + "hersheys_chocolate_bar_unwrapped.glb")?.transform.rotation ?? Quaternion.identity),
                  0.15f, new Vector3(9.75f, 0.0225f, 14.0975f));   // x: the Playboy's centre after the trunk's -0.14 m (hifi_buzz_props.py DX)

        // --- den: the Astro table (glass top in a wood ring, four curved legs; film 2850) at the old table's spot (den.json coffee_table,
        // Marina f9), 0.80 m across, 0.425 m high; the Poly Haven pedestal table in DenProps.glb is hidden (its walk collider stays)
        var den = GameObject.Find("DenProps_HiFi");
        int hid = 0;
        if (den != null) foreach (var r in den.GetComponentsInChildren<MeshRenderer>().Where(r => r.name.StartsWith("coffee_table"))) { r.enabled = false; hid++; }
        if (Sketchfab(g, "coffee_table_astro", "den_astro_table", Quaternion.identity, 0.80f, new Vector3(5.98f, gy, 17.83f)) == null)
            foreach (var r in den != null ? den.GetComponentsInChildren<MeshRenderer>(true).Where(r => r.name.StartsWith("coffee_table")) : Enumerable.Empty<MeshRenderer>()) r.enabled = true;
        Debug.Log($"Sketchfab: den pedestal table hidden ({hid} renderers)");

        // --- parents' bedroom (user Oct 18: "the mannequin and other hero items"; Marina p2 184-188, 238): the treadle sewing table under
        // the side window (wall z 0), machine head up, 1.05 m tall; the 1900s dress form in front of the window corner, 1.45 m
        Sketchfab(g, "sewing_machine", "parents_sewing_table", turn, 1.05f, new Vector3(5.75f, 0f, 0.33f));
        Sketchfab(g, "mannequin_1900s_m_size", "parents_dress_form", Quaternion.Euler(0, -90, 0), 1.45f, new Vector3(7.95f, 0f, 1.0f));
        // --- basement (Oct 18 dressing round, film 2394: a shirted mannequin in the clutter by the stair's foot): the same dress form, 1.55 m,
        // on the slab past the flight's foot, off the walk to the areaway door (spec/dressing/basement.json; slab at ground -2.681)
        Sketchfab(g, "mannequin_1900s_m_size", "basement_mannequin", Quaternion.Euler(0, 180, 0), 1.55f, new Vector3(3.3f, gy - 2.681f, 8.5f));

        // --- kitchen: Kevin's blowtorch trap at the back door (film 10351-10363: a brass plumber's torch clamped beside the door at head
        // height by the upper cabinet, its nozzle across the doorway; a string to the door fires it into Harry's hat). CGTrader "Rusty Blow
        // Torch" (free, user download Oct 18; GLB at 2K by the coordinator, gitignored). 0.33 m long, in front of the cabinet's door-side end
        // (kitchen.json uppers[0] x -5.192..-4.862, z 1.219..1.874; door z 2.046..3.004 on the x -5.262 wall), bottom 1.70 m up.
        // The import's nozzle is its +x end: the turn sends it to +spec z, across the doorway. Centre z 1.79 (was 1.90, which hung the
        // tank past the cabinet's end in the air; film 10354/10357 hang it in front of the door-side end, the nozzle just past it)
        Sketchfab(g, "rusty_blowtorch", "kitchen_blowtorch", Quaternion.Euler(0, 90, 0), 0.33f, new Vector3(-4.80f, gy + 1.70f, 1.79f));
    }
}
