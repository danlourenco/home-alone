using UnityEngine;

// The split (DEVIATIONS 1, 97): the exterior is the film's house on the measured ground floor; Marina's upstairs is bigger and stands
// outside it. While the camera is upstairs (above switchY and over an upstairs room) the upstairs and attic are drawn whole and the
// skin's upper storey and roofs are hidden; everywhere else (outside, ground floor) the skin is drawn and the upstairs pieces that
// reach outside it are hidden. Renderers only: colliders never change. Play mode follows Camera.main; in the editor everything stays
// drawn (the bake and the gates see the whole house) except around a batch render (SpecGreybox.RenderViews: ApplyFor / RestoreAll).
public class HouseSplit : MonoBehaviour
{
    public Renderer[] skinUpper = new Renderer[0];   // the skin's upper storey, main roofs, dormers, chimney, portico
    public Renderer[] insideOnly = new Renderer[0];  // upstairs/attic pieces reaching outside the skin
    public float switchY;
    public Vector2[] rooms = new Vector2[0];         // upstairs room outlines (world x, z), concatenated
    public int[] roomStarts = new int[0];
    int state = -1;

    public bool Upstairs(Vector3 p)
    {
        if (p.y <= switchY) return false;
        var q = new Vector2(p.x, p.z);
        for (int r = 0; r < roomStarts.Length; r++)
        {
            int a = roomStarts[r], b = r + 1 < roomStarts.Length ? roomStarts[r + 1] : rooms.Length;
            bool c = false;
            for (int i = a, j = b - 1; i < b; j = i++)
                if ((rooms[i].y > q.y) != (rooms[j].y > q.y) && q.x < (rooms[j].x - rooms[i].x) * (q.y - rooms[i].y) / (rooms[j].y - rooms[i].y) + rooms[i].x) c = !c;
            if (c) return true;
        }
        return false;
    }

    void Set(int s)
    {
        state = s;
        foreach (var r in skinUpper) if (r) r.enabled = s != 1;
        foreach (var r in insideOnly) if (r) r.enabled = s != 0;
    }

    public void ApplyFor(Vector3 p) => Set(Upstairs(p) ? 1 : 0);
    public void RestoreAll() => Set(-1);

    void LateUpdate()
    {
        if (!Application.isPlaying) return;
        var cam = Camera.main; if (cam == null) return;
        int s = Upstairs(cam.transform.position) ? 1 : 0;
        if (s == state) return;
        Set(s);
        ShadowRefresh.Forget();   // lamp shadow maps drawn with the other set hidden are redrawn when next in view
    }
}
