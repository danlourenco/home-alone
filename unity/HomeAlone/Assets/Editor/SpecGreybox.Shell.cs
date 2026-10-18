using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEngine;
using UnityEngine.Rendering;

// The house's exterior skin (Oct 18 2026, TRIAL; changes/2026-10-18-exterior-shell.json, DEVIATIONS 97): tools/house/exterior_shell.py
// (the film's house on our measured ground footprint) -> hifi_exterior.py -> Exterior.glb, world coordinates. Its parts are named by
// draw set: L_* always drawn (ground-storey veneer, low roofs, porch, door face), U_* the upper storey and roofs, hidden while the
// player is upstairs (HouseSplit). The U parts stand in for the film's flush upper storey in the sun's shadows exactly like
// FilmFront (LayerFilmFront: cast while the player is downstairs, out of the bake); the L parts are the house (LayerHouse).
// Upstairs and attic pieces that reach outside the skin (Marina's overhang strip, the attic's knee walls and roof) are drawn only upstairs.
public static partial class SpecGreybox
{
    static readonly List<Renderer> ShellGlow = new List<Renderer>();   // the upper sashes' drawn shades: lit at night (HouseNightMode)

    static void Shell(GameObject ext, float gy)
    {
        ShellGlow.Clear();
        var S = JObject.Parse(File.ReadAllText(Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/exterior_shell.json"))));
        var holder = new GameObject("HouseShell"); holder.transform.SetParent(ext.transform, false);
        holder.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
        var shade = AtticGlow("HiFi_ShadeExterior", new Color(0.88f, 0.83f, 0.70f), 25f, 0.15f);
        var glass = Mat("HiFi_ExtGlass", new Color(0.035f, 0.045f, 0.055f)); glass.SetFloat("_Smoothness", 0.93f);
        var g = PlaceHiFi(holder, 0f, "Exterior", new Dictionary<string, Material> {
            ["EX_Brick"] = TexMat("HiFi_ExtBrick", "red_brick_03", new Color(0.80f, 0.60f, 0.53f), 1.90f, 0.12f),   // 28 courses a tile: 68 mm (2 5/8 in) courses
            ["EX_Trim"] = Mat("HiFi_ExtTrim", new Color(0.86f, 0.85f, 0.81f)),
            ["EX_Shutter"] = Mat("HiFi_ExtShutter", new Color(0.022f, 0.026f, 0.026f)),
            ["EX_Roof"] = TexMat("HiFi_ExtRoof", "concrete_floor_worn_001", new Color(0.10f, 0.095f, 0.095f), 1.6f, 0.08f),
            ["EX_Glass"] = glass, ["EX_Shade"] = shade,
            ["EX_Stone"] = Mat("HiFi_ExtStone", new Color(0.74f, 0.70f, 0.62f)),
            ["EX_Gutter"] = Mat("HiFi_ExtGutter", new Color(0.84f, 0.84f, 0.82f)),
            ["EX_Pot"] = Mat("HiFi_ExtPot", new Color(0.50f, 0.25f, 0.16f)),
            ["EX_DoorBlack"] = Mat("HiFi_ExtDoor", new Color(0.02f, 0.025f, 0.025f)),
            ["EX_Brass"] = BrassMat(),
            ["EX_Wreath"] = Mat("HiFi_ExtWreath", new Color(0.06f, 0.16f, 0.06f)),
            ["EX_Bow"] = Mat("HiFi_ExtBow", new Color(0.55f, 0.04f, 0.04f)),
            ["EX_PorchGlass"] = mGlass });
        if (g == null) { Debug.LogWarning("Shell: Exterior.glb missing, no skin"); return; }
        var upper = new List<Renderer>();
        foreach (var r in g.GetComponentsInChildren<MeshRenderer>())
        {
            bool u = r.name.StartsWith("U_");
            r.gameObject.isStatic = true;
            r.renderingLayerMask = u ? LayerFilmFront : LayerHouse;
            r.shadowCastingMode = r.sharedMaterial == shade || r.sharedMaterial == mGlass ? ShadowCastingMode.Off : ShadowCastingMode.TwoSided;
            if (u) upper.Add(r);
            if (r.sharedMaterial == shade) ShellGlow.Add(r);
        }
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
}
