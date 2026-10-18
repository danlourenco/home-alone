using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using UnityEditor;
using Object = UnityEngine.Object;

// The house's exterior skin (Oct 18 2026, TRIAL; changes/2026-10-18-exterior-shell.json, DEVIATIONS 97): tools/house/exterior_shell.py
// (the film's house on our measured ground footprint) -> hifi_exterior.py -> Exterior.glb, world coordinates. Its parts are named by
// draw set: L_* always drawn (ground-storey veneer, low roofs, porch, door face), U_* the upper storey and roofs, hidden while the
// player is upstairs (HouseSplit). The U parts stand in for the film's flush upper storey in the sun's shadows exactly like
// FilmFront (LayerFilmFront: cast while the player is downstairs, out of the bake); the L parts are the house (LayerHouse).
// Upstairs and attic pieces that reach outside the skin (Marina's overhang strip, the attic's knee walls and roof) are drawn only upstairs.
public static partial class SpecGreybox
{
    static readonly List<Renderer> ShellGlow = new List<Renderer>();   // the upper sashes' drawn shades: lit at night (HouseNightMode)
    static readonly List<Light> ShellLights = new List<Light>();       // porch lantern, lamp posts: moved into the night layer (Daylight)
    static Material XmasBulb()   // film 10: warm white mini-lights (double-sided: the generated cubes' winding is not checked)
    {
        var m = AtticGlow("HiFi_XmasBulb", new Color(1f, 0.78f, 0.50f), 2500f, 0.4f); m.SetFloat("_DoubleSidedEnable", 1f); HDMaterial.ValidateMaterial(m); return m;
    }

