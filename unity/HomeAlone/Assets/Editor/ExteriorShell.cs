using System.Linq;
using UnityEditor;
using UnityEngine;

/// Places the downloaded exterior model (Assets/ThirdParty/HomeAloneExterior) around the survey
/// rooms as a visual shell: rotated to face the same way, scaled to Marina's footprint, aligned on
/// the front-left corner. Meshes that lie entirely inside the survey envelope (furniture, interior
/// walls) are disabled so they don't fight the survey-built interiors.
/// Alignment (2026-09-11): Blender slice of the GLB gives left wing outer x -11.5, main front wall
/// y -2.6, right end x 15.5, kitchen wing rear y 19.5. Survey: X 0..22.7, front outer face Y 0.05.
public static class ExteriorShell
{
    const string PrefabPath = "Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb";
    public const float Scale = 0.83f;
    const float Grow = 0.5f;   // clip envelope = survey rooms grown by this; the model's walls sit up to ~1 m off the survey's
    public const float FloorZ = 0.0f;          // GLB ground-floor level in Blender z (see ZHIST)
    static readonly Vector3 GlbFrontLeft = new Vector3(-11.5f, FloorZ, -2.6f);   // Blender (x, z, y) as Unity (x, y, z) after the 180° turn
    static readonly Vector3 SurveyFrontLeft = new Vector3(-0.1f, 0f, 0.05f);

    [MenuItem("HomeAlone/Place Exterior Shell")]
    public static void PlaceFromMenu() => Place(null);

    public static void Place((float x0, float x1, float z0, float z1)[] surveyRects)
    {
        var house = GameObject.Find("House"); if (house == null) { Debug.LogError("Build the house first."); return; }
        var old = house.transform.Find("Exterior"); if (old != null) Object.DestroyImmediate(old.gameObject);
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(PrefabPath);
        if (prefab == null) { Debug.LogWarning("Exterior GLB not imported yet: " + PrefabPath); return; }
        var root = new GameObject("Exterior"); root.transform.parent = house.transform;
        var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); inst.transform.parent = root.transform;
        // glTFast import lands the model with its front toward +Z; the survey house faces -Z. Turn it, scale, align.
        inst.transform.localRotation = Quaternion.Euler(0, 180f, 0);
        inst.transform.localScale = Vector3.one * Scale;
        inst.transform.localPosition = Vector3.zero;
        // After rotation, Blender (bx, by) maps to Unity (bx, by) in the survey frame; find where the GLB corner landed and shift.
        Vector3 cornerNow = inst.transform.TransformPoint(new Vector3(-GlbFrontLeft.x, GlbFrontLeft.y, -GlbFrontLeft.z));
        inst.transform.localPosition += SurveyFrontLeft - cornerNow;

        // Survey envelope in XZ, slightly shrunk so exterior walls (which straddle the boundary) survive.
        var rects = surveyRects ?? new[] { (0.1f,4.1f,1.0f,8.5f), (4.3f,8.9f,0.4f,9.4f), (9.1f,13.2f,0.2f,11.0f), (13.4f,18.4f,0.4f,6.4f), (18.5f,22.5f,1.1f,8.5f),
                            (13.4f,17.5f,6.8f,12.6f), (17.5f,22.6f,8.7f,16.7f) };
        int kept = 0, dropped = 0, clippedTris = 0;
        System.IO.Directory.CreateDirectory("Assets/ThirdParty/HomeAloneExterior/Clipped");
        foreach (var r in inst.GetComponentsInChildren<MeshRenderer>())
        {
            var b = r.bounds; bool inside = b.max.y < 8.5f && Inside(b.min, rects, -Grow) && Inside(b.max, rects, -Grow) && Inside(new Vector3(b.min.x, 0, b.max.z), rects, -Grow) && Inside(new Vector3(b.max.x, 0, b.min.z), rects, -Grow);
            if (inside) { r.gameObject.SetActive(false); dropped++; continue; }
            kept++;
            var mf = r.GetComponent<MeshFilter>();
            // Colliders only for ground-level site pieces (terrace, steps, lawn, drive) so the player can step outside;
            // interior collision is the survey's job, and the shell's walls are only approximately aligned to it.
            if (mf && mf.sharedMesh) { clippedTris += ClipInterior(mf, rects); if (b.max.y < 1.6f && mf.sharedMesh.triangles.Length > 0 && r.GetComponent<Collider>() == null) r.gameObject.AddComponent<MeshCollider>(); }
            GameObjectUtility.SetStaticEditorFlags(r.gameObject, (StaticEditorFlags)(-1));
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"Exterior shell placed: kept {kept} exterior meshes, disabled {dropped} interior-only meshes, clipped {clippedTris} interior triangles.");
    }

    // The model's merged meshes carry their own interior walls and floors. Remove every triangle whose
    // centroid lies inside the survey rooms (below the roof), keeping facades, roof, terrace and site.
    static int ClipInterior(MeshFilter mf, (float x0, float x1, float z0, float z1)[] rects)
    {
        var src = mf.sharedMesh; var verts = src.vertices; var m = mf.transform.localToWorldMatrix;
        var world = new Vector3[verts.Length]; for (int i = 0; i < verts.Length; i++) world[i] = m.MultiplyPoint3x4(verts[i]);
        int removed = 0; var subs = new System.Collections.Generic.List<int[]>();
        for (int s = 0; s < src.subMeshCount; s++)
        {
            var tri = src.GetTriangles(s); var keep = new System.Collections.Generic.List<int>(tri.Length);
            for (int t = 0; t < tri.Length; t += 3)
            {
                Vector3 a = world[tri[t]], bb = world[tri[t + 1]], cc = world[tri[t + 2]]; var c = (a + bb + cc) / 3f;
                bool low = c.y < 8.5f && c.y > -0.3f;
                // Big site/floor triangles reach into rooms even when their centroid is outside; those reach the collider.
                bool reaches = c.y < 1.8f && (Inside(a, rects, 0f) || Inside(bb, rects, 0f) || Inside(cc, rects, 0f));
                if ((low && Inside(c, rects, -Grow)) || reaches) { removed++; continue; }
                keep.Add(tri[t]); keep.Add(tri[t + 1]); keep.Add(tri[t + 2]);
            }
            subs.Add(keep.ToArray());
        }
        if (removed == 0) return 0;
        var dst = Object.Instantiate(src); dst.name = src.name + "_clipped";
        for (int s = 0; s < subs.Count; s++) dst.SetTriangles(subs[s], s);
        dst.RecalculateBounds();
        AssetDatabase.CreateAsset(dst, $"Assets/ThirdParty/HomeAloneExterior/Clipped/{mf.gameObject.name}.asset");
        mf.sharedMesh = dst;
        return removed;
    }
    static bool Inside(Vector3 p, (float x0, float x1, float z0, float z1)[] rects, float shrink)
    {
        foreach (var (x0, x1, z0, z1) in rects) if (p.x > x0 + shrink && p.x < x1 - shrink && p.z > z0 + shrink && p.z < z1 - shrink) return true;
        return false;
    }
}
