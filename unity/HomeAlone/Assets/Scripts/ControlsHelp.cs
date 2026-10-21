using UnityEngine;

// F1 controls panel (user, Oct 20: "you've given me a lot of commands to test lighting and such. Could you give me a hud with controls
// to reference"). Lists every key (keep it in step with FpsController's header) plus the live values the user tunes: night white
// balance ([ ]) and render scale (P). A small "F1: controls" hint shows for the first seconds. Created at scene load; no scene edit.
public class ControlsHelp : MonoBehaviour
{
    static readonly string[] Lines =
    {
        "MOVE   WASD + mouse  ·  Shift sprint  ·  Space jump  ·  C / Left Ctrl (hold) crouch",
        "       G Kevin / adult  ·  R back to the start  ·  H walking bob  ·  Esc / Tab free the mouse",
        "DO     E doors, den chair, Buzz's footlocker, zipline (attic dormer), treehouse ladder",
        "       V den TV video  ·  M walk note + screenshot",
        "LOOK   N day / night  ·  [ ] night interior white balance (cooler / warmer)",
        "       O weather: sunny / morning / overcast  ·  F falling snow (overcast + night)",
        "       P render scale 100 / 75 / 50 / 38 %  ·  K hide everything off the lot",
        "MUSIC  J pause  ·  - / = volume  ·  U next track",
        "       F1 hide this panel",
    };
    bool show; float hintUntil; GUIStyle box, hint;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Create()
    {
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-perfprobe") >= 0) return;   // the perf tour's frames stay clean
        var go = new GameObject("ControlsHelp"); DontDestroyOnLoad(go); go.AddComponent<ControlsHelp>().hintUntil = Time.unscaledTime + 8f;
    }

    void Update() { if (Input.GetKeyDown(KeyCode.F1)) show = !show; }

    void OnGUI()
    {
        float s = Screen.height / 1080f;   // scale with the window: readable on the 5K Studio Display and in a small window
        box ??= new GUIStyle(GUI.skin.box) { alignment = TextAnchor.UpperLeft, richText = true, wordWrap = false };
        hint ??= new GUIStyle(GUI.skin.label);
        box.fontSize = Mathf.RoundToInt(17 * s); hint.fontSize = Mathf.RoundToInt(16 * s); box.padding = new RectOffset((int)(14 * s), (int)(14 * s), (int)(10 * s), (int)(10 * s));
        if (show)
        {
            string wb = PlayerPrefs.HasKey("NightWhiteBalance") ? PlayerPrefs.GetFloat("NightWhiteBalance").ToString("0") : HouseNightMode.WbDefault.ToString("0") + " (default)";
            string sc = PlayerPrefs.HasKey("RenderScale") ? PlayerPrefs.GetFloat("RenderScale").ToString("0") + " %" : RenderScale.Default.ToString("0") + " % (default)";
            string text = "<b>CONTROLS</b>\n" + string.Join("\n", Lines) + $"\n\n<b>NOW</b>   night white balance {wb}  ·  render scale {sc}  ·  {Screen.width}x{Screen.height}";
            var size = box.CalcSize(new GUIContent(text));
            GUI.Box(new Rect(20 * s, 20 * s, size.x, size.y), text, box);
        }
        else if (Time.unscaledTime < hintUntil)
            GUI.Label(new Rect(20 * s, 20 * s, 400 * s, 30 * s), "F1: controls", hint);
    }
}
