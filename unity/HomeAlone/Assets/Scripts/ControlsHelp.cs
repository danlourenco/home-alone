using UnityEngine;
using UnityEngine.UIElements;

// F1 controls panel (user, Oct 20: "you've given me a lot of commands to test lighting and such. Could you give me a hud with controls
// to reference"). UI Toolkit (Oct 21; the project has no uGUI package): the key list is Assets/UI/Controls/Resources/ControlsPanel.uxml
// (keep it in step with FpsController's header), styled by ../ControlsPanel.uss; the "Now" strip shows the live values the user tunes
// (night white balance [ ], render scale P, resolution, day/night, weather). Also the "F1 · controls" hint (first 8 s) and RenderScale's
// P toast. Created at scene load, no scene edit; skipped under -perfprobe so the perf tour's frames stay clean.
// PanelSettings is made here, not a hand-written .asset (its YAML names a built-in script by fileID: fragile across versions); the
// theme is ControlsTheme.tss, a real imported ThemeStyleSheet. Resources.Load puts both entry points, and the USS and Inter fonts they
// reference, in a player build. Nothing is pickable: the panel never takes the mouse or keys from the FpsController.
public class ControlsHelp : MonoBehaviour
{
    const float HintSeconds = 8f, Tick = 0.25f;   // live values refresh at most 4 times a second, and only rebuild text on a change
    const string Faded = "is-faded", Hidden = "is-hidden", WbKey = "NightWhiteBalance";
    static readonly string[] Weathers = { "sunny", "morning", "overcast" };
    VisualElement panel, hint; Label toast, wbValue, scaleValue, resValue, timeValue, weatherValue;
    HouseNightMode nightMode; HouseWeather weather;
    bool open; float hintUntil, nextTick, toastStamp;
    float lastWb = float.NaN, lastMode = float.NaN, lastPct = float.NaN;
    int lastWbSaved = -1, lastW = -1, lastH = -1, lastFs = -1, lastNight = -1, lastWeather = -1;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Create()
    {
        if (System.Array.IndexOf(System.Environment.GetCommandLineArgs(), "-perfprobe") >= 0) return;   // the perf tour's frames stay clean
        var tree = Resources.Load<VisualTreeAsset>("ControlsPanel"); var theme = Resources.Load<ThemeStyleSheet>("ControlsTheme");
        if (!tree || !theme) { Debug.LogWarning("ControlsHelp: Resources ControlsPanel.uxml or ControlsTheme.tss missing, no controls panel"); return; }
        var ps = ScriptableObject.CreateInstance<PanelSettings>(); ps.name = "ControlsPanelSettings";
        ps.themeStyleSheet = theme; ps.sortingOrder = 100f;
        ps.scaleMode = PanelScaleMode.ScaleWithScreenSize; ps.referenceResolution = new Vector2Int(1920, 1080);
        ps.screenMatchMode = PanelScreenMatchMode.MatchWidthOrHeight; ps.match = 1f;   // match height: same share of a 5K display and a small window
        var go = new GameObject("ControlsHelp"); go.SetActive(false); DontDestroyOnLoad(go);   // inactive until both are set: one tree build
        var doc = go.AddComponent<UIDocument>(); doc.panelSettings = ps; doc.visualTreeAsset = tree;
        go.AddComponent<ControlsHelp>(); go.SetActive(true);
    }

    void Start()   // after UIDocument's OnEnable built the tree
    {
        var root = GetComponent<UIDocument>().rootVisualElement;
        root.pickingMode = PickingMode.Ignore; root.Query<VisualElement>().ForEach(e => e.pickingMode = PickingMode.Ignore);
        panel = root.Q("panel"); hint = root.Q("hint"); toast = root.Q<Label>("toast");
        wbValue = root.Q<Label>("wbValue"); scaleValue = root.Q<Label>("scaleValue"); resValue = root.Q<Label>("resValue");
        timeValue = root.Q<Label>("timeValue"); weatherValue = root.Q<Label>("weatherValue");
        nightMode = FindAnyObjectByType<HouseNightMode>(FindObjectsInactive.Include); weather = FindAnyObjectByType<HouseWeather>(FindObjectsInactive.Include);
        hintUntil = Time.unscaledTime + HintSeconds; toastStamp = RenderScale.ToastUntil;
    }

    void Update()
    {
        bool now = false;
        if (Input.GetKeyDown(KeyCode.F1)) { open = !open; panel.EnableInClassList(Hidden, !open); now = true; }
        if (RenderScale.ToastUntil != toastStamp) { toastStamp = RenderScale.ToastUntil; now = true; }
        float t = Time.unscaledTime;
        if (!now && t < nextTick) return;
        nextTick = t + Tick;
        hint.EnableInClassList(Faded, open || t >= hintUntil);
        bool toastOn = t < toastStamp; toast.EnableInClassList(Faded, !toastOn);
        if (!open && !toastOn) return;
        // compare the inputs first: strings are built only when one changed (no per-frame allocation)
        bool scale = Changed(ref lastMode, RenderScale.Mode) | Changed(ref lastPct, RenderScale.Percent) | Changed(ref lastW, Screen.width)
                   | Changed(ref lastH, Screen.height) | Changed(ref lastFs, (int)Screen.fullScreenMode);
        if (scale)
        {
            scaleValue.text = RenderScale.Label; resValue.text = $"{Screen.width} x {Screen.height}";
            if (toastOn) toast.text = RenderScale.ToastText;
        }
        else if (now && toastOn) toast.text = RenderScale.ToastText;
        if (Changed(ref lastWb, HouseNightMode.WbTemperature) | Changed(ref lastWbSaved, PlayerPrefs.HasKey(WbKey) ? 1 : 0))
            wbValue.text = $"{lastWb:+0;-0;0}" + (lastWbSaved == 1 ? "" : " (default)");
        if (Changed(ref lastNight, !nightMode ? -1 : nightMode.night ? 1 : 0)) timeValue.text = lastNight < 0 ? "n/a" : lastNight == 1 ? "night" : "day";
        if (Changed(ref lastWeather, weather ? (int)weather.state : -1)) weatherValue.text = lastWeather < 0 ? "n/a" : Weathers[lastWeather];
    }

    static bool Changed(ref float last, float v) { if (last == v) return false; last = v; return true; }
    static bool Changed(ref int last, int v) { if (last == v) return false; last = v; return true; }
}
