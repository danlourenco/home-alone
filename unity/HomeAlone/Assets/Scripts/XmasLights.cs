using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

// EXTERIOR CHRISTMAS LIGHTS, bake-off set (Oct 21; docs/XMAS-LIGHTS.md, .claude/skills/xmas-lights). Built by SpecGreybox.Xmas.cs. One
// build carries both looks; Mode picks one live (PerfProbe xmas=old|A|B|C, + xdecal=0, xpool=0, xinst=1):
//   old  today's mini-lights (the exterior GLB's XmasBulbs, the yard's XmasBulbs_Yard) and the 35 ShrubGlow lights   (THE DEFAULT)
//   A    C7s at the film's 0.21 m (chunked static meshes, LODGroups, 3 shared materials), physical emission + the night bloom
//   B    A + glow cards (XmasGlowCard.shader: billboards, exposed units, pixel floor, near fade)
//   C    B + the pool (24 unshadowed exterior-layer lights at the nearest strand clusters, faded) + emissive decals behind the loops
// Switching uses Renderer.forceRenderingOff (HouseSplit owns .enabled of the upper storey) and Light.enabled. Night only: the cards,
// decals and pool follow HouseNightMode.night; the bulb meshes are glass by day (HouseNightMode's glow list darkens their emission).
public class XmasLights : MonoBehaviour
{
    public enum Look { Old, A, B, C }
    public static Look Mode = Look.Old; public static bool Decals = true, Pool = true, Instanced, CardsLowRes = true;
    public Renderer[] oldRenderers = new Renderer[0];
    public Light[] oldLights = new Light[0];
    public Renderer[] bulbs = new Renderer[0];      // chunk LOD renderers and the new wire
    public Renderer[] cards = new Renderer[0];
    public GameObject decalRoot;
    public Light[] pool = new Light[0];
    public Vector3[] clusterPos = new Vector3[0];
    public float[] clusterLumens = new float[0], clusterRange = new float[0];
    // xinst=1: the same bulbs drawn with Graphics.RenderMeshInstanced (the AGENTS.md instancing rule, measured): one call per material
    public Mesh instMesh; public Material[] instMats = new Material[0];
    public Matrix4x4[] instXf = new Matrix4x4[0]; public int[] instMat = new int[0];
    static XmasLights live; HouseNightMode night; Look applied = (Look)(-1); bool appliedDecal, appliedPool, appliedInst, appliedNight;
    readonly int[] slot = new int[24]; readonly float[] weight = new float[24]; readonly bool[] outgoing = new bool[24]; float nextPick;
    List<Matrix4x4>[] instBatches;

    void Awake() { live = this; night = FindAnyObjectByType<HouseNightMode>(); for (int i = 0; i < slot.Length; i++) slot[i] = -1; }
    public static void Set(string look, bool decals, bool pool, bool inst, bool cardsLowRes = true)
    {
        Mode = look switch { "A" => Look.A, "B" => Look.B, "C" => Look.C, _ => Look.Old }; Decals = decals; Pool = pool; Instanced = inst; CardsLowRes = cardsLowRes;
        if (live) live.Apply(true);
    }
    public static string Readout() => live == null ? "\"none\"" :
        $"{{\"mode\":\"{Mode}\",\"cards_lowres\":{CardsLowRes.ToString().ToLower()},\"decals\":{Decals.ToString().ToLower()},\"pool\":{Pool.ToString().ToLower()},\"inst\":{Instanced.ToString().ToLower()},\"bulb_renderers_visible\":{live.Visible(live.bulbs)},\"card_renderers_visible\":{live.Visible(live.cards)},\"pool_lit\":{live.PoolLit()}}}";
    int Visible(Renderer[] rs) { int n = 0; foreach (var r in rs) if (r && r.isVisible && !r.forceRenderingOff && r.enabled) n++; return n; }
    int PoolLit() { int n = 0; foreach (var l in pool) if (l && l.enabled && l.intensity > 0f) n++; return n; }

