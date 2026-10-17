using System.Collections;
using System.IO;
using UnityEngine;

// Flicker probe: with the camera still, grab consecutive Game-view frames and count pixels whose brightness jumps by more than
// a threshold between frames (the lighting "squares" that pop in and out). A still camera on a still scene should score ~0.
//   FlickerProbe.Run("name", 120)   -> spec/captures/flicker/name.json (+ name-first.png, name-heat.png)
// Started from the unity CLI (eval) during Play; the camera is not moved.
public class FlickerProbe : MonoBehaviour
{
    public static string Last = "";
    const int Step = 2, Threshold = 25;   // sample every 2nd pixel; 25/255 luma jump counts as a pop

    public static void Run(string name, int frames)
    {
        var g = new GameObject("FlickerProbe"); g.AddComponent<FlickerProbe>().StartCoroutine(g.GetComponent<FlickerProbe>().Burst(name, frames));
    }

    IEnumerator Burst(string name, int frames)
    {
        Last = "running";
        var dir = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../spec/captures/flicker")); Directory.CreateDirectory(dir);
        byte[] prev = null; int[] heat = null; int w = 0, h = 0; long pops = 0; int popFrames = 0;
        for (int i = 0; i < frames; i++)
        {
            yield return new WaitForEndOfFrame();
            var tex = ScreenCapture.CaptureScreenshotAsTexture();
            if (i == 0) File.WriteAllBytes(Path.Combine(dir, name + "-first.png"), tex.EncodeToPNG());
            var px = tex.GetPixels32(); int tw = tex.width, th = tex.height; Destroy(tex);
            w = tw / Step; h = th / Step; var luma = new byte[w * h];
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { var c = px[(y * Step) * tw + x * Step]; luma[y * w + x] = (byte)((c.r * 54 + c.g * 183 + c.b * 19) >> 8); }
            if (prev != null && prev.Length == luma.Length)
            {
                heat ??= new int[luma.Length]; int n = 0;
                for (int k = 0; k < luma.Length; k++) if (Mathf.Abs(luma[k] - prev[k]) > Threshold) { heat[k]++; n++; }
                pops += n; if (n > 0) popFrames++;
            }
            prev = luma;
        }
        if (heat != null)
        {
            int max = 1; foreach (var v in heat) max = Mathf.Max(max, v);
            var ht = new Texture2D(w, h, TextureFormat.RGB24, false); var cols = new Color32[w * h];
            for (int k = 0; k < heat.Length; k++) { byte b = (byte)(255 * heat[k] / max); cols[k] = new Color32(b, b, b, 255); }
            ht.SetPixels32(cols); ht.Apply(); File.WriteAllBytes(Path.Combine(dir, name + "-heat.png"), ht.EncodeToPNG()); Destroy(ht);
        }
        Last = $"{{\"name\":\"{name}\",\"frames\":{frames},\"pop_pixels\":{pops},\"frames_with_pops\":{popFrames},\"sample\":\"every {Step}px, >{Threshold}/255\"}}";
        File.WriteAllText(Path.Combine(dir, name + ".json"), Last + "\n");
        Destroy(gameObject);
    }
}
