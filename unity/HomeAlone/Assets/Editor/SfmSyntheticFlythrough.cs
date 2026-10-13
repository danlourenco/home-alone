using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

// Synthetic truth for the SfM pipeline (tasks/sfm-plan.md, phase 0b).
// Flies a camera through the generated, textured House.unity (known metres) along SurveyBuilder's walk-checked route,
// writing PNG frames plus exact per-frame pose and vertical FOV to gt.json.
// Batch: Unity -batchmode -projectPath unity/HomeAlone -executeMethod SfmSyntheticFlythrough.Run -quit
public static class SfmSyntheticFlythrough
{
    const float Floor = 0f, Eye = 1.55f, Speed = 1.4f, Fps = 25f;

    // Ground-floor circuit from SurveyBuilder.WalkCheck (capsule-checked): vestibule, foyer, corridor,
    // kitchen aisles, breakfast, dining, foyer, living, den. (x, 0, y) in survey metres.
    static readonly Vector3[] Route =
    {
        new Vector3(11.2f, 0, 0.9f), new Vector3(11.2f, 0, 6.5f), new Vector3(12.9f, 0, 10.4f), new Vector3(15.2f, 0, 10.9f),
        new Vector3(15.3f, 0, 12.0f), new Vector3(18.1f, 0, 12.0f), new Vector3(18.1f, 0, 15.5f), new Vector3(21.2f, 0, 15.5f),
        new Vector3(21.2f, 0, 10.5f), new Vector3(17.7f, 0, 11.5f), new Vector3(17.7f, 0, 7.6f), new Vector3(17.7f, 0, 5.0f),
        new Vector3(16.8f, 0, 2.8f), new Vector3(15.9f, 0, 2.6f), new Vector3(11.0f, 0, 2.6f), new Vector3(6.6f, 0, 2.7f),
        new Vector3(2.0f, 0, 2.7f),
    };

    // Shots split the route by arc-length fraction; FOV changes per shot, and shot 3 zooms mid-shot.
    static readonly (float end, float fovStart, float fovEnd)[] Shots =
    {
        (0.25f, 55f, 55f), (0.50f, 42f, 42f), (0.75f, 62f, 62f), (1.00f, 50f, 36f),
    };

    public static void Run()
    {
        string outDir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../sfm-work/synthetic/render"));
        Directory.CreateDirectory(outDir);
        EditorSceneManager.OpenScene("Assets/Scenes/House.unity");

        var cumulative = new List<float> { 0 };
        for (int i = 1; i < Route.Length; i++) cumulative.Add(cumulative[i - 1] + Vector3.Distance(Route[i - 1], Route[i]));
        float total = cumulative[cumulative.Count - 1];
        int frames = Mathf.CeilToInt(total / Speed * Fps);

        var go = new GameObject("SfmSyntheticCamera");
        var cam = go.AddComponent<Camera>();
        go.AddComponent<HDAdditionalCameraData>();
        cam.nearClipPlane = 0.05f;
        var rt = new RenderTexture(1920, 1080, 24);
        cam.targetTexture = rt;
        var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
        var gt = new StringBuilder("{\"width\":1920,\"height\":1080,\"fps\":25,\"frames\":[\n");
        Vector3 smoothedFwd = Vector3.zero;

        try
        {
            for (int f = 0; f < frames; f++)
            {
                float s = Mathf.Min(f * Speed / Fps, total - 1e-3f);
                int seg = cumulative.FindLastIndex(c => c <= s);
                Vector3 pos = Vector3.Lerp(Route[seg], Route[seg + 1], (s - cumulative[seg]) / (cumulative[seg + 1] - cumulative[seg]));
                float t = f / Fps;
                // Vertical bob gives the solve height variation; it isn't only a flat walk.
                pos.y = Floor + Eye + 0.2f * Mathf.Sin(t * 0.9f);

                Vector3 dir = (Route[seg + 1] - Route[seg]).normalized;
                smoothedFwd = f == 0 ? dir : Vector3.Slerp(smoothedFwd, dir, 0.08f);
                // Marina-style pans: yaw sweeps +-35 deg around travel direction, slight pitch drift.
                var rot = Quaternion.LookRotation(smoothedFwd) * Quaternion.Euler(4f * Mathf.Sin(t * 0.5f), 35f * Mathf.Sin(t * 0.6f), 0);

                float frac = s / total;
                int shot = 0;
                while (frac > Shots[shot].end && shot < Shots.Length - 1) shot++;
                float start = shot == 0 ? 0 : Shots[shot - 1].end;
                float fov = Mathf.Lerp(Shots[shot].fovStart, Shots[shot].fovEnd, Mathf.InverseLerp(start, Shots[shot].end, frac));

                go.transform.SetPositionAndRotation(pos, rot);
                cam.fieldOfView = fov;
                cam.Render();
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(outDir, $"r_{f:D5}.png"), tex.EncodeToPNG());

                gt.Append($"{{\"i\":{f},\"shot\":{shot},\"vfov\":{fov:F4},\"pos\":[{pos.x:F5},{pos.y:F5},{pos.z:F5}],\"rot\":[{rot.x:F6},{rot.y:F6},{rot.z:F6},{rot.w:F6}]}}{(f < frames - 1 ? "," : "")}\n");
                if (f % 100 == 0) Debug.Log($"SfmSynthetic: frame {f}/{frames}");
            }
        }
        finally
        {
            RenderTexture.active = null;
            Object.DestroyImmediate(go);
            Object.DestroyImmediate(tex);
            rt.Release();
        }
        File.WriteAllText(Path.Combine(outDir, "../gt.json"), gt.Append("]}\n").ToString());
        Debug.Log($"SfmSynthetic: wrote {frames} frames + gt.json to {outDir}");
    }
}
