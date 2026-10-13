using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

/// Fidelity pass for the foyer and the kitchen/breakfast zone: real stair, trim, casings, beams,
/// cabinetry, island, and textured HDRP materials (Astra's damask/floral, Poly Haven oak/terracotta,
/// generated blue tile). Everything is placed from the survey numbers; nothing is hand-dragged.
public static partial class SurveyBuilder
{
    static Material mDamask, mFloral, mOak, mTerracotta, mBlueTile, mCherry, mTrim, mRunner, mBeam, mSteel, mBlack, mCream, mGlass, mCopper, mSheer;

    // ---------- materials ----------
    static void DetailMaterials()
    {
        Directory.CreateDirectory("Assets/Materials");
        mDamask = TexMat("FoyerDamask", "Assets/Textures/foyer_wallpaper.png", null, 1.25f, 0.25f);
        mFloral = TexMat("KitchenFloral", "Assets/Textures/kitchen_floral.png", null, 1.05f, 0.2f);
        mOak = TexMat("OakFloor", "Assets/Textures/wood_floor_diff.jpg", "Assets/Textures/wood_floor_normal.jpg", 2.4f, 0.45f);
        mTerracotta = File.Exists("Assets/Textures/terracotta_Diffuse.jpg")
            ? TexMat("Terracotta", "Assets/Textures/terracotta_Diffuse.jpg", "Assets/Textures/terracotta_nor_gl.jpg", 2.08f, 0.35f)
            : Mat("Terracotta", new Color(0.45f, 0.22f, 0.15f));
        mBlueTile = TexMat("BlueTile", GenerateTilePng("Assets/Textures/blue_tile_gen.png", new Color(0.13f, 0.22f, 0.42f), new Color(0.72f, 0.74f, 0.78f), 4, 0.06f), null, 0.42f, 0.85f);
        mCherry = Mat("DarkCherry", new Color(0.24f, 0.10f, 0.07f)); mCherry.SetFloat("_Smoothness", 0.55f);
        mTrim = Mat("WhiteTrim", new Color(0.94f, 0.93f, 0.90f)); mTrim.SetFloat("_Smoothness", 0.5f);
        mRunner = Mat("CranberryRunner", new Color(0.45f, 0.06f, 0.09f)); mRunner.SetFloat("_Smoothness", 0.1f);
        mBeam = Mat("DarkBeam", new Color(0.20f, 0.11f, 0.07f)); mBeam.SetFloat("_Smoothness", 0.3f);
        mSteel = Mat("Steel", new Color(0.75f, 0.76f, 0.78f)); mSteel.SetFloat("_Smoothness", 0.85f); mSteel.SetFloat("_Metallic", 1f);
        mBlack = Mat("BlackAppliance", new Color(0.05f, 0.05f, 0.05f)); mBlack.SetFloat("_Smoothness", 0.6f);
        mCream = Mat("CreamPaint", new Color(0.93f, 0.90f, 0.82f)); mCream.SetFloat("_Smoothness", 0.4f);
        mCopper = Mat("Copper", new Color(0.72f, 0.42f, 0.28f)); mCopper.SetFloat("_Smoothness", 0.7f); mCopper.SetFloat("_Metallic", 1f);
        mSheer = Mat("SheerCurtain", new Color(0.96f, 0.95f, 0.90f, 0.82f)); mSheer.SetFloat("_SurfaceType", 1); mSheer.SetFloat("_BlendMode", 0); mSheer.SetFloat("_Smoothness", 0.1f); mSheer.renderQueue = 3000; HDMaterial.ValidateMaterial(mSheer);
        mGlass = Mat("Glass", new Color(0.8f, 0.9f, 1f, 0.25f));
        mGlass.SetFloat("_SurfaceType", 1); mGlass.SetFloat("_BlendMode", 0); mGlass.SetFloat("_Smoothness", 0.95f);
        mGlass.renderQueue = 3000; HDMaterial.ValidateMaterial(mGlass);
    }

