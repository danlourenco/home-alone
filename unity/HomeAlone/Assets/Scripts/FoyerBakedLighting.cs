using System;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;

public class FoyerBakedLighting : MonoBehaviour
{
    [Serializable] public class State
    {
        public Texture2D[] color, direction;
        public int[] index;
        public Vector4[] scaleOffset;
    }
    public Renderer[] surfaces;
    public State day=new State(), night=new State();
    public HDAdditionalReflectionData[] reflections;
    public UnityEngine.Rendering.Volume nightExposure;
    public UnityEngine.Rendering.Volume dayExposure;
    void Start(){var mode=FindFirstObjectByType<HouseNightMode>();Apply(mode&&mode.night);}
    public void Apply(bool isNight)
    {
        if(nightExposure)nightExposure.enabled=isNight;
        if(dayExposure)dayExposure.enabled=!isNight;
        var s=isNight?night:day;
        if(s.color!=null&&s.color.Length>0){
            var maps=new LightmapData[s.color.Length];
            for(int i=0;i<maps.Length;i++)maps[i]=new LightmapData{lightmapColor=s.color[i],lightmapDir=s.direction[i]};
            LightmapSettings.lightmapsMode=LightmapsMode.CombinedDirectional;LightmapSettings.lightmaps=maps;
            for(int i=0;i<surfaces.Length;i++)if(surfaces[i]){surfaces[i].lightmapIndex=s.index[i];surfaces[i].lightmapScaleOffset=s.scaleOffset[i];}
        }
        if(reflections!=null)foreach(var p in reflections)if(p)p.RequestRenderNextUpdate();
    }
}
