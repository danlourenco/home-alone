// Glow cards for the Christmas lights (docs/XMAS-LIGHTS.md 3.2; SpecGreybox.Xmas.cs builds one mesh per strand chunk: 4 vertices per
// bulb, all at the bulb's centre, UV0 = the corner (+-1, +-1), colour = the bulb's tint (rgb) and intensity (a)). The vertex stage turns
// each quad to the camera and sizes it r = max(_RadiusM, _MinPx pixels at its depth): the film's halo (5545: 5.4 cm glow, 11 cm halo)
// up close, a pixel floor far away (a sub-pixel bulb otherwise aliases away). The quad is pulled toward the camera by r, so it never
// cuts into the wall it hangs on (no depth sampling needed). Additive, no lighting, analytic falloff (no texture).
// Output is in EXPOSED units: HDRP's colour buffer is pre-exposed, so a value written here is what the tonemapper sees at any EV
// (the emission level "set by maths relative to the night EV"). Drawn in the low-resolution transparent pass (render queue 3400).
// ponytail: no fog on the cards (volumetric fog's 110 m mean free path dims a 25 m bulb ~20 %); add HDRP's EvaluateAtmosphericScattering if the bake-off shows it
Shader "HomeAlone/XmasGlowCard"
{
    Properties
    {
        _Gain("Gain (exposed units)", Float) = 1.2
        _CoreGain("Core", Float) = 2.0
        _HaloGain("Halo", Float) = 0.45
        _CoreSigma("Core width (fraction of r)", Float) = 0.22
        _RadiusM("Radius (m)", Float) = 0.11
        _MinPx("Minimum radius (px)", Float) = 3.0
        _NearFade("Near fade start, end (m)", Vector) = (3, 5, 0, 0)
    }
    SubShader
    {
        Tags { "RenderPipeline" = "HDRenderPipeline" "RenderType" = "Transparent" "Queue" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Name "XmasGlowCard"
            Tags { "LightMode" = "SRPDefaultUnlit" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"
            #include "Packages/com.unity.render-pipelines.high-definition/Runtime/ShaderLibrary/ShaderVariables.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _Gain, _CoreGain, _HaloGain, _CoreSigma, _RadiusM, _MinPx;
                float4 _NearFade;
            CBUFFER_END

            struct Attributes { float3 positionOS : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                float3 c = TransformObjectToWorld(v.positionOS);           // camera-relative world position (the camera at the origin)
                float dist = max(length(c), 1e-3);
                float pxWorld = dist * 2.0 / (UNITY_MATRIX_P[1][1] * _ScreenSize.y);
                float r = max(_RadiusM, _MinPx * pxWorld);
                float3 right = UNITY_MATRIX_V[0].xyz, up = UNITY_MATRIX_V[1].xyz;
                float3 p = c - (c / dist) * min(r, 0.5 * dist) + (right * v.uv.x + up * v.uv.y) * r;
                o.positionCS = TransformWorldToHClip(p);
                o.uv = v.uv;
                o.color = v.color;
                o.color.a *= smoothstep(_NearFade.x, _NearFade.y, dist);   // up close the bulb mesh is resolved and bloom does the halo
                return o;
            }

            float4 Frag(Varyings i) : SV_Target
            {
                float d2 = dot(i.uv, i.uv);
                float core = exp(-d2 / (_CoreSigma * _CoreSigma));
                float edge = saturate(1.0 - sqrt(d2));
                float halo = edge * edge / (1.0 + 8.0 * d2);
                float I = (_CoreGain * core + _HaloGain * halo) * i.color.a * _Gain;
                return float4(i.color.rgb * I, 0.0);
            }
            ENDHLSL
        }
    }
}
