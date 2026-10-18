using System.Reflection;
using UnityEditor;
using UnityEngine;

// HDRP treats exposure as Fixed while any Scene-view search filter is on (HDRenderPipeline.IsExposureFixed: lastActiveSceneView.isUsingSceneFiltering);
// with our Automatic exposure it then falls back to the physical camera (f/16, 1/200, ISO 200 = EV 14.6) and the walk goes near black,
// night worst (user Oct 17 "why are all the lights off at night?": a Hierarchy search for "piano" did it). In Play and in edit mode (user: "when i click on an item in the hierachy the lighting is lost") we turn the Scene-view
// search filtering off (its own filter and the Hierarchy's forcing of it); the Hierarchy keeps its search. Proven by `unity_pipeline.sh nightcheck`.
[InitializeOnLoad]
static class SceneFilterExposureGuard
{
    static readonly MethodInfo SetFilter = typeof(SceneView).GetMethod("SetSearchFilter", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
    static readonly MethodInfo ForSearch = typeof(SceneView).GetMethod("SetSceneViewFilteringForSearch", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
    static readonly FieldInfo Filter = typeof(SearchableEditorWindow).GetField("m_SearchFilter", BindingFlags.Instance | BindingFlags.NonPublic);
    static readonly FieldInfo Forced = typeof(SceneView).GetField("m_ForceSceneViewFilteringForSearch", BindingFlags.Instance | BindingFlags.NonPublic);
    static SceneFilterExposureGuard() { EditorApplication.update += Check; }
    static void Check()
    {
        foreach (SceneView sv in SceneView.sceneViews)
            // search only (the Scene view's own filter, or the Hierarchy's search forcing it), not LOD/prefab-stage filtering
            if (sv && sv.isUsingSceneFiltering && (!string.IsNullOrEmpty(Filter?.GetValue(sv) as string) || Forced?.GetValue(sv) is true))
            {
                SetFilter?.Invoke(sv, new object[] { "", SearchableEditorWindow.SearchMode.All, false, false });
                ForSearch?.Invoke(sv, new object[] { false });
                if (EditorApplication.isPlaying) Debug.LogWarning("Scene-view search filter cleared: HDRP forces fixed exposure while it is on (the walk goes dark). The Hierarchy search is kept.");
            }
    }
}
