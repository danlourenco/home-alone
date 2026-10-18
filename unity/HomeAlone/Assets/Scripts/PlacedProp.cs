using UnityEngine;

// Marks a prop placed from a spec file, with the turn it was built at, so Home Alone > Save Prop Placement
// (Editor/SavePropPlacement.cs) can write a hand move or turn back to the spec.
public class PlacedProp : MonoBehaviour
{
    public string spec;          // "store_props" or "trunk"
    public float yaw;            // the yaw it was built at (degrees, Unity)
    public Quaternion rot0;      // its first renderer's world rotation as built: a turn of the root or of a child shows against it
    public string src;           // its store_props.json entry as placed: Home Alone > Refresh Props re-places it when the entry changes
    public Vector3 c0;           // the centre of what was drawn, as built: a move shows against it (an open door or a fit tolerance does not)
}