    void Apply(bool force)
    {
        bool isNight = night && night.night;
        if (!force && applied == Mode && appliedDecal == Decals && appliedPool == Pool && appliedInst == Instanced && appliedNight == isNight) return;
        applied = Mode; appliedDecal = Decals; appliedPool = Pool; appliedInst = Instanced; appliedNight = isNight;
        bool old = Mode == Look.Old, nu = !old;
        foreach (var r in oldRenderers) if (r) r.forceRenderingOff = !old;
        foreach (var l in oldLights) if (l) l.enabled = old;
        foreach (var r in bulbs) if (r) r.forceRenderingOff = !nu || (Instanced && r.name.StartsWith("XmasC7_"));
        foreach (var r in cards) if (r) r.forceRenderingOff = !(isNight && Mode >= Look.B);
        // xlowres=0: the cards in the full-resolution transparent pass (3000) instead of HDRP's low-resolution one (3400), in case the
        // frame setting is off on this player (a 3400 material is then not drawn at all) or the quarter-res halo reads too soft
        if (cards.Length > 0 && cards[0] && cards[0].sharedMaterial) cards[0].sharedMaterial.renderQueue = CardsLowRes ? 3400 : 3000;
        if (decalRoot) decalRoot.SetActive(isNight && Mode == Look.C && Decals);
        bool poolOn = isNight && Mode == Look.C && Pool;
        foreach (var l in pool) if (l) { l.enabled = poolOn; if (!poolOn) l.intensity = 0f; }
        for (int i = 0; i < slot.Length; i++) { slot[i] = -1; weight[i] = 0f; outgoing[i] = false; }
        nextPick = 0f;
    }

    void Update()
    {
        Apply(false);
        if (night && night.night && Mode == Look.C && Pool) PumpPool();
        if (night && night.night && Mode != Look.Old && Instanced) DrawInstanced();   // a perf variant: night only (not in the day glow list)
    }

    // the 24 strand clusters nearest the camera (not well behind it), re-picked every 0.25 s; a slot fades its light out over 0.5 s before
    // it takes another cluster, so a cluster changing hands never pops
    void PumpPool()
    {
        var cam = Camera.main; if (!cam || pool.Length == 0) return;
        Vector3 c = cam.transform.position, f = cam.transform.forward;
        if (Time.unscaledTime >= nextPick)
        {
            nextPick = Time.unscaledTime + 0.25f;
            var best = new List<(float d, int i)>();
            for (int i = 0; i < clusterPos.Length; i++)
            {
                var v = clusterPos[i] - c;
                if (Vector3.Dot(v, f) < -clusterRange[i]) continue;   // behind the camera by more than its reach
                best.Add((v.sqrMagnitude, i));
            }
            best.Sort((x, y) => x.d.CompareTo(y.d));
            var want = new HashSet<int>(); for (int k = 0; k < best.Count && k < pool.Length; k++) want.Add(best[k].i);
            for (int s = 0; s < pool.Length; s++) if (slot[s] >= 0 && !want.Contains(slot[s])) outgoing[s] = true;
            foreach (var i in want)
            {
                int held = System.Array.IndexOf(slot, i); if (held >= 0) { outgoing[held] = false; continue; }   // wanted again: fade back in
                int free = System.Array.IndexOf(slot, -1); if (free < 0) break;
                slot[free] = i; weight[free] = 0f; outgoing[free] = false;
            }
        }
        float step = Time.unscaledDeltaTime / 0.5f;
        for (int s = 0; s < pool.Length; s++)
        {
            var l = pool[s]; if (!l) continue;
            int i = slot[s]; if (i < 0) { l.intensity = 0f; continue; }
            weight[s] = Mathf.Clamp01(weight[s] + (outgoing[s] ? -step : step));
            l.transform.position = clusterPos[i]; l.range = clusterRange[i]; l.intensity = clusterLumens[i] * weight[s];
            if (outgoing[s] && weight[s] <= 0f) { slot[s] = -1; outgoing[s] = false; }
        }
    }

    void DrawInstanced()
    {
        if (!instMesh || instMats.Length == 0) return;
        if (instBatches == null)
        {   // ponytail: 511 per call (RenderMeshInstanced without assumeuniformscaling); one list per material, built once
            instBatches = new List<Matrix4x4>[instMats.Length]; for (int m = 0; m < instMats.Length; m++) instBatches[m] = new List<Matrix4x4>();
            for (int i = 0; i < instXf.Length; i++) instBatches[instMat[i]].Add(instXf[i]);
        }
        for (int m = 0; m < instMats.Length; m++)
        {
            var rp = new RenderParams(instMats[m]) { shadowCastingMode = ShadowCastingMode.Off, lightProbeUsage = LightProbeUsage.BlendProbes, renderingLayerMask = 8 | 1 };
            var all = instBatches[m];
            for (int o = 0; o < all.Count; o += 511) Graphics.RenderMeshInstanced(rp, instMesh, 0, all, Mathf.Min(511, all.Count - o), o);
        }
    }
}
