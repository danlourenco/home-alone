using UnityEngine;

// Seated TV view; E returns to the clear approach position. Does not alter the chair.
public class DenSeat : MonoBehaviour
{
    public Renderer screen;
    public Vector3 eyePosition;
    public float fieldOfView = 36f, reach = 1.6f;
    public bool Seated => seated;
    FpsController player; CharacterController cc; Camera view;
    Vector3 returnPosition, cameraPosition;
    Quaternion returnRotation, cameraRotation;
    float previousFov;
    bool seated, aimed, previousFrozen, previousEnabled;
    void Update()
    {
        if (!player) player=FindFirstObjectByType<FpsController>();
        if (!player || !screen) return;
        if (seated) {
            if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Tab)) { Cursor.lockState=CursorLockMode.None; Cursor.visible=true; }
            if (Input.GetMouseButtonDown(0)) { Cursor.lockState=CursorLockMode.Locked; Cursor.visible=false; }
        }
        var to = transform.position + Vector3.up*.5f - player.cam.position;
        aimed = !seated && !player.frozen && to.magnitude < reach && Vector3.Angle(player.cam.forward,to)<40f;
        if (Cursor.lockState == CursorLockMode.Locked && Input.GetKeyDown(KeyCode.E))
        { if (seated) Stand(); else if (aimed) Sit(); }
    }
    public bool Sit()
    {
        if (seated || !screen) return false;
        if (!player) player=FindFirstObjectByType<FpsController>();
        if (!player || player.frozen) return false;
        cc=player.GetComponent<CharacterController>();view=player.cam.GetComponent<Camera>();
        returnPosition=player.transform.position;returnRotation=player.transform.rotation;
        cameraPosition=player.cam.localPosition;cameraRotation=player.cam.localRotation;previousFov=view.fieldOfView;
        previousFrozen=player.frozen;previousEnabled=player.enabled;
        cc.enabled=false;player.frozen=true;player.enabled=false;seated=true;
        var eye=eyePosition+Vector3.up*(player.kid?0f:.17f);
        player.cam.position=eye;player.cam.rotation=Quaternion.LookRotation(screen.bounds.center-eye);
        view.fieldOfView=fieldOfView;
        return true;
    }
    public bool Stand()
    {
        if (!seated) return false;
        // Other bodies may have entered the return spot while we watched.
        float r=cc.radius;var bottom=returnPosition+cc.center-Vector3.up*(cc.height/2-r);
        var top=returnPosition+cc.center+Vector3.up*(cc.height/2-r);
        if (Physics.CheckCapsule(bottom+Vector3.up*.04f,top,r*.94f,~0,QueryTriggerInteraction.Ignore)) return false;
        Restore();return true;
    }
    void Restore()
    {
        if (!player) return;
        player.transform.SetPositionAndRotation(returnPosition,returnRotation);
        player.cam.localPosition=cameraPosition;player.cam.localRotation=cameraRotation;
        view.fieldOfView=previousFov;player.frozen=previousFrozen;player.enabled=previousEnabled;cc.enabled=true;seated=false;
    }
    void OnDisable() { if(seated) Restore(); }
    void OnGUI()
    {
        if (!aimed && !seated) return;
        var style=new GUIStyle(GUI.skin.label){fontSize=18,alignment=TextAnchor.MiddleCenter};
        GUI.Label(new Rect(0,Screen.height*.62f,Screen.width,30),seated?"E: stand up   •   V: TV on/off":"E: sit and watch TV",style);
    }
}
