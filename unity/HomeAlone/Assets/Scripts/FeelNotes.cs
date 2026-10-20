using System.Collections;
using System.IO;
using UnityEngine;

/// Walk-and-annotate: how does this spot FEEL compared with the film / Marina? Works in every scene with an
/// FpsController (attached automatically on Play). Press M (mark): a screenshot is taken, then a small panel asks
/// "feels right / feels off / not sure" plus a note. Each note is one JSON line in spec/feedback/feel-notes.jsonl
/// with the scene, position, view direction and screenshot, so tools/house/feel_notes.py can map it to a room. It also records the
/// camera's eye height (world y), vertical fov, Kevin/adult body and day/night, so tools/house/note_views.py replays the exact view.
public class FeelNotes : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Attach()
    {
        foreach (var fc in Object.FindObjectsByType<FpsController>())
            if (!fc.GetComponent<FeelNotes>()) fc.gameObject.AddComponent<FeelNotes>();
    }

    // the editor writes into the repo (feel_notes.py reads it); a standalone player has no repo beside it, so its notes and shots go to
    // the app's data folder (macOS: ~/Library/Application Support/<bundle id>/feedback, i.e. com.homealone.local)
    static string Dir => Application.isEditor ? Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/feedback"))
                                              : Path.Combine(Application.persistentDataPath, "feedback");
    bool open; string note = "", rating = "", light = "", shot = ""; int saved; string flash = ""; float flashUntil;
    FpsController fc;

    void Start()
    {
        fc = GetComponent<FpsController>();
        Directory.CreateDirectory(Path.Combine(Dir, "shots"));
        var f = Path.Combine(Dir, "feel-notes.jsonl");
        if (File.Exists(f)) saved = File.ReadAllLines(f).Length;
    }

    void Update()
    {
        if (!open && Input.GetKeyDown(KeyCode.M)) StartCoroutine(Begin());
    }

    IEnumerator Begin()
    {
        yield return new WaitForEndOfFrame();            // screenshot before the panel is drawn
        var tex = ScreenCapture.CaptureScreenshotAsTexture();
        shot = $"shots/{System.DateTime.Now:yyyyMMdd-HHmmss}-{UnityEngine.SceneManagement.SceneManager.GetActiveScene().name}.png";
        File.WriteAllBytes(Path.Combine(Dir, shot), tex.EncodeToPNG()); Destroy(tex);
        open = true; note = ""; rating = ""; light = "";
        if (fc) fc.enabled = false;
        Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
    }

    void Close()
    {
        open = false;
        if (fc) fc.enabled = true;
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
    }

    void Save()
    {
        var c = Camera.main; var cam = c ? c.transform : transform;
        var p = transform.position; var e = cam.eulerAngles;
        var hm = Object.FindAnyObjectByType<HouseNightMode>();
        string Esc(string s) => s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", " ");
        var line = $"{{\"time\":\"{System.DateTime.Now:s}\",\"scene\":\"{UnityEngine.SceneManagement.SceneManager.GetActiveScene().name}\"," +
                   $"\"pos\":[{p.x:F3},{p.y:F3},{p.z:F3}],\"yaw\":{e.y:F1},\"pitch\":{(e.x > 180 ? e.x - 360 : e.x):F1}," +
                   $"\"eye\":{cam.position.y:F3},\"fov\":{(c ? c.fieldOfView : 60f):F1},\"kid\":{(fc && fc.kid ? "true" : "false")},\"night\":{(hm && hm.night ? "true" : "false")}," +
                   $"\"rating\":\"{rating}\",\"lighting\":\"{light}\",\"note\":\"{Esc(note)}\",\"shot\":\"{shot}\"}}";
        File.AppendAllText(Path.Combine(Dir, "feel-notes.jsonl"), line + "\n");
        saved++; flash = $"Saved note {saved} (shape {rating}, lighting {light})"; flashUntil = Time.time + 2f;
        Close();
    }

    void OnGUI()
    {
        var hint = new GUIStyle(GUI.skin.label) { fontSize = 16 }; hint.normal.textColor = Color.white;
        GUI.Label(new Rect(14, Screen.height - 34, 900, 28),
                  Time.time < flashUntil ? flash : $"M: mark how this spot feels   ({saved} notes so far)", hint);
        if (!open) return;
        var w = 600f; var r = new Rect((Screen.width - w) / 2, Screen.height / 2 - 130, w, 255);
        GUI.Box(r, "How does this spot feel compared with the film / Marina?");
        GUILayout.BeginArea(new Rect(r.x + 16, r.y + 34, w - 32, 215));
        GUILayout.BeginHorizontal(); GUILayout.Label("Shape / size", GUILayout.Width(90));
        foreach (var opt in new[] { "right", "off", "not sure" })
            if (GUILayout.Toggle(rating == opt, opt, "Button", GUILayout.Height(30))) rating = opt;
        GUILayout.EndHorizontal();
        GUILayout.BeginHorizontal(); GUILayout.Label("Lighting", GUILayout.Width(90));
        foreach (var opt in new[] { "right", "off", "not sure" })
            if (GUILayout.Toggle(light == opt, opt, "Button", GUILayout.Height(30))) light = opt;
        GUILayout.EndHorizontal();
        GUILayout.Label("What feels right or off? (size, shape, a doorway, the route, lighting...)");
        GUI.SetNextControlName("note");
        note = GUILayout.TextArea(note, GUILayout.Height(60));
        GUI.FocusControl("note");
        GUILayout.BeginHorizontal();
        GUI.enabled = rating != "" && light != "";
        if (GUILayout.Button("Save  (Enter)", GUILayout.Height(30)) ||
            (rating != "" && light != "" && Event.current.type == EventType.KeyDown && Event.current.keyCode == KeyCode.Return && !Event.current.shift)) Save();
        GUI.enabled = true;
        if (GUILayout.Button("Cancel  (Esc)", GUILayout.Height(30)) ||
            (Event.current.type == EventType.KeyDown && Event.current.keyCode == KeyCode.Escape)) Close();
        GUILayout.EndHorizontal();
        GUILayout.EndArea();
    }
}
