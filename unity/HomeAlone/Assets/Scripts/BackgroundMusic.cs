using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

// Background music: tracks live in  unity/HomeAlone/Assets/StreamingAssets/LocalMedia/  (gitignored: the user's tracks never enter
// the public repo) as  music.mp3  (the main track) and  music_<phase>.mp3  (e.g. music_prep.mp3 for the trap-setting phase);
// .ogg / .wav work too. Starts itself in Play, no scene object needed; a missing file means silence, no errors.
// Default volume 20% (user, Oct 19 walk). Game code switches with BackgroundMusic.Phase("prep") / Phase("") for the main track. Keys: J pause, - / = volume,
// U cycles the tracks (for listening until the game has phases). 2-D (the same in every room).
public class BackgroundMusic : MonoBehaviour
{
    static readonly (string ext, AudioType type)[] Files = { ("mp3", AudioType.MPEG), ("ogg", AudioType.OGGVORBIS), ("wav", AudioType.WAV) };
    static readonly string[] Phases = { "", "prep" };
    static BackgroundMusic inst;
    readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();
    AudioSource src;
    string current;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot() { var g = new GameObject("BackgroundMusic"); DontDestroyOnLoad(g); inst = g.AddComponent<BackgroundMusic>(); }

    public static void Phase(string phase) { if (inst) inst.StartCoroutine(inst.Switch(phase ?? "")); }

    void Awake()
    {
        src = gameObject.AddComponent<AudioSource>();
        src.loop = true; src.spatialBlend = 0f; src.volume = 0.20f; src.playOnAwake = false;
    }

    void Start() => StartCoroutine(Switch(""));

    IEnumerator Switch(string phase)
    {
        if (phase == current) yield break;
        current = phase;
        if (!clips.ContainsKey(phase)) yield return Load(phase);
        if (current != phase) yield break;   // another switch arrived while this one loaded
        var clip = clips[phase];
        if (clip == null) { src.Stop(); src.clip = null; yield break; }
        src.clip = clip; src.Play();
    }

    IEnumerator Load(string phase)
    {
        clips[phase] = null;
        foreach (var (ext, type) in Files)
        {
            var path = Path.Combine(Application.streamingAssetsPath, "LocalMedia", (phase == "" ? "music" : "music_" + phase) + "." + ext);
            if (!File.Exists(path)) continue;
            using var req = UnityWebRequestMultimedia.GetAudioClip("file://" + path, type);
            yield return req.SendWebRequest();
            if (req.result != UnityWebRequest.Result.Success) { Debug.LogWarning("BackgroundMusic: " + req.error); yield break; }
            clips[phase] = DownloadHandlerAudioClip.GetContent(req);
            yield break;
        }
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.U)) Phase(Phases[(System.Array.IndexOf(Phases, current) + 1) % Phases.Length]);
        if (!src.clip) return;
        if (Input.GetKeyDown(KeyCode.J)) { if (src.isPlaying) src.Pause(); else src.UnPause(); }
        if (Input.GetKeyDown(KeyCode.Minus)) src.volume = Mathf.Max(0f, src.volume - 0.1f);
        if (Input.GetKeyDown(KeyCode.Equals)) src.volume = Mathf.Min(1f, src.volume + 0.1f);
    }
}
