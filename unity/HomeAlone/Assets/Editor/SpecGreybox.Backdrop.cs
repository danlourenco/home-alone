using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

// Window winter backdrops (user Oct 17: "change the windows such that you don't see outside but rather a nice fake backdrop that looks
// like a realistic winter scene"; overnight5). A photographic dome around the house, R 75 m from its middle: by day Poly Haven's
// "Snowy Park 01" (CC0; overcast, bare trees, snow), by night the same panorama as a winter night; at night the film's own lit front
// (film 5546, mirrored) stands across Lincoln Avenue as a cut-out card. Textures: tools/house/window_backdrop.py -> Textures/Backdrop.
// Unlit emissive, no shadows, no collider, not static: out of the bake (the sky still lights the house), out of the walk.
// The stand-in neighbour houses (fake-looking boxes through the den and living windows) cast shadows only, and every exterior
// renderer beyond the dome (hidden by it anyway) is disabled (perf). The yard, street, street trees, poles and wires inside it stay.
public static partial class SpecGreybox
{
    public static float DomeRadius = 75f, DomeDayNits = 9000f, DomeClearNits = 9000f, DomeNightNits = 600f, CardNightNits = 300f, MoonLux = 30f, DomeYawU = 0.55f;
    static readonly Vector3 DomeCentreXZ = new Vector3(3f, 0f, -8f);   // the house's middle (front x 10.3, back -5; z +4 .. -20)
    public const uint LayerOutside = 8;   // the exterior's own rendering layer (the moon lights only it)
    const string BackdropDir = "Assets/Textures/Backdrop";

    public static void WindowBackdrop(GameObject dayLayer, GameObject nightLayer, float gy)
    {
        if (dayLayer == null || nightLayer == null) { Debug.LogWarning("Backdrop: no day/night layer"); return; }
        Texture2D Tex(string n, int max, bool alpha)
        {
            string p = $"{BackdropDir}/{n}";
            if (AssetImporter.GetAtPath(p) is TextureImporter ti && (ti.maxTextureSize != max || ti.alphaIsTransparency != alpha || ti.wrapModeV != TextureWrapMode.Clamp))
            { ti.maxTextureSize = max; ti.alphaIsTransparency = alpha; ti.wrapModeU = alpha ? TextureWrapMode.Clamp : TextureWrapMode.Repeat; ti.wrapModeV = TextureWrapMode.Clamp;
              ti.mipmapEnabled = true; ti.anisoLevel = 4; ti.textureCompression = TextureImporterCompression.CompressedHQ; ti.SaveAndReimport(); }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(p);
        }
        Material Glow(string n, Texture2D t, float nits, bool cutout)
        {
            string path = $"Assets/Materials/Greybox/{n}.mat"; var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(Shader.Find("HDRP/Unlit")); AssetDatabase.CreateAsset(m, path); }
            m.SetColor("_UnlitColor", new Color(0, 0, 0, 1)); m.SetTexture("_UnlitColorMap", t);   // alpha (the card's cut) from the map
            m.SetTexture("_EmissiveColorMap", t); m.SetColor("_EmissiveColor", Color.white * nits); m.SetFloat("_EmissiveExposureWeight", 1f);
            m.SetFloat("_AlphaCutoffEnable", cutout ? 1f : 0f); m.SetFloat("_AlphaCutoff", 0.5f);
            m.SetFloat("_DoubleSidedEnable", 1f);
            HDMaterial.ValidateMaterial(m); EditorUtility.SetDirty(m); return m;
        }
        var c = new Vector3(DomeCentreXZ.x, gy + 3f, DomeCentreXZ.z);   // between the two storeys' eyes: the photo's horizon at eye level
        var day = Dome(dayLayer.transform, "WinterBackdrop_Day", c, Glow("Backdrop_DomeDay", Tex("dome_day.jpg", 8192, false), DomeDayNits, false));
        Dome(nightLayer.transform, "WinterBackdrop_Night", c, Glow("Backdrop_DomeNight", Tex("dome_night.jpg", 4096, false), DomeNightNits, false));
        // O: sunny / morning / overcast (Scripts/HouseWeather.cs; user Oct 19). The clear-winter dome (Poly Haven Horn-koppe Snow, CC0; Snowy Cemetery until walk note Oct 19 09:04,
        // its sun rolled to the film's azimuth by tools/house/window_backdrop.py) for the sunny states, the Snowy Park one when overcast
        {
            var wx = new GameObject("Weather - press O").AddComponent<HouseWeather>(); wx.transform.SetParent(dayLayer.transform, false);
            wx.sun = dayLayer.transform.Find("Sun")?.GetComponent<Light>(); wx.dome = day.GetComponent<MeshRenderer>();
            wx.overcastDome = day.GetComponent<MeshRenderer>().sharedMaterial;
            wx.clearDome = Glow("Backdrop_DomeDayClear", Tex("dome_day_clear.jpg", 8192, false), DomeClearNits, false);
            wx.frontAzimuth = FrontAzimuth; wx.sunny.az = wx.overcast.az = wx.domeSunAzimuth = SunAzimuth; wx.sunny.el = SunElevation;
            string op = "Assets/Settings/OvercastSky.asset"; AssetDatabase.DeleteAsset(op);
            var prof = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(prof, op);
            var env = prof.Add<VisualEnvironment>(true); env.skyType.value = (int)SkyType.Gradient; AssetDatabase.AddObjectToAsset(env, prof);
            var g = prof.Add<GradientSky>(true); AssetDatabase.AddObjectToAsset(g, prof);   // tuned live against film 6399 (Oct 19)
            g.top.value = new Color(0.70f, 0.72f, 0.76f); g.middle.value = new Color(0.62f, 0.63f, 0.65f); g.bottom.value = new Color(0.30f, 0.30f, 0.31f);
            g.skyIntensityMode.value = SkyIntensityMode.Lux; g.desiredLuxValue.value = 18000f;
            var ov = new GameObject("OvercastSky").AddComponent<Volume>(); ov.transform.SetParent(wx.transform, false); ov.isGlobal = true; ov.priority = 6f; ov.sharedProfile = prof;
            wx.overcastSky = ov; wx.Apply(wx.state);   // the scene is saved Sunny
        }
        // the film's front across the street: 26 m wide (the house fills 90% of the frame; ours is ~24 m), bottom at the far lots
        var card = GameObject.CreatePrimitive(PrimitiveType.Quad); card.name = "WinterBackdrop_NightHouse";
        Object.DestroyImmediate(card.GetComponent<Collider>()); card.transform.SetParent(nightLayer.transform, false);
        float w = 26f, h = w * 1058f / 1920f;
        card.transform.SetPositionAndRotation(new Vector3(52f, gy - 2.2f + h / 2f, -9.7f), Quaternion.Euler(0, 90f, 0));   // faces -x (the house)
        card.transform.localScale = new Vector3(w, h, 1f);
        Quiet(card.GetComponent<MeshRenderer>(), Glow("Backdrop_NightHouse", Tex("card_night.png", 2048, true), CardNightNits, true));

