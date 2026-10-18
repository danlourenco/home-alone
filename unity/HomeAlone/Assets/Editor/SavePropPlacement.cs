using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;

// Home Alone > Save Prop Placement: after moving (W) or turning (E) props in the Scene view, write what is drawn back to the spec so
// the next build keeps it (user Oct 17: "is there any way i can just use the unity interface to easily turn and position things?").
// Store props -> spec/dressing/store_props.json (x, z, yaw, "placed_by": "user"); Buzz's trunk -> spec/dressing/buzz_trunk.json.
// Spec x = Unity x, spec z = -Unity z. Only moves over 5 mm or turns over 0.5 deg are written.
public static class SavePropPlacement
{
    static string Spec(string f) => Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/dressing/" + f));

    static Bounds Drawn(Transform t)
    {
        var rs = t.GetComponentsInChildren<Renderer>().Where(r => r.enabled).ToArray();
        return rs.Aggregate(rs[0].bounds, (a, r) => { a.Encapsulate(r.bounds); return a; });
    }

    static float Turn(PlacedProp pp)
    {
        var r = pp.GetComponentInChildren<Renderer>();
        float d = Mathf.DeltaAngle(0, (r.transform.rotation * Quaternion.Inverse(pp.rot0)).eulerAngles.y);
        return Mathf.Abs(d) < 0.5f ? 0 : d;
    }

    static JArray Pair(float a, float b) => new JArray(System.Math.Round(a, 3), System.Math.Round(b, 3));

    static void Write(string path, JObject j)
    {
        using var sw = new StreamWriter(path); using var w = new JsonTextWriter(sw) { Formatting = Formatting.Indented, Indentation = 1 };
        j.WriteTo(w); sw.WriteLine();
    }

    [MenuItem("Home Alone/Save Prop Placement")]
    static void Menu() => Save(true);

    public static string Save(bool dialog = false)
    {
        var log = new System.Text.StringBuilder(); int n = 0;
        var sp = JObject.Parse(File.ReadAllText(Spec("store_props.json")));
        foreach (var pp in Object.FindObjectsByType<PlacedProp>(FindObjectsSortMode.None))
        {
            float turn = Turn(pp);
            var drawn = pp.spec == "trunk" ? pp.GetComponentsInChildren<Transform>().First(t => t.name == "TrunkBody") : pp.transform;
            var b = Drawn(drawn); float dx = b.center.x - pp.c0.x, dz = -(b.center.z - pp.c0.z);   // the move, spec axes
            if (Mathf.Abs(dx) < 0.005f && Mathf.Abs(dz) < 0.005f && turn == 0) continue;
            // a move shifts the spec box by the move (what was drawn may sit inside the box: an open door, the fit tolerance);
            // a turn takes the drawn box, as StoreProps fits the turned model into it
            JArray Shift(JToken a, float d) => Pair((float)a[0] + d, (float)a[1] + d);
            if (pp.spec == "store_props")
            {
                var e = sp["pieces"].FirstOrDefault(q => (string)q["name"] == pp.name) as JObject;
                if (e == null) continue;
                if (turn != 0) { e["x"] = Pair(b.min.x, b.max.x); e["z"] = Pair(-b.max.z, -b.min.z); e["yaw"] = Mathf.Round(Mathf.Repeat(pp.yaw + turn, 360f)); e["back"] = ""; }
                else { e["x"] = Shift(e["x"], dx); e["z"] = Shift(e["z"], dz); }
                e["placed_by"] = "user";
                log.AppendLine($"{pp.name}: x {e["x"][0]}..{e["x"][1]} z {e["z"][0]}..{e["z"][1]}" + (turn != 0 ? $" yaw {e["yaw"]}" : "")); n++;
            }
            else if (pp.spec == "trunk")
            {
                var path = Spec("buzz_trunk.json"); var j = JObject.Parse(File.ReadAllText(path));
                if (turn != 0) { j["x"] = Pair(b.min.x, b.max.x); j["z"] = Pair(-b.max.z, -b.min.z); j["yaw_deg"] = Mathf.Round(Mathf.Repeat((float)(j["yaw_deg"] ?? 0) - turn, 360f)); }   // Blender z-up turns the other way
                else { j["x"] = Shift(j["x"], dx); j["z"] = Shift(j["z"], dz); }
                j["placement"] = "PLACED BY THE USER in the editor (Home Alone > Save Prop Placement)";
                Write(path, j);
                log.AppendLine($"trunk: x {j["x"][0]}..{j["x"][1]} z {j["z"][0]}..{j["z"][1]} (rebuild its model: Blender -b --disable-autoexec -P tools/house/purchased_trunk.py)"); n++;
            }
        }
        Write(Spec("store_props.json"), sp);
        Debug.Log($"Save Prop Placement: {n} saved\n{log}");
        if (dialog) EditorUtility.DisplayDialog("Save Prop Placement", n == 0 ? "Nothing moved." : $"Saved {n}:\n{log}", "OK");
        return $"{n} saved\n{log}";
    }
}
