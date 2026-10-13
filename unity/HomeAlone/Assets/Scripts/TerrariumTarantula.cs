using UnityEngine;

public class TerrariumTarantula : MonoBehaviour
{
    public Transform[] legs;
    public void Pose(float seconds)
    {
        // Small, slow patrol inside the tank; independent object for a later pickup mechanic.
        float phase=seconds*.22f;
        transform.localPosition=new Vector3(.20f*Mathf.Sin(phase),0,.06f*Mathf.Sin(phase*2));
        transform.localRotation=Quaternion.Euler(0,Mathf.Atan2(.20f*Mathf.Cos(phase),.12f*Mathf.Cos(phase*2))*Mathf.Rad2Deg,0);
        for(int i=0;i<legs.Length;i++){
            float stride=Mathf.Sin(seconds*4f+(i%2)*Mathf.PI);
            legs[i].localRotation=Quaternion.Euler(0,stride*9f,(i<4?1:-1)*Mathf.Max(0,stride)*7f);
        }
    }
    void Update(){Pose(Time.time);}
}