        // Buzz's desk-wall window (user Oct 18): the film's own POV out of it, Marley shovelling by the trash can (film 546) at night,
        // Christmas morning (film 12510) by day. Since the guest room over the den (Oct 18, TRIAL; changes/2026-10-18-guest-room.json,
        // DEVIATIONS 92) stands behind this wall, it is a SET window: the card fills the opening just behind the glass (the middle third of
        // each still, u 0.34-0.66: what the desk saw of the old 7 m card 2.5 m out), with a closed panel behind it, so the guest room and the
        // street see a flat wall. Spec: wall z 15.998-16.138, window x 10.197-10.917, sill 0.81 / head 2.15, glass at z 16.062-16.074
        const float bx0 = 10.197f, bx1 = 10.917f, by0 = 0.81f, by1 = 2.15f, bCard = 16.105f, bPanel0 = 16.115f, bPanel1 = 16.125f;
        var setRoot = GameObject.Find("Upstairs") ?? nightLayer.transform.root.gameObject;
        var panel = GameObject.CreatePrimitive(PrimitiveType.Cube); panel.name = "BuzzSetWindow_Panel"; panel.transform.SetParent(setRoot.transform, false);
        panel.transform.position = new Vector3((bx0 + bx1) / 2f, (by0 + by1) / 2f, -(bPanel0 + bPanel1) / 2f);
        panel.transform.localScale = new Vector3(bx1 - bx0 - 0.004f, by1 - by0 - 0.004f, bPanel1 - bPanel0);   // 2 mm inside the reveal: no coplanar faces
        panel.GetComponent<MeshRenderer>().sharedMaterial = mWall; panel.isStatic = true;
        var pov = GameObject.CreatePrimitive(PrimitiveType.Quad); pov.name = "WinterBackdrop_BuzzPOV";
        Object.DestroyImmediate(pov.GetComponent<Collider>()); pov.transform.SetParent(nightLayer.transform, false);
        {
            string mp = "Assets/Materials/Greybox/BuzzPOVCard.asset"; AssetDatabase.DeleteAsset(mp);
            var mesh = Object.Instantiate(pov.GetComponent<MeshFilter>().sharedMesh); mesh.name = "BuzzPOVCard";
            mesh.uv = mesh.uv.Select(u => new Vector2(0.34f + 0.32f * u.x, u.y)).ToArray();
            AssetDatabase.CreateAsset(mesh, mp); pov.GetComponent<MeshFilter>().sharedMesh = mesh;
        }
        pov.transform.SetPositionAndRotation(new Vector3((bx0 + bx1) / 2f, (by0 + by1) / 2f, -bCard), Quaternion.Euler(0, 180f, 0));   // faces +z (the room)
        pov.transform.localScale = new Vector3(bx1 - bx0, by1 - by0, 1f);
        Quiet(pov.GetComponent<MeshRenderer>(), Glow("Backdrop_BuzzPOV", Tex("buzz_pov_night.jpg", 2048, false), CardNightNits, false));
        var povDay = Object.Instantiate(pov, dayLayer.transform, true); povDay.name = "WinterBackdrop_BuzzPOVDay";
        Quiet(povDay.GetComponent<MeshRenderer>(), Glow("Backdrop_BuzzPOVDay", Tex("buzz_pov_day.jpg", 2048, false), DomeDayNits, false));

