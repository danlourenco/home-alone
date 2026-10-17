using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;
using UnityEngine.Video;

// The den's TV plays a clip the user supplies (Oct 16, user: "if i download a clip from youtube to play it on the tv?").
// Drop an H.264 .mp4 at  unity/HomeAlone/Assets/StreamingAssets/LocalMedia/tv.mp4  (gitignored: user clips never enter the public repo).
// It plays looped from the start of Play; V toggles it on/off. No file: a dark screen,
// no errors. Picture: VideoPlayer -> RenderTexture -> the screen's emissive map; sound: a 3-D AudioSource at the TV; a small cool
// real-time light in front of the screen while it plays (created here, so it is never in the bake).
[RequireComponent(typeof(Renderer))]
public class DenTV : MonoBehaviour
{
    public RenderTexture target;
    public string file = "LocalMedia/tv.mp4";
    public float range = 9f, screenNits = 120f, glowLumens = 60f;
    public KeyCode toggleKey = KeyCode.V;
    public bool on = true;
    [Header("Walls between you and the TV (Unity audio has no occlusion of its own)")]
    public float wallLoss = 0.45f, openCutoff = 22000f, wallCutoff = 900f, smoothing = 4f;
    VideoPlayer vp; AudioSource audioSrc; AudioLowPassFilter lowpass; Light glow; Material mat; bool hasFile;
    float occVol = 1f, occCut = 22000f; readonly RaycastHit[] hits = new RaycastHit[16];

    void Start()
    {
        var r = GetComponent<Renderer>(); mat = r.material;   // an instance: the shared material keeps its dark off-state
        Clear();
        string path = Path.Combine(Application.streamingAssetsPath, file);
        hasFile = File.Exists(path);
        if (!hasFile) { Debug.Log($"DenTV: no clip at {path} (drop an H.264 .mp4 there); the screen stays off"); SetEmission(false); return; }
        audioSrc = gameObject.AddComponent<AudioSource>();
        audioSrc.spatialBlend = 1f; audioSrc.rolloffMode = AudioRolloffMode.Logarithmic; audioSrc.minDistance = 1.5f; audioSrc.maxDistance = 25f; audioSrc.playOnAwake = false;
        lowpass = gameObject.AddComponent<AudioLowPassFilter>(); lowpass.cutoffFrequency = openCutoff;   // muffled through walls (Occlude)
        vp = gameObject.AddComponent<VideoPlayer>();
        vp.playOnAwake = false; vp.isLooping = true; vp.source = VideoSource.Url; vp.url = path;
        vp.renderMode = VideoRenderMode.RenderTexture; vp.targetTexture = target; vp.aspectRatio = VideoAspectRatio.FitInside;
        vp.audioOutputMode = VideoAudioOutputMode.AudioSource; vp.EnableAudioTrack(0, true); vp.SetTargetAudioSource(0, audioSrc);
        vp.errorReceived += (p, msg) => { Debug.LogWarning("DenTV: " + msg); hasFile = false; SetEmission(false); Clear(); };
        vp.Prepare();
        var g = new GameObject("DenTV_Glow"); g.transform.SetParent(transform, false);
        g.transform.position = GetComponent<Renderer>().bounds.center + Vector3.right * 0.4f;   // the screen faces +x (spec and world)
        glow = g.AddComponent<Light>(); g.AddComponent<HDAdditionalLightData>().affectSpecular = false;   // tints the room only: as a specular it showed as two hot spots on the screen glass
        glow.type = LightType.Point; glow.range = 4f; glow.lightUnit = LightUnit.Lumen; glow.intensity = glowLumens;
        glow.useColorTemperature = true; glow.colorTemperature = 7500f; glow.shadows = LightShadows.None;   // made at run time: never in the bake
        glow.enabled = false;
    }

    void Update()
    {
        if (Input.GetKeyDown(toggleKey)) on = !on;
        if (!hasFile || vp == null) return;
        bool play = on;   // always plays when on (user, Oct 16: "automatically come on"); sound still fades with distance
        if (play && !vp.isPlaying) { vp.Play(); }
        else if (!play && vp.isPlaying) { vp.Pause(); }
        if (!on && vp.isPaused) { Clear(); }
        SetEmission(on); glow.enabled = on && vp.isPlaying;
        Occlude();
        if (glow.enabled)   // flicker with the picture: the frame's mean brightness from a tiny mip read is costly; a gentle random walk reads as TV light
            glow.intensity = Mathf.Lerp(glow.intensity, glowLumens * Random.Range(0.6f, 1.2f), 0.2f);
    }

    // Count the solid surfaces between the listener and the screen (walls, doors, shelves); each one costs `wallLoss` of the volume and
    // pulls the low-pass cutoff toward `wallCutoff`, so the next room hears a quieter, duller TV. Smoothed so it never jumps.
    void Occlude()
    {
        var l = FindFirstObjectByType<AudioListener>(); if (l == null || audioSrc == null) return;
        Vector3 from = l.transform.position, to = GetComponent<Renderer>().bounds.center, d = to - from;
        int n = Physics.RaycastNonAlloc(from, d.normalized, hits, d.magnitude, ~0, QueryTriggerInteraction.Ignore), walls = 0;
        for (int i = 0; i < n; i++)   // ignore the bookcase round the TV and the listener's own body
            if (hits[i].distance > 0.6f && hits[i].distance < d.magnitude - 1.2f) walls++;
        float vol = Mathf.Pow(1f - wallLoss, walls), cut = walls == 0 ? openCutoff : Mathf.Max(wallCutoff, openCutoff * Mathf.Pow(0.06f, walls));
        float k = 1f - Mathf.Exp(-smoothing * Time.deltaTime);
        occVol = Mathf.Lerp(occVol, vol, k); occCut = Mathf.Lerp(occCut, cut, k);
        audioSrc.volume = occVol; if (lowpass) lowpass.cutoffFrequency = occCut;
    }

    void SetEmission(bool lit) { if (mat) mat.SetColor("_EmissiveColor", lit && hasFile ? Color.white * screenNits : Color.black); }

    void Clear()
    {
        if (!target) return;
        var prev = RenderTexture.active; RenderTexture.active = target; GL.Clear(true, true, Color.black); RenderTexture.active = prev;
    }
}