    static void Shell(GameObject ext, float gy)
    {
        // (ShellGlow / ShellLights are cleared in ExteriorPlants, which runs first: clearing here dropped the yard's lights from the
        // night switch, so they glowed by day; build 4)
        var S = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/exterior_shell.json"))));
        var holder = new GameObject("HouseShell"); holder.transform.SetParent(ext.transform, false);
        holder.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        var shade = AtticGlow("HiFi_ShadeExterior", new Color(0.88f, 0.83f, 0.70f), 25f, 0.15f);
        // the sealed sunroom's windows (sunroom fix, Oct 18): sheers seen through glass, greyer and glossier than the shades (sun-lit they
        // read flat against the white sashes), lit at night (film 10)
        var sheer = AtticGlow("HiFi_SheerExterior", new Color(0.70f, 0.69f, 0.66f), 25f, 0.75f);
        var glass = Mat("HiFi_ExtGlass", new Color(0.035f, 0.045f, 0.055f)); glass.SetFloat("_Smoothness", 0.93f);
        var g = PlaceHiFi(holder, 0f, "Exterior", new Dictionary<string, Material> {
            ["EX_Brick"] = TexMat("HiFi_ExtBrick", "red_brick_03", new Color(0.80f, 0.60f, 0.53f), 1.90f, 0.12f),   // 28 courses a tile: 68 mm (2 5/8 in) courses
            ["EX_Trim"] = Mat("HiFi_ExtTrim", new Color(0.86f, 0.85f, 0.81f)),
            ["EX_Shutter"] = Mat("HiFi_ExtShutter", new Color(0.022f, 0.026f, 0.026f)),
            ["EX_Roof"] = TexMat("HiFi_ExtRoof", "concrete_floor_worn_001", new Color(0.14f, 0.12f, 0.11f), 1.6f, 0.08f),   // polish: lifted from 0.10/0.095/0.095 (read near-black in sun; film 4382 dark brown-grey)
            ["EX_Snow"] = Mat("HiFi_ExtRoofSnow", new Color(0.80f, 0.82f, 0.86f)),
            ["EX_Glass"] = glass, ["EX_Shade"] = shade, ["EX_Sheer"] = sheer,
            ["EX_Stone"] = Mat("HiFi_ExtStone", new Color(0.74f, 0.70f, 0.62f)),
            ["EX_Gutter"] = Mat("HiFi_ExtGutter", new Color(0.84f, 0.84f, 0.82f)),
            ["EX_Pot"] = Mat("HiFi_ExtPot", new Color(0.50f, 0.25f, 0.16f)),
            ["EX_DoorBlack"] = Mat("HiFi_ExtDoor", new Color(0.02f, 0.025f, 0.025f)),
            ["EX_Brass"] = BrassMat(),
            ["EX_Wreath"] = Mat("HiFi_ExtWreath", new Color(0.06f, 0.16f, 0.06f)),
            ["EX_Bow"] = Mat("HiFi_ExtBow", new Color(0.55f, 0.04f, 0.04f)),
            ["EX_PorchGlass"] = mGlass,
            ["EX_Bulb"] = XmasBulb(),
            ["EX_LampGlow"] = AtticGlow("HiFi_ExtLanternGlow", new Color(1f, 0.85f, 0.62f), 1500f, 0.6f) });
        if (g == null) { Debug.LogWarning("Shell: Exterior.glb missing, no skin"); return; }
        var upper = new List<Renderer>();
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            bool u = r.name.StartsWith("U_");
            r.gameObject.isStatic = true;
            r.renderingLayerMask = u ? LayerFilmFront : LayerHouse;
            bool lit = r.sharedMaterial.name.StartsWith("HiFi_XmasBulb") || r.sharedMaterial.name.StartsWith("HiFi_ExtLanternGlow");
            r.shadowCastingMode = r.sharedMaterial == shade || r.sharedMaterial == sheer || r.sharedMaterial == mGlass || lit ? ShadowCastingMode.Off : ShadowCastingMode.TwoSided;
            if (u) upper.Add(r);
            if (r.sharedMaterial == shade || r.sharedMaterial == sheer || lit) ShellGlow.Add(r);   // Christmas lights and the porch lantern: dark by day
        }
        var pl = S["porch_lantern"];   // film 10/714: the portico's lantern lit at night (no shadows: perf; a short range)
        if (pl != null) ShellLights.Add(NightLight(holder, "PorchLantern", new Vector3((float)pl["x"], (float)pl["y"], -(float)pl["z"]), 60f, 4.5f));
        // the inside-only set: upstairs/attic renderers (under Upstairs, above the ground storey) with any of 125 bounds points outside every
        // skin solid (the walls' plan rectangle under its roof), more than 5 cm
        var solids = S["roofs"].Where(q => (string)q["kind"] != "box" && q["walls"].Count() == 4).ToList();
        bool InSkin(Vector3 w)
        {
            float x = w.x, z = -w.z, y = w.y;
            foreach (var q in solids)
            {
                float w0 = (float)q["walls"][0] - 0.05f, w1 = (float)q["walls"][1] + 0.05f, w2 = (float)q["walls"][2] - 0.05f, w3 = (float)q["walls"][3] + 0.05f;
                if (x < w0 || x > w1 || z < w2 || z > w3) continue;
                float e = (float)q["eave"], t = (float)q["tan"], top;
                if ((string)q["kind"] == "lean") top = e + t * (x - (float)q["x"][0]);
                else top = e + t * Mathf.Min(Mathf.Min(x - (float)q["x"][0], (float)q["x"][1] - x), Mathf.Min(z - (float)q["z"][0], (float)q["z"][1] - z));
                if (y < top + 0.10f) return true;
            }
            return false;
        }
        var up = GameObject.Find("Upstairs"); var inside = new List<Renderer>();
        foreach (var r in up.GetComponentsInChildren<MeshRenderer>(true))
        {
            if (r.shadowCastingMode == ShadowCastingMode.ShadowsOnly || r.transform.IsChildOf(ext.transform)) continue;
            var b = r.bounds; if (b.min.y < gy + 2.75f) continue;
            if (b.center.x < -2f || b.center.x > 13f || -b.center.z < -2.5f || -b.center.z > 21.5f) continue;   // the treehouse and the yard are not the house
            string path = r.transform.parent != null ? r.transform.parent.name + "/" + r.name : r.name;
            if (path.Contains("Treehouse") || path.Contains("ZipLine")) continue;
            bool outside = false;
            for (int i = 0; i < 125 && !outside; i++)
            {
                var q = new Vector3(Mathf.Lerp(b.min.x + 0.02f, b.max.x - 0.02f, (i % 5) / 4f), Mathf.Lerp(b.min.y + 0.02f, b.max.y - 0.02f, (i / 5 % 5) / 4f),
                                    Mathf.Lerp(b.min.z + 0.02f, b.max.z - 0.02f, (i / 25) / 4f));
                outside = !InSkin(q);
            }
            if (outside) inside.Add(r);
        }
        // upstairs room outlines (world) for the camera test, and the attic's
        var geo = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/geometry.json"))));
        var hs = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/house_spec.json"))));
        var pts = new List<Vector2>(); var starts = new List<int>();
        foreach (var rm in geo["upstairs"]["rooms"]) { starts.Add(pts.Count); pts.AddRange(rm["poly"].Select(p => new Vector2((float)p[0], -(float)p[1]))); }
        var A = hs["attic_stair"]["attic"];
        starts.Add(pts.Count);
        float ax0 = (float)A["x"][0], ax1 = (float)A["x"][1], az0 = (float)A["z"][0], az1 = (float)A["z"][1];
        pts.AddRange(new[] { new Vector2(ax0, -az0), new Vector2(ax1, -az0), new Vector2(ax1, -az1), new Vector2(ax0, -az1) });
        var split = new GameObject("HouseSplit").AddComponent<HouseSplit>(); split.transform.SetParent(holder.transform, false);
        split.skinUpper = upper.ToArray(); split.insideOnly = inside.ToArray(); split.rooms = pts.ToArray(); split.roomStarts = starts.ToArray();
        split.switchY = gy + 2.326f + 0.9f;   // StoreyShadows' switch: the eye 0.9 m over the main stair's landing
        Debug.Log($"Shell: {g.GetComponentsInChildren<MeshRenderer>().Length} skin parts ({upper.Count} upper), {ShellGlow.Count} shades; " +
                  $"{inside.Count} upstairs/attic renderers drawn only upstairs: {string.Join(", ", inside.Take(40).Select(r => r.name))}{(inside.Count > 40 ? " ..." : "")}");
    }

    // The front (film 4382, 6399): the stoop under the portico, seven red steps down through two terraced brick beds with stone caps,
    // and the walk to the street. Spec x, z; world y (front yard -4.32, the registered GLB's).
    static void FrontBeds(GameObject yard, float d, Material snow, Material walk)
    {
        var brick = TexMat("HiFi_ExtBrick", "red_brick_03", new Color(0.80f, 0.60f, 0.53f), 1.90f, 0.12f);
        var cap = Mat("HiFi_ExtStone", new Color(0.74f, 0.70f, 0.62f));
        var red = Mat("Yard_Steps", new Color(0.50f, 0.22f, 0.18f));
        const float face = 10.37f, zc = 9.716f, sw = 0.95f, cheek = 0.25f;
        const float stoopX = 12.25f, upX = 12.85f, loX = 14.85f, riser = 0.1757f, tread = 0.30f;
        float yS = -3.09f + d, yU = -3.45f + d, yUw = -3.32f + d, yL = -3.90f + d, yLw = -3.80f + d, yB = -4.35f + d, yW = -4.30f + d;
        void B(string n, float x0, float x1, float z0, float z1, float y0, float y1, Material m) => Box(yard, n, x0, x1, -z1, -z0, y0, y1, m);
        B("Stoop_Front", face, stoopX, 8.0f, 11.43f, yB, yS, red);
        for (int k = 1; k <= 6; k++)
            B($"Step_Front{k}", stoopX + tread * (k - 1), stoopX + tread * k, zc - sw, zc + sw, yB, yS - riser * k, red);
        B("Walk_Front", stoopX + tread * 6, 24.40f, zc - 0.75f, zc + 0.75f, yB, yW, walk);
        // beds either side of the stoop and steps, from each section's brick face: den 9.506 (z 16.21-20.157), main 10.37, right 9.647
        // (right: from 10.40, past the basement's front wall, which stands 0.8 m proud of the sunroom's: the build's room cull took the bed)
        var spans = new[] { (-1.155f, 2.864f, 10.40f), (2.864f, 8.0f, face), (11.43f, 16.21f, face), (16.21f, 20.157f, 9.506f) };
        foreach (var (z0, z1, x0) in spans)
        {
            B("Bed_Upper", x0, upX - 0.20f, z0, z1, yB, yU, snow);
            B("Bed_Lower", upX, loX - 0.20f, z0, z1, yB, yL, snow);
        }
        B("Bed_Upper", stoopX, upX - 0.20f, 8.0f, zc - sw - cheek, yB, yU, snow); B("Bed_Upper", stoopX, upX - 0.20f, zc + sw + cheek, 11.43f, yB, yU, snow);
        B("Bed_Lower", upX, loX - 0.20f, 8.0f, zc - sw - cheek, yB, yL, snow);   B("Bed_Lower", upX, loX - 0.20f, zc + sw + cheek, 11.43f, yB, yL, snow);
        foreach (var (z0, z1) in new[] { (-1.155f, zc - sw - cheek), (zc + sw + cheek, 20.157f) })
        {   // the retaining walls (brick, stone cap) along x = upX and loX
            B("BedWall_Upper", upX - 0.20f, upX, z0, z1, yB, yUw - 0.05f, brick); B("BedCap_Upper", upX - 0.23f, upX + 0.03f, z0, z1, yUw - 0.05f, yUw, cap);
            B("BedWall_Lower", loX - 0.20f, loX, z0, z1, yB, yLw - 0.05f, brick); B("BedCap_Lower", loX - 0.23f, loX + 0.03f, z0, z1, yLw - 0.05f, yLw, cap);
        }
        foreach (var (z0, z1) in new[] { (zc - sw - cheek, zc - sw), (zc + sw, zc + sw + cheek) })
        {   // cheek walls beside the steps, stepping down with the beds
            B("BedCheek_Upper", stoopX, upX, z0, z1, yB, yUw, brick);
            B("BedCheek_Lower", upX, loX, z0, z1, yB, yLw, brick);
        }
        // the beds' ends at the den and right section corners (side returns)
        B("BedWall_End", 9.506f, loX, 20.157f, 20.357f, yB, yUw - 0.05f, brick);
        B("BedWall_End", 9.647f, loX, -1.355f, -1.155f, yB, yUw - 0.05f, brick);
    }

    // a warm unshadowed point light for the night layer (moved there by Daylight)
    static Light NightLight(GameObject parent, string n, Vector3 world, float lumens, float range)
    {
        var l = new GameObject(n).AddComponent<Light>(); l.transform.SetParent(parent.transform, true); l.transform.position = world;
        l.type = LightType.Point; l.gameObject.AddComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalLightData>();
        l.intensity = lumens; l.lightUnit = UnityEngine.Rendering.LightUnit.Lumen; l.range = range; l.color = new Color(1f, 0.80f, 0.55f);
        l.shadows = LightShadows.None; l.lightmapBakeType = LightmapBakeType.Realtime; return l;
    }

    // one mesh of small cubes (Christmas mini-lights) at the given world points
    static GameObject Bulbs(GameObject parent, string n, List<Vector3> pts, float size, Material m)
    {
        var vs = new List<Vector3>(); var tris = new List<int>(); float h = size / 2;
        int[] F = { 0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4, 1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7 };
        foreach (var p in pts)
        {
            int b = vs.Count;
            foreach (var y in new[] { -h, h }) { vs.Add(p + new Vector3(-h, y, -h)); vs.Add(p + new Vector3(h, y, -h)); vs.Add(p + new Vector3(h, y, h)); vs.Add(p + new Vector3(-h, y, h)); }
            foreach (var i in F) tris.Add(b + i);
        }
        var mesh = new Mesh { name = n, indexFormat = IndexFormat.UInt32 }; mesh.SetVertices(vs); mesh.SetTriangles(tris, 0); mesh.RecalculateNormals(); mesh.RecalculateBounds();
        // the mesh is saved inside the scene (as PropertyPart's): an asset made in the scratch copy is missing from the project after a load
        var g = new GameObject(n); g.transform.SetParent(parent.transform, false); g.isStatic = true;
        g.AddComponent<MeshFilter>().sharedMesh = mesh; var r = g.AddComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
        ShellGlow.Add(r); return g;
    }

    // The front beds' plants (exterior polish, Oct 18, TRIAL; decoration): tools/house/hifi_ext_plants.py -> ExteriorPlants.glb, one
    // root per plant at its spec (x, 0, z), dropped onto the bed by a ray; mini-lights strung over each shrub and along the bed caps
    // (film 10, 1470: the shrubs and terraces lit at night), and lamp posts at the street (film 10 left, 1470 right).
    static void ExteriorPlants(GameObject yard, float d)
    {
        ShellGlow.Clear(); ShellLights.Clear();   // the exterior's night set starts here (Shell adds to it after)
        var a = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Models/Foyer/ExteriorPlants.glb");
        if (a == null) { Debug.LogWarning("ExteriorPlants: missing ExteriorPlants.glb"); return; }
        // a holder at the WORLD origin: the yard's parent (the registered site) is offset, and every position below is world
        var holder = new GameObject("ExteriorPolish"); holder.transform.SetParent(yard.transform, true);
        holder.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        var g = (GameObject)Object.Instantiate(a, holder.transform); g.name = "ExteriorPlants_HiFi"; g.transform.localPosition = Vector3.zero; g.transform.localRotation = Quaternion.identity;
        foreach (var c in g.GetComponentsInChildren<Collider>()) Object.DestroyImmediate(c);
        Material DS(Material m) { m.SetFloat("_DoubleSidedEnable", 1f); HDMaterial.ValidateMaterial(m); return m; }
        var remap = new Dictionary<string, Material> {
            ["EP_Core"] = Mat("HiFi_ExtShrubCore", new Color(0.012f, 0.025f, 0.010f)),
            ["EP_LeafB"] = DS(Mat("HiFi_ExtShrubLeafB", new Color(0.050f, 0.095f, 0.030f))),
            ["EP_Leaf"] = DS(Mat("HiFi_ExtShrubLeaf", new Color(0.030f, 0.070f, 0.025f))),
            ["EP_Snow"] = DS(Mat("HiFi_ExtShrubSnow", new Color(0.85f, 0.87f, 0.90f))),
            ["EP_Stem"] = Mat("HiFi_ExtShrubStem", new Color(0.12f, 0.08f, 0.05f)),
            ["EP_Stone"] = Mat("HiFi_ExtUrn", new Color(0.80f, 0.78f, 0.74f)) };
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            r.sharedMaterials = r.sharedMaterials.Select(m => m == null ? m : remap.Where(kv => m.name.StartsWith(kv.Key)).Select(kv => kv.Value).FirstOrDefault() ?? m).ToArray();
            r.gameObject.isStatic = true; r.shadowCastingMode = ShadowCastingMode.On;
        }
        Physics.SyncTransforms();
        var pts = new List<Vector3>(); var rnd = new System.Random(10); int dropped = 0;
        foreach (Transform p in g.transform.Cast<Transform>().ToList())
        {
            var o = p.position;
            if (Physics.Raycast(new Vector3(o.x, -2.6f + d, o.z), Vector3.down, out var hit, 3f)) { p.position = new Vector3(o.x, hit.point.y - 0.02f, o.z); dropped++; }
            else Debug.LogWarning($"ExteriorPlants: no bed under {p.name} at {o}");
            if (p.name.Contains("urn") || p.name.Contains("fir")) continue;
            foreach (var r in p.GetComponentsInChildren<MeshRenderer>())
            {   // mini-lights on the shrub's ellipsoid, upper 80%, ~32 a square metre
                if (r.name.Contains("stem")) continue;
                var b = r.bounds; var c = b.center; var e = b.extents + Vector3.one * 0.035f;   // at the leaf cards' tips
                int n = Mathf.RoundToInt(4f * Mathf.PI * Mathf.Pow((e.x * e.y + e.x * e.z + e.y * e.z) / 3f, 1f) * 32f);
                for (int k = 0; k < n; k++)
                {
                    var v = new Vector3((float)(rnd.NextDouble() * 2 - 1), (float)(rnd.NextDouble() * 2 - 1), (float)(rnd.NextDouble() * 2 - 1));
                    if (v.sqrMagnitude < 1e-4f || v.sqrMagnitude > 1f) { k--; continue; }
                    v.Normalize(); if (v.y < -0.55f) continue;
                    pts.Add(c + Vector3.Scale(v, e));
                }
            }
        }
        // the terraces' caps (FrontBeds: upper cap x 12.62-12.88 at -3.32, lower 14.62-14.88 at -3.80): a strand along each front edge
        const float zc = 9.716f, sw = 0.95f, cheek = 0.25f;
        foreach (var (x, y) in new[] { (12.90f, -3.32f + d + 0.02f), (14.90f, -3.80f + d + 0.02f) })
            foreach (var (z0, z1) in new[] { (-1.155f, zc - sw - cheek), (zc + sw + cheek, 20.157f) })
                for (float z = z0 + 0.05f; z < z1; z += 0.12f) pts.Add(new Vector3(x, y, -z));
        var bulbs = Bulbs(holder, "XmasBulbs_Yard", pts, 0.02f, XmasBulb());
        // lamp posts at the street (film 1470: black post, globe lantern; film 10 one at the left)
        var post = Mat("HiFi_ExtLampPost", new Color(0.02f, 0.025f, 0.025f)); var globe = AtticGlow("HiFi_ExtLampGlobe", new Color(1f, 0.88f, 0.70f), 1200f, 0.6f);
        var posts = new GameObject("LampPosts"); posts.transform.SetParent(holder.transform, false);
        foreach (var (x, z) in new[] { (25.2f, 21.5f), (25.2f, -6.0f) })
        {
            float y0 = -4.35f + d;
            if (Physics.Raycast(new Vector3(x, 0f, -z), Vector3.down, out var hit, 8f)) y0 = hit.point.y;
            void Prim(PrimitiveType t, string n, Vector3 pos, Vector3 sc, Material m)
            {
                var q = GameObject.CreatePrimitive(t); q.name = n; Object.DestroyImmediate(q.GetComponent<Collider>()); q.transform.SetParent(posts.transform, false);
                q.transform.position = pos; q.transform.localScale = sc; q.GetComponent<MeshRenderer>().sharedMaterial = m; q.isStatic = true;
                if (m == globe) { q.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off; ShellGlow.Add(q.GetComponent<MeshRenderer>()); }
            }
            Prim(PrimitiveType.Cylinder, "Base", new Vector3(x, y0 + 0.25f, -z), new Vector3(0.24f, 0.25f, 0.24f), post);
            Prim(PrimitiveType.Cylinder, "Post", new Vector3(x, y0 + 1.6f, -z), new Vector3(0.11f, 1.6f, 0.11f), post);
            Prim(PrimitiveType.Cylinder, "Collar", new Vector3(x, y0 + 3.22f, -z), new Vector3(0.22f, 0.04f, 0.22f), post);
            Prim(PrimitiveType.Sphere, "Globe", new Vector3(x, y0 + 3.48f, -z), new Vector3(0.36f, 0.44f, 0.36f), globe);
            Prim(PrimitiveType.Cylinder, "Finial", new Vector3(x, y0 + 3.74f, -z), new Vector3(0.06f, 0.05f, 0.06f), post);
            ShellLights.Add(NightLight(posts, "LampPostLight", new Vector3(x, y0 + 3.48f, -z), 1200f, 12f));
        }
        Debug.Log($"ExteriorPlants: {g.transform.childCount} plants ({dropped} on a bed), {pts.Count} mini-lights, {ShellLights.Count} night lights");
    }

    // every exterior mini-light / lantern glow must switch with N (build 4 shipped the yard's glowing by day): logged per build
    static void NightSetCheck(HouseNightMode mode)
    {
        var set = new HashSet<Renderer>(mode.glowRenderers);
        int miss = Object.FindObjectsByType<MeshRenderer>(FindObjectsInactive.Include, FindObjectsSortMode.None)
            .Count(r => r.sharedMaterial != null && (r.sharedMaterial.name.StartsWith("HiFi_Xmas") || r.sharedMaterial.name.StartsWith("HiFi_ExtLampGlobe")) && !set.Contains(r));
        int day = ShellLights.Count(l => l != null && !l.transform.IsChildOf(mode.nightLayer.transform));
        Debug.Log(miss == 0 && day == 0 ? $"Night set check: exterior glows and {ShellLights.Count} lights switch with N" : $"Night set check FAIL: {miss} glow renderers not switched, {day} exterior lights outside the night layer");
    }
}