        // moonlight on the yard's snow only (rendering layer 8, which only the exterior carries): without it the lawn under the lower
        // sashes was black at night (film 5546: the snow reads blue-grey). No shadows (cheap); it never reaches a room
        var moon = new GameObject("Moonlight").AddComponent<Light>(); moon.transform.SetParent(nightLayer.transform, false);
        moon.type = LightType.Directional; moon.transform.rotation = Quaternion.Euler(35f, -60f, 0f);
        var moonHd = moon.gameObject.AddComponent<HDAdditionalLightData>();   // first: adding it resets the light's intensity
        moon.intensity = MoonLux; moon.color = new Color(0.62f, 0.72f, 1f); moon.shadows = LightShadows.None; moon.lightmapBakeType = LightmapBakeType.Realtime;
        moon.renderingLayerMask = (int)LayerOutside; moonHd.lightlayersMask = (UnityEngine.Rendering.HighDefinition.RenderingLayerMask)LayerOutside;

        // what the dome replaces: the neighbour stand-ins, and anything outside it
        var ext = GameObject.Find("Exterior");
        int off = 0, far = 0;
        if (ext != null)
        {
            // shadows only: they still shade the house as before (a stand-in beside us kept the low sun off Buzz's windows; removed, the
            // sheers lit up in stripes), but are never seen
            foreach (var t in ext.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Neighbor house")).ToList())
            { foreach (var r in t.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = ShadowCastingMode.ShadowsOnly; off++; }
            foreach (var r in ext.GetComponentsInChildren<Renderer>(true))
            {
                r.renderingLayerMask |= LayerOutside;
                var b = r.bounds; var d = new Vector2(b.center.x - c.x, b.center.z - c.z).magnitude - new Vector2(b.extents.x, b.extents.z).magnitude;
                if (d > DomeRadius) { r.enabled = false; far++; }
            }
        }
        Debug.Log($"Backdrop: dome R {DomeRadius} at {c} (day {DomeDayNits} nits, night {DomeNightNits}), night card {CardNightNits}; " +
                  $"{off} neighbour stand-ins off, {far} exterior renderers beyond the dome disabled; {day.GetComponent<MeshFilter>().sharedMesh.vertexCount} verts");
    }

    static void Quiet(MeshRenderer r, Material m)
    {
        r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        r.lightProbeUsage = LightProbeUsage.Off; r.reflectionProbeUsage = ReflectionProbeUsage.Off;
        GameObjectUtility.SetStaticEditorFlags(r.gameObject, 0);
    }

    // an inward lat-long dome, elevation -25 .. +90 deg (below that the ground hides it); u = DomeYawU at +x (the front), growing toward -z
    static GameObject Dome(Transform parent, string name, Vector3 c, Material m)
    {
        const int nu = 128, nv = 40; const float e0 = -25f, e1 = 90f;
        var v = new Vector3[(nu + 1) * (nv + 1)]; var uv = new Vector2[v.Length]; var tri = new int[nu * nv * 6];
        for (int j = 0; j <= nv; j++)
            for (int i = 0; i <= nu; i++)
            {
                float u = i / (float)nu, e = Mathf.Lerp(e0, e1, j / (float)nv) * Mathf.Deg2Rad, a = (u - DomeYawU) * 2f * Mathf.PI;
                v[j * (nu + 1) + i] = DomeRadius * new Vector3(Mathf.Cos(e) * Mathf.Cos(a), Mathf.Sin(e), -Mathf.Cos(e) * Mathf.Sin(a));
                uv[j * (nu + 1) + i] = new Vector2(u, 0.5f + e / Mathf.PI);
            }
        int k = 0;
        for (int j = 0; j < nv; j++)
            for (int i = 0; i < nu; i++)
            {
                int a = j * (nu + 1) + i, b = a + 1, d = a + nu + 1, e = d + 1;
                tri[k++] = a; tri[k++] = b; tri[k++] = d; tri[k++] = b; tri[k++] = e; tri[k++] = d;
            }
        var mesh = new Mesh { name = name, vertices = v, uv = uv, triangles = tri };
        mesh.RecalculateNormals(); mesh.bounds = new Bounds(Vector3.zero, Vector3.one * DomeRadius * 2.2f);
        string mp = $"Assets/Materials/Greybox/{name}.asset"; AssetDatabase.DeleteAsset(mp); AssetDatabase.CreateAsset(mesh, mp);
        var g = new GameObject(name); g.transform.SetParent(parent, false); g.transform.position = c;
        g.AddComponent<MeshFilter>().sharedMesh = mesh; Quiet(g.AddComponent<MeshRenderer>(), m);
        return g;
    }
}
