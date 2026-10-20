using UnityEngine;

// The Mac app's start pose (user, Oct 20: "start me facing the house between the piers"): on the front walk between the piers, facing
// the house. Player builds only; the editor keeps its own spawn (unity_pipeline.sh load uses HA_START). The perf tour (-perfprobe)
// sets its own poses, so it is left alone. Override: -start x,y,z,yaw (world metres, yaw degrees).
public static class AppStart
{
    static readonly Vector4 Piers = new Vector4(28.55f, -4.10f, -9.716f, 270f);   // x, y (feet), z, yaw: in the gap on the pier line (piers x 28.30-28.80), walk centre z

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Place()
    {
        var a = System.Environment.GetCommandLineArgs();
        if (Application.isEditor || System.Array.IndexOf(a, "-perfprobe") >= 0) return;
        var p = Piers; int i = System.Array.IndexOf(a, "-start");
        if (i >= 0 && i + 1 < a.Length)
        {
            var f = a[i + 1].Split(',');
            if (f.Length == 4 && float.TryParse(f[0], out var x) && float.TryParse(f[1], out var y) && float.TryParse(f[2], out var z) && float.TryParse(f[3], out var w))
                p = new Vector4(x, y, z, w);
        }
        var fps = Object.FindAnyObjectByType<FpsController>(); if (fps == null) return;
        var cc = fps.GetComponent<CharacterController>(); if (cc) cc.enabled = false;
        fps.transform.SetPositionAndRotation(new Vector3(p.x, p.y, p.z), Quaternion.Euler(0, p.w, 0));
        if (fps.cam) fps.cam.localRotation = Quaternion.identity;
        if (cc) cc.enabled = true;
    }
}
