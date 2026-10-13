using UnityEngine;

/// Shared constants for the survey-driven house. Survey frame: X east, Y toward rear, metres,
/// origin at the ground floor's front-left outer corner. Unity: X = X, Z = Y, Y up.
public static class SurveyHouse
{
    public const float WallThickness = 0.16f;
    public const float GroundCeiling = 2.75f;   // survey estimate 2.6-2.9 m
    public const float FloorStructure = 0.25f;  // slab between storeys
    public const float UpperCeiling = 2.6f;     // unmeasured; authored
    public const float AtticCeiling = 2.4f;     // ridge, authored
    public const float DoorHead = 2.1f;
    public const float WindowSill = 0.9f;

    // Spawn in the vestibule, facing the rear of the house.
    public static readonly Vector3 Spawn = new Vector3(11.2f, 0.05f, 0.9f);

    // Stacking decision (2026-09-11): upper floor mirrored in X so the hall lands over the foyer
    // stair, X scaled to the ground-floor main block (13.02 m -> 14.44 m), Y compressed so the
    // rear wall lands on the kitchen's rear wall line (16.74 m).
    public const float UpperMirrorWidth = 13.02f;
    public const float UpperX0 = 4.10f, UpperXScale = 14.44f / 13.02f;
    public const float UpperY0 = 0.36f, UpperYIn0 = 0.28f, UpperYScale = (16.74f - 0.36f) / (18.90f - 0.28f);

    public static Vector2 UpperToGround(float xu, float yu)
    {
        float xm = UpperMirrorWidth - xu;
        return new Vector2(UpperX0 + xm * UpperXScale, UpperY0 + (yu - UpperYIn0) * UpperYScale);
    }
}
