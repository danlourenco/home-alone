using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

public static partial class SpecGreybox
{
    static EntranceDoor FoyerInteractions(GameObject root, float gy)
    {
        Material Paint(string side) {
            var m=BakedMat("FrontLeaf",side);
            // Close-range live comparison: painted wood has fine orange-peel, not plaster-scale relief.
            m.SetFloat("_NormalScale",.3f); m.SetFloat("_DetailNormalScale",.1f); m.SetFloat("_DetailSmoothnessScale",.25f);
            EditorUtility.SetDirty(m); return m;
        }
        var hardware = BakedMat("FrontLeaf", "Hardware");
        hardware.SetFloat("_NormalScale",.4f); hardware.SetFloat("_DetailNormalScale",.05f); hardware.SetFloat("_DetailSmoothnessScale",.2f);
        hardware.SetFloat("_MetallicRemapMin", .8f); hardware.SetFloat("_MetallicRemapMax", .8f);
        EditorUtility.SetDirty(hardware);
        var g = PlaceHiFi(root, gy, "FrontLeaf", new System.Collections.Generic.Dictionary<string,Material> {
            ["FD_Inside"]=Paint("Inside"), ["FD_Outside"]=Paint("Outside"), ["FD_Hardware"]=hardware });
        if (!g) throw new System.InvalidOperationException("FrontLeaf is missing: the front door must not be built without its leaf");
        foreach (var c in Object.FindObjectsByType<Collider>(FindObjectsInactive.Include,FindObjectsSortMode.None))
            if (c.name=="front_door" && c.transform.parent && c.transform.parent.name=="Dressing") Object.DestroyImmediate(c);
        var hinge = new GameObject("FrontDoorHinge"); hinge.transform.SetParent(root.transform,false);
        hinge.transform.position = new Vector3(10.082f,gy,-9.312f);
        g.transform.SetParent(hinge.transform,true);
        var mounted=Child(hinge,"StoreProps");
        // Both decorations and the outside bulb string belong to this same physical leaf.
        var transforms = Object.FindObjectsByType<Transform>(FindObjectsInactive.Include,FindObjectsSortMode.None);
        foreach (var t in transforms.Where(t=>t.name=="front_door_wreath" || t.name=="FrontWreath" || t.name=="WreathBulbs"))
        {
            if (t.name!="front_door_wreath") t.position += Vector3.left*.184f;
            t.SetParent(mounted.transform,true);
        }
        foreach (var r in hinge.GetComponentsInChildren<Renderer>(true)) {
            r.gameObject.isStatic=false; r.renderingLayerMask=LayerHouse;
        }
        var leafBox=hinge.AddComponent<BoxCollider>();
        leafBox.center=new Vector3(.025f,.948f,-.4035f);leafBox.size=new Vector3(.05f,1.896f,.807f);
        var door=hinge.AddComponent<EntranceDoor>();door.leaf=hinge.transform;door.leafCollider=leafBox;
        door.locked=false;
        // Static surface/prop gates see the closed pose; EntranceCheck tests both collision states.
        door.SetInstant(false);
        var tv=Object.FindFirstObjectByType<DenTV>();
        if (tv) {
            var seatObject=new GameObject("DenMovieSeat");seatObject.transform.SetParent(root.transform,false);
            seatObject.transform.position=new Vector3(6.30f,gy,-17.06f);
            var seat=seatObject.AddComponent<DenSeat>();seat.screen=tv.GetComponent<Renderer>();
            seat.eyePosition=new Vector3(6.30f,gy+1.02f,-17.06f);seat.fieldOfView=36f;
        }
        return door;
    }

    static string EntranceCheck(EntranceDoor door,float gy)
    {
        bool Blocked() => Physics.Raycast(new Vector3(9.70f,gy+1f,-9.7155f),Vector3.right,.9f,~0,QueryTriggerInteraction.Ignore);
        door.SetInstant(false);bool closed=Blocked();
        door.SetInstant(true);bool open=!Blocked();
        door.locked=true;door.SetInstant(false);bool locked=!door.SetOpen(true);door.locked=false;
        door.SetInstant(false);
        if (!closed || !open || !locked) throw new System.InvalidOperationException($"Entrance FAIL: closed={closed}, open={open}, locked={locked}");
        return "Entrance check: closed blocks, open clears, locked refuses open; one leaf collider\n";
    }

    static void FoyerMirror(GameObject root,float gy)
    {
        var gilt=BakedMat("FoyerMirror","Gilt");gilt.SetFloat("_MetallicRemapMin",.65f);gilt.SetFloat("_MetallicRemapMax",.65f);
        PlaceHiFi(root,gy,"FoyerMirror",new System.Collections.Generic.Dictionary<string,Material>{["FM_Gilt"]=gilt});
        var go=new GameObject("FoyerMirrorProbe");go.transform.SetParent(root.transform,false);
        go.transform.position=new Vector3(5.67f,gy+1.66f,-7.806f);
        go.transform.rotation=Quaternion.Euler(0,180,0); // local forward faces the room
        var probe=go.AddComponent<PlanarReflectionProbe>();
        probe.mode=ProbeSettings.Mode.Realtime;probe.realtimeMode=ProbeSettings.RealtimeMode.EveryFrame;
        probe.settingsRaw.resolutionScalable.useOverride=true;
        probe.settingsRaw.resolutionScalable.@override=PlanarReflectionAtlasResolution.Resolution1024;
        probe.settingsRaw.proxySettings.mirrorPositionProxySpace=Vector3.zero;
        probe.settingsRaw.proxySettings.mirrorRotationProxySpace=Quaternion.identity;
        probe.influenceVolume.boxSize=new Vector3(.46f,1.0f,.16f);
        probe.influenceVolume.boxBlendDistancePositive=Vector3.zero;
        probe.influenceVolume.boxBlendDistanceNegative=Vector3.zero;
        probe.lightLayers=(UnityEngine.Rendering.HighDefinition.RenderingLayerMask)255;probe.importance=100;
        var glass=AssetDatabase.LoadAssetAtPath<Material>("Assets/Materials/Greybox/HiFi_MirrorGlass.mat");
        if (glass) { glass.SetFloat("_Smoothness",1f); glass.SetFloat("_Metallic",1f);EditorUtility.SetDirty(glass); }
    }
}