    // World-space triplanar HDRP/Lit so box scaling never stretches the texture. tile = metres per repeat.
    static Material TexMat(string n, string albedo, string normal, float tile, float smooth)
    {
        string path = $"Assets/Materials/{n}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) { m = new Material(Shader.Find("HDRP/Lit")); AssetDatabase.CreateAsset(m, path); }
        var a = AssetDatabase.LoadAssetAtPath<Texture2D>(albedo);
        m.SetColor("_BaseColor", Color.white); m.SetTexture("_BaseColorMap", a); m.SetFloat("_Smoothness", smooth);
        m.SetFloat("_UVBase", 5f); m.EnableKeyword("_MAPPING_TRIPLANAR"); m.SetFloat("_TexWorldScale", 1f / tile);
        if (normal != null && File.Exists(normal))
        {
            var imp = AssetImporter.GetAtPath(normal) as TextureImporter;
            if (imp != null && imp.textureType != TextureImporterType.NormalMap) { imp.textureType = TextureImporterType.NormalMap; imp.SaveAndReimport(); }
            m.SetTexture("_NormalMap", AssetDatabase.LoadAssetAtPath<Texture2D>(normal)); m.SetFloat("_NormalScale", 0.8f); m.EnableKeyword("_NORMALMAP");
        }
        HDMaterial.ValidateMaterial(m); return m;
    }

    static string GenerateTilePng(string path, Color tile, Color grout, int n, float groutFrac)
    {
        if (File.Exists(path)) return path;
        int size = 512; var t = new Texture2D(size, size, TextureFormat.RGB24, false); var rnd = new System.Random(7);
        float cell = size / (float)n, g = cell * groutFrac;
        var shades = new float[n * n]; for (int i = 0; i < shades.Length; i++) shades[i] = 0.9f + 0.2f * (float)rnd.NextDouble();
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
        {
            float fx = x % cell, fy = y % cell; int ix = (int)(x / cell), iy = (int)(y / cell);
            bool isGrout = fx < g || fy < g; var c = isGrout ? grout : tile * shades[iy * n + ix];
            t.SetPixel(x, y, c);
        }
        t.Apply(); File.WriteAllBytes(path, t.EncodeToPNG()); Object.DestroyImmediate(t); AssetDatabase.ImportAsset(path); return path;
    }

    static void Retexture(GameObject room, string namePrefix, Material m)
    {
        foreach (var r in room.GetComponentsInChildren<MeshRenderer>()) if (r.name.StartsWith(namePrefix)) r.sharedMaterial = m;
    }

    // ---------- shared details ----------
    static void Casing(GameObject p, Opening o, float floorY, float depth = 0.20f, float w = 0.09f)
    {
        float h = o.head; var mat = mTrim;
        if (o.xWall) { Box(p, "Casing", o.at - depth / 2, o.at + depth / 2, o.a - w, o.a, floorY + o.sill, floorY + h + w, mat); Box(p, "Casing", o.at - depth / 2, o.at + depth / 2, o.b, o.b + w, floorY + o.sill, floorY + h + w, mat); Box(p, "Casing", o.at - depth / 2, o.at + depth / 2, o.a, o.b, floorY + h, floorY + h + w, mat); if (o.sill > 0.01f) Box(p, "Sill", o.at - depth / 2 - 0.03f, o.at + depth / 2 + 0.03f, o.a - w, o.b + w, floorY + o.sill - 0.04f, floorY + o.sill, mat); }
        else { Box(p, "Casing", o.a - w, o.a, o.at - depth / 2, o.at + depth / 2, floorY + o.sill, floorY + h + w, mat); Box(p, "Casing", o.b, o.b + w, o.at - depth / 2, o.at + depth / 2, floorY + o.sill, floorY + h + w, mat); Box(p, "Casing", o.a, o.b, o.at - depth / 2, o.at + depth / 2, floorY + h, floorY + h + w, mat); if (o.sill > 0.01f) Box(p, "Sill", o.a - w, o.b + w, o.at - depth / 2 - 0.03f, o.at + depth / 2 + 0.03f, floorY + o.sill - 0.04f, floorY + o.sill, mat); }
    }
    // Baseboard and crown along the four inner faces, cut around floor-level openings.
    static void Trim(GameObject p, Rect r, float floorY, float ceilH, System.Collections.Generic.IEnumerable<Opening> ops, float baseH = 0.15f, float crownH = 0.10f, float d = 0.02f)
    {
        var doors = ops.Where(o => o.sill < 0.2f).ToList();
        void Run(bool xWall, float at, float s0, float s1, bool inward)
        {
            float t0 = inward ? at : at - d, t1 = inward ? at + d : at;
            var cuts = doors.Where(o => o.xWall == xWall && Mathf.Abs(o.at - at) <= 0.3f).Select(o => (Mathf.Max(s0, o.a - 0.09f), Mathf.Min(s1, o.b + 0.09f))).OrderBy(c => c.Item1).ToList();
            float cur = s0;
            foreach (var (a, b) in cuts) { if (a > cur) SegM(p, "Baseboard", xWall, t0, t1, cur, a, floorY, floorY + baseH, mTrim); cur = Mathf.Max(cur, b); }
            if (s1 > cur) SegM(p, "Baseboard", xWall, t0, t1, cur, s1, floorY, floorY + baseH, mTrim);
            SegM(p, "Crown", xWall, inward ? at : at - 0.08f, inward ? at + 0.08f : at, s0, s1, floorY + ceilH - crownH, floorY + ceilH, mTrim);
        }
        Run(true, r.x0, r.y0, r.y1, true); Run(true, r.x1, r.y0, r.y1, false); Run(false, r.y0, r.x0, r.x1, true); Run(false, r.y1, r.x0, r.x1, false);
    }
    static void SegM(GameObject p, string n, bool xWall, float t0, float t1, float s0, float s1, float y0, float y1, Material m)
    {
        if (xWall) Box(p, n, t0, t1, s0, s1, y0, y1, m); else Box(p, n, s0, s1, t0, t1, y0, y1, m);
    }
    static GameObject Cyl(GameObject p, string n, float x, float z, float y0, float y1, float radius, Material m)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cylinder); go.name = n; go.transform.parent = p.transform;
        go.transform.position = new Vector3(x, (y0 + y1) / 2, z); go.transform.localScale = new Vector3(radius * 2, (y1 - y0) / 2, radius * 2);
        go.GetComponent<Renderer>().sharedMaterial = m; Object.DestroyImmediate(go.GetComponent<Collider>()); return go;
    }

    // ---------- foyer ----------
    static void DetailFoyer(GameObject root, Rect foyer, System.Collections.Generic.List<Opening> ops, float ceil, float upperFloorY)
    {
        var fo = root.transform.Find("Ground/foyer")?.gameObject; if (fo == null) return;
        Retexture(fo, "West", mDamask); Retexture(fo, "East", mDamask); Retexture(fo, "Front", mDamask); Retexture(fo, "Rear", mDamask);
        Retexture(fo, "Floor", mOak);
        foreach (var name in new[] { "living", "dining", "den", "sunroom" }) { var r = root.transform.Find("Ground/" + name)?.gameObject; if (r) Retexture(r, "Floor", mOak); }
        var d = Child(root.transform.Find("Ground").gameObject, "FoyerDetail");
        var foyerOps = ops.Where(o => (o.xWall && (Mathf.Abs(o.at - foyer.x0) < 0.3f || Mathf.Abs(o.at - foyer.x1) < 0.3f) && o.a >= foyer.y0 - 0.1f && o.b <= foyer.y1 + 0.1f)
                                   || (!o.xWall && (Mathf.Abs(o.at - foyer.y0) < 0.3f || Mathf.Abs(o.at - foyer.y1) < 0.3f || Mathf.Abs(o.at - 1.46f) < 0.05f) && o.a >= foyer.x0 - 0.1f && o.b <= foyer.x1 + 0.1f)).ToList();
        Trim(d, foyer, 0f, ceil, foyerOps);
        foreach (var o in foyerOps) if (o.name != "foyer_landing_arch_window") Casing(d, o, 0f);
        // Vestibule partition: the inner wall at Y 1.46 is a survey line; give it trim and a cased door.
        var vest = ops.FirstOrDefault(o => o.name == "vestibule_inner_door"); if (vest != null) Casing(d, vest, 0f);

        // Main stair: 17 risers from Y 3.7 to Y 7.9 along the west wall, rising to the upper floor.
        float x0 = 9.12f, x1 = 10.4f, y0 = 3.7f, y1 = 7.9f; int n = 17; float rise = upperFloorY / n, run = (y1 - y0) / n;
        var st = Child(d, "MainStair");
        for (int i = 0; i < n; i++)
        {
            float ya = y0 + i * run, yb = y0 + (i + 1) * run, top = (i + 1) * rise;
            Box(st, "Step", x0, x1, ya, yb + 0.03f, top - 0.06f, top, mCherry);              // tread with 3 cm nosing
            Box(st, "Riser", x0, x1, ya - 0.02f, ya + 0.01f, top - rise, top - 0.06f, mTrim);
            Box(st, "Runner", x0 + 0.3f, x1 - 0.3f, ya - 0.001f, yb + 0.032f, top, top + 0.012f, mRunner);
            Box(st, "RunnerRiser", x0 + 0.3f, x1 - 0.3f, ya - 0.012f, ya, top - rise, top, mRunner);
        }
        // Balustrade on the open (east) side: newel, balusters, handrail.
        Box(st, "Newel", x1 - 0.06f, x1 + 0.06f, y0 - 0.12f, y0, 0f, 1.1f, mCherry);
        for (int i = 0; i < n; i++)
        {
            float y = y0 + (i + 0.5f) * run, top = (i + 1) * rise;
            Box(st, "Baluster", x1 - 0.02f, x1 + 0.02f, y - 0.02f, y + 0.02f, top, top + 0.9f, mTrim);
        }
        var rail = GameObject.CreatePrimitive(PrimitiveType.Cube); rail.name = "Handrail"; rail.transform.parent = st.transform;
        float len = Mathf.Sqrt((y1 - y0) * (y1 - y0) + upperFloorY * upperFloorY), ang = Mathf.Atan2(upperFloorY, y1 - y0) * Mathf.Rad2Deg;
        rail.transform.position = new Vector3(x1, upperFloorY / 2 + 0.92f + rise / 2, (y0 + y1) / 2); rail.transform.rotation = Quaternion.Euler(-ang, 0, 0); rail.transform.localScale = new Vector3(0.07f, 0.05f, len);
        rail.GetComponent<Renderer>().sharedMaterial = mCherry; Object.DestroyImmediate(rail.GetComponent<Collider>());
        // Hide the ramp's renderer; it stays as the walking collider.
        var ramp = root.transform.Find("Ground/MainStairRamp"); if (ramp) ramp.GetComponent<MeshRenderer>().sharedMaterial = mTrim;   // visible as the painted soffit
        var bd = ops.FirstOrDefault(o => o.name == "basement_door"); if (bd != null) Casing(d, bd, 0f);
        foreach (var r in fo.GetComponentsInChildren<MeshRenderer>()) if (r.name == "Spandrel" || r.name.StartsWith("Understair")) r.sharedMaterial = mDamask;
        // Upper-hall balustrade around the well and the landing runner.
        var hallUp = root.transform.Find("Upper/upper_hall")?.gameObject;
        if (hallUp)
        {
            Retexture(hallUp, "West", mDamask); Retexture(hallUp, "East", mDamask); Retexture(hallUp, "Front", mDamask); Retexture(hallUp, "Rear", mDamask); Retexture(hallUp, "Floor", mOak);
            foreach (var r in root.transform.Find("Upper").GetComponentsInChildren<MeshRenderer>()) if (r.name.StartsWith("WellRail")) r.gameObject.SetActive(false);
            float wy0 = 4.8f;
            for (float y = wy0 + 0.1f; y < y1; y += 0.25f) Box(hallUp, "Baluster", x1 + 0.03f, x1 + 0.07f, y - 0.02f, y + 0.02f, upperFloorY, upperFloorY + 0.9f, mTrim);
            for (float x = x0 + 0.1f; x < x1; x += 0.25f) Box(hallUp, "Baluster", x - 0.02f, x + 0.02f, wy0 - 0.07f, wy0 - 0.03f, upperFloorY, upperFloorY + 0.9f, mTrim);
            Box(hallUp, "Handrail", x1, x1 + 0.1f, wy0 - 0.1f, y1, upperFloorY + 0.9f, upperFloorY + 0.95f, mCherry);
            Box(hallUp, "Handrail", x0, x1 + 0.1f, wy0 - 0.1f, wy0, upperFloorY + 0.9f, upperFloorY + 0.95f, mCherry);
            Box(hallUp, "Newel", x1 - 0.01f, x1 + 0.11f, wy0 - 0.12f, wy0, upperFloorY, upperFloorY + 1.05f, mCherry);
            var arch = ops.FirstOrDefault(o => o.name == "foyer_landing_arch_window"); if (arch != null) { Casing(hallUp, arch, 0f); Box(hallUp, "Glass", arch.a, arch.b, arch.at - 0.01f, arch.at + 0.01f, arch.sill, arch.head, mGlass); }
        }
        // Console table on the east wall, pendant in the centre.
        Box(d, "ConsoleTop", foyer.x1 - 0.42f, foyer.x1 - 0.02f, 5.0f, 6.3f, 0.78f, 0.82f, mCherry);
        foreach (var (cx, cz) in new[] { (foyer.x1 - 0.38f, 5.05f), (foyer.x1 - 0.06f, 5.05f), (foyer.x1 - 0.38f, 6.25f), (foyer.x1 - 0.06f, 6.25f) }) Box(d, "ConsoleLeg", cx - 0.02f, cx + 0.02f, cz - 0.02f, cz + 0.02f, 0f, 0.78f, mCherry);
        Cyl(d, "PendantRod", (foyer.x0 + foyer.x1) / 2 + 0.6f, 5.5f, ceil - 0.6f, ceil, 0.01f, mBlack);
        Cyl(d, "PendantShade", (foyer.x0 + foyer.x1) / 2 + 0.6f, 5.5f, ceil - 0.85f, ceil - 0.6f, 0.18f, mCream);
        // Front door leaf and the vestibule's inner door as thin panels (closed look; no interaction yet).
        var fd = ops.FirstOrDefault(o => o.name == "front_door"); if (fd != null) Box(d, "FrontDoor", fd.a, fd.b, fd.at - 0.03f, fd.at + 0.03f, 0f, fd.head, mCherry);
    }

    // ---------- kitchen / breakfast ----------
    static void DetailKitchen(GameObject root, System.Collections.Generic.List<Rect> rooms, System.Collections.Generic.List<Opening> ops, float ceil)
    {
        var bk = root.transform.Find("Ground/BreakfastKitchen")?.gameObject; if (bk == null) return;
        Rect k = rooms.First(x => x.name == "kitchen"), b = rooms.First(x => x.name == "breakfast"), s = rooms.First(x => x.name == "service_stair_bay"), e = rooms.First(x => x.name == "breakfast_extension");
        foreach (var r in bk.GetComponentsInChildren<MeshRenderer>()) { if (r.name.StartsWith("Floor_")) r.sharedMaterial = mTerracotta; else if (r.name.Contains("Wall") && !r.name.Contains("Rail")) r.sharedMaterial = mFloral; }
        var d = Child(bk, "KitchenDetail");
        // Beams across the kitchen's width, 1.1 m apart, and across the breakfast room.
        for (float y = k.y0 + 0.55f; y < k.y1; y += 1.1f) Box(d, "Beam", k.x0, k.x1, y - 0.08f, y + 0.08f, ceil - 0.22f, ceil, mBeam);
        for (float y = b.y0 + 0.55f; y < b.y1; y += 1.1f) Box(d, "Beam", s.x0, k.x0, y - 0.08f, y + 0.08f, ceil - 0.22f, ceil, mBeam);
        // Casings for every opening on the zone's walls, trim along the exterior walls.
        foreach (var o in ops.Where(o => o.name.StartsWith("kitchen_") || o.name.StartsWith("window_seat") || o.name.StartsWith("breakfast_") || o.name == "foyer_breakfast_door" || o.name == "closet_off_breakfast")) Casing(d, o, 0f);
        // Rear wall run: base cabinets with doors, blue tile top, sink under the window, uppers flanking it.
        var fx = root.transform.Find("Ground/Fixtures"); foreach (Transform t in fx) if (t.name == "RearCounter" || t.name.StartsWith("EastCounter") || t.name.StartsWith("Island") || t.name == "Fridge") t.gameObject.SetActive(false);
        float counter = 0.92f, depth = 0.62f, doorW = 0.45f;
        void BaseRun(bool xWall, float at, float s0, float s1, bool faceNeg)
        {
            // body
            if (xWall) Box(d, "CabBody", faceNeg ? at - depth : at, faceNeg ? at : at + depth, s0, s1, 0.1f, counter - 0.04f, mCherry);
            else Box(d, "CabBody", s0, s1, faceNeg ? at - depth : at, faceNeg ? at : at + depth, 0.1f, counter - 0.04f, mCherry);
            // toe kick
            if (xWall) Box(d, "ToeKick", faceNeg ? at - depth + 0.06f : at + 0.06f, faceNeg ? at : at + depth - 0.06f, s0, s1, 0f, 0.1f, mBlack);
            else Box(d, "ToeKick", s0, s1, faceNeg ? at - depth + 0.06f : at + 0.06f, faceNeg ? at : at + depth - 0.06f, 0f, 0.1f, mBlack);
            // doors with handles
            for (float p = s0 + 0.02f; p + doorW <= s1; p += doorW + 0.02f)
            {
                float f = faceNeg ? at - depth - 0.02f : at + depth;
                if (xWall) { Box(d, "CabDoor", f, f + 0.02f, p, p + doorW, 0.12f, counter - 0.06f, mCherry); Box(d, "Handle", f - 0.02f, f + 0.02f, p + doorW / 2 - 0.05f, p + doorW / 2 + 0.05f, counter - 0.2f, counter - 0.18f, mSteel); }
                else { Box(d, "CabDoor", p, p + doorW, f, f + 0.02f, 0.12f, counter - 0.06f, mCherry); Box(d, "Handle", p + doorW / 2 - 0.05f, p + doorW / 2 + 0.05f, f - 0.02f, f + 0.02f, counter - 0.2f, counter - 0.18f, mSteel); }
            }
            // tiled top with a 2 cm overhang
            if (xWall) Box(d, "CounterTop", faceNeg ? at - depth - 0.02f : at, faceNeg ? at : at + depth + 0.02f, s0, s1, counter - 0.04f, counter, mBlueTile);
            else Box(d, "CounterTop", s0, s1, faceNeg ? at - depth - 0.02f : at, faceNeg ? at : at + depth + 0.02f, counter - 0.04f, counter, mBlueTile);
        }
        // rear wall (Y = k.y1), from the back door casing to the fridge
        var door = ops.First(o => o.name == "kitchen_back_door"); var win = ops.First(o => o.name == "kitchen_rear_window");
        BaseRun(false, k.y1, door.b + 0.12f, 21.55f, true);
        // sink basin cut into the top under the window
        Box(d, "SinkBasin", win.a, win.b, k.y1 - depth + 0.08f, k.y1 - 0.1f, counter - 0.2f, counter + 0.002f, mSteel);
        Cyl(d, "Faucet", (win.a + win.b) / 2, k.y1 - 0.08f, counter, counter + 0.3f, 0.015f, mSteel);
        Box(d, "FaucetSpout", (win.a + win.b) / 2 - 0.01f, (win.a + win.b) / 2 + 0.01f, k.y1 - 0.3f, k.y1 - 0.08f, counter + 0.28f, counter + 0.3f, mSteel);
        // upper cabinets either side of the window
        Box(d, "UpperCab", door.b + 0.12f, win.a - 0.1f, k.y1 - 0.35f, k.y1, 1.45f, 2.25f, mCherry);
        Box(d, "UpperCab", win.b + 0.1f, 21.55f, k.y1 - 0.35f, k.y1, 1.45f, 2.25f, mCherry);
        // fridge in the rear-right corner, black with handles
        Box(d, "Fridge", 21.6f, k.x1 - 0.05f, k.y1 - 0.75f, k.y1 - 0.02f, 0f, 1.8f, mBlack);
        Box(d, "FridgeHandle", 21.75f, 21.78f, k.y1 - 0.78f, k.y1 - 0.76f, 0.5f, 1.4f, mSteel);
        Box(d, "FridgeHandle", 21.95f, 21.98f, k.y1 - 0.78f, k.y1 - 0.76f, 0.9f, 1.4f, mSteel);
        // east wall: counters between the two window seats, seats with red cushions
        BaseRun(true, k.x1, 14.8f, 15.9f, true); BaseRun(true, k.x1, 12.5f, 13.8f, true); BaseRun(true, k.x1, k.y0 + 0.25f, 11.5f, true);
        foreach (var (z0, z1) in new[] { (13.8f, 14.8f), (11.5f, 12.5f) })
        {
            Box(d, "SeatBox", k.x1 - 0.55f, k.x1, z0, z1, 0f, 0.42f, mCherry); Box(d, "SeatCushion", k.x1 - 0.55f, k.x1 - 0.02f, z0 + 0.02f, z1 - 0.02f, 0.42f, 0.50f, mRunner);
            Box(d, "Valance", k.x1 - 0.12f, k.x1 + 0.02f, z0 - 0.15f, z1 + 0.15f, 2.1f, 2.35f, mRunner);
        }
        foreach (var o in ops.Where(o => o.name == "kitchen_rear_window" || o.name.StartsWith("window_seat") || o.name == "breakfast_rear_window"))
        {
            if (o.xWall) Box(d, "Sheer", o.at - 0.03f, o.at - 0.01f, o.a + 0.02f, o.b - 0.02f, o.sill + 0.02f, o.head - 0.02f, mSheer);
            else Box(d, "Sheer", o.a + 0.02f, o.b - 0.02f, o.at - 0.03f, o.at - 0.01f, o.sill + 0.02f, o.head - 0.02f, mSheer);
        }
        Box(d, "Valance", door.a - 0.1f, door.b + 0.1f, k.y1 - 0.12f, k.y1 + 0.02f, door.head - 0.1f, door.head + 0.18f, mRunner);
        Box(d, "Valance", win.a - 0.15f, win.b + 0.15f, k.y1 - 0.12f, k.y1 + 0.02f, 2.1f, 2.35f, mRunner);
        var bw = ops.FirstOrDefault(o => o.name == "breakfast_rear_window"); if (bw != null) Box(d, "Valance", bw.a - 0.15f, bw.b + 0.15f, bw.at - 0.12f, bw.at + 0.02f, 2.1f, 2.35f, mRunner);
        // back door: pale glazed leaf
        Box(d, "BackDoor", door.a, door.b, k.y1 - 0.03f, k.y1 + 0.03f, 0f, door.head, mCream);
        Box(d, "BackDoorGlass", door.a + 0.1f, door.b - 0.1f, k.y1 - 0.035f, k.y1 + 0.035f, 1.0f, door.head - 0.15f, mGlass);
        // island: long leg + L foot, cherry body, blue tile top, cooktop, stools on the east side, pot rack above
        float ix0 = 19.84f, ix1 = 20.55f, iy0 = 11.68f, iy1 = 14.94f, fx0 = 18.86f, fy1 = 12.18f;
        Box(d, "IslandBody", ix0 + 0.03f, ix1 - 0.03f, iy0 + 0.03f, iy1 - 0.03f, 0.1f, counter - 0.04f, mCherry);
        Box(d, "IslandBody", fx0 + 0.03f, ix0, iy0 + 0.03f, fy1 - 0.03f, 0.1f, counter - 0.04f, mCherry);
        Box(d, "IslandTop", ix0, ix1, iy0, iy1, counter - 0.04f, counter, mBlueTile); Box(d, "IslandTop", fx0, ix0, iy0, fy1, counter - 0.04f, counter, mBlueTile);
        Box(d, "Cooktop", ix0 + 0.06f, ix1 - 0.06f, iy1 - 0.85f, iy1 - 0.15f, counter, counter + 0.01f, mBlack);
        for (float z = iy0 + 0.6f; z < iy1 - 0.3f; z += 0.65f) { Cyl(d, "StoolSeat", ix1 + 0.45f, z, 0.68f, 0.72f, 0.17f, mCherry); Cyl(d, "StoolLeg", ix1 + 0.45f, z, 0f, 0.68f, 0.025f, mCherry); }
        Box(d, "PotRack", ix0 + 0.1f, ix1 - 0.1f, iy0 + 0.6f, iy1 - 0.6f, ceil - 0.75f, ceil - 0.70f, mBeam);
        for (float z = iy0 + 0.85f; z < iy1 - 0.7f; z += 0.4f) { Cyl(d, "Pot", (ix0 + ix1) / 2, z, ceil - 0.95f, ceil - 0.87f, 0.085f, mCopper); Cyl(d, "PotHook", (ix0 + ix1) / 2, z, ceil - 0.87f, ceil - 0.75f, 0.006f, mSteel); }
        // hutch: pale glazed, on the stair stringer wall facing the table
        foreach (Transform t in fx) if (t.name == "Hutch" || t.name == "Desk") t.gameObject.SetActive(false);
        Box(d, "DeskTop", e.x1 - 0.55f, e.x1 - 0.02f, 7.9f, 8.6f, 0.72f, 0.75f, mCherry);
        foreach (var (lx, lz) in new[] { (e.x1 - 0.52f, 7.93f), (e.x1 - 0.05f, 7.93f), (e.x1 - 0.52f, 8.57f), (e.x1 - 0.05f, 8.57f) }) Box(d, "DeskLeg", lx - 0.02f, lx + 0.02f, lz - 0.02f, lz + 0.02f, 0f, 0.72f, mCherry);
        Box(d, "DeskChairSeat", e.x1 - 0.50f, e.x1 - 0.18f, 8.05f, 8.45f, 0.42f, 0.46f, mCherry);
        Box(d, "HutchBase", s.x1, s.x1 + 0.38f, 8.6f, 10.4f, 0f, 0.9f, mCream); Box(d, "HutchTop", s.x1, s.x1 + 0.28f, 8.6f, 10.4f, 1.2f, 2.1f, mCream);
        Box(d, "HutchGlass", s.x1 + 0.28f, s.x1 + 0.29f, 8.65f, 10.35f, 1.25f, 2.05f, mGlass); Box(d, "HutchCounter", s.x1, s.x1 + 0.40f, 8.58f, 10.42f, 0.9f, 0.93f, mCream);
        // breakfast table: oak top on a pedestal, six chairs
        foreach (Transform t in fx) if (t.name == "BreakfastTable") t.gameObject.SetActive(false);
        float tx = 16.45f, tz = 9.5f;
        Cyl(d, "TableTop", tx, tz, 0.72f, 0.76f, 0.55f, mCherry); Box(d, "TableTopLong", tx - 0.5f, tx + 0.5f, tz - 1.05f, tz + 1.05f, 0.72f, 0.76f, mCherry); Cyl(d, "Pedestal", tx, tz, 0f, 0.72f, 0.12f, mCherry);
        foreach (var (cx, cz, side) in new[] { (tx - 0.72f, tz - 0.55f, -1), (tx - 0.72f, tz + 0.55f, -1), (tx + 0.72f, tz - 0.55f, 1), (tx + 0.72f, tz + 0.55f, 1), (tx, tz - 1.25f, 0), (tx, tz + 1.25f, 0) })
        {
            Box(d, "ChairSeat", cx - 0.2f, cx + 0.2f, cz - 0.2f, cz + 0.2f, 0.42f, 0.46f, mCherry);
            if (side != 0) Box(d, "ChairBack", cx + side * 0.17f, cx + side * 0.2f, cz - 0.2f, cz + 0.2f, 0.46f, 0.95f, mCherry); else Box(d, "ChairBack", cx - 0.2f, cx + 0.2f, cz + (cz < tz ? -0.2f : 0.17f), cz + (cz < tz ? -0.17f : 0.2f), 0.46f, 0.95f, mCherry);
            foreach (var (lx, lz) in new[] { (-0.17f, -0.17f), (0.17f, -0.17f), (-0.17f, 0.17f), (0.17f, 0.17f) }) Box(d, "ChairLeg", cx + lx - 0.015f, cx + lx + 0.015f, cz + lz - 0.015f, cz + lz + 0.015f, 0f, 0.42f, mCherry);
        }
        // service stair: give the flight treads on top of the ramp collider and paint the rail white
        var flight = bk.transform.Find("ServiceStairFlight"); if (flight) { flight.GetComponent<MeshRenderer>().sharedMaterial = mRunner; }
        foreach (var r in bk.GetComponentsInChildren<MeshRenderer>()) if (r.name.Contains("Rail") || r.name == "ServiceStairStringerWall") r.sharedMaterial = mTrim;

    }
}
