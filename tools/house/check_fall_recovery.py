#!/usr/bin/env python3
"""Re-runnable controller fall regression in an isolated temporary additive scene.
Uses the connected, stopped main editor; closes the test scene and restores cursor.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CODE = r'''
if(UnityEditor.EditorApplication.isPlaying) throw new System.InvalidOperationException("Stop Play before running the isolated fall check");
var original=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var scene=UnityEditor.SceneManagement.EditorSceneManager.NewScene(UnityEditor.SceneManagement.NewSceneSetup.EmptyScene,UnityEditor.SceneManagement.NewSceneMode.Additive);
var cursor=UnityEngine.Cursor.lockState;var visible=UnityEngine.Cursor.visible;var results="";
try {
 UnityEngine.SceneManagement.SceneManager.SetActiveScene(scene);
 var floor=UnityEngine.GameObject.CreatePrimitive(UnityEngine.PrimitiveType.Cube);
 floor.transform.position=new UnityEngine.Vector3(2000,-.5f,2000);floor.transform.localScale=new UnityEngine.Vector3(6,1,6);
 foreach(bool kid in new[]{true,false}) {
  var go=new UnityEngine.GameObject("FallCheckPlayer");var p=go.AddComponent<FpsController>();p.kid=kid;
  var eye=new UnityEngine.GameObject("FallCheckEye");eye.transform.SetParent(go.transform,false);p.cam=eye.transform;
  go.transform.position=new UnityEngine.Vector3(2000,.05f,2000);p.SendMessage("Start");
  var cc=go.GetComponent<UnityEngine.CharacterController>();UnityEngine.Physics.SyncTransforms();
  for(int i=0;i<80;i++)p.TickMotion(UnityEngine.Vector3.zero,false,false,1f/60);
  // A second supported location distinguishes last-grounded recovery from spawn reset.
  cc.enabled=false;go.transform.position=new UnityEngine.Vector3(2001,.05f,2000);cc.enabled=true;UnityEngine.Physics.SyncTransforms();
  for(int i=0;i<80;i++)p.TickMotion(UnityEngine.Vector3.zero,false,false,1f/60);
  // A centre still over the ledge has an unsupported footprint; do not remember it.
  cc.enabled=false;go.transform.position=new UnityEngine.Vector3(2002.95f,.05f,2000);cc.enabled=true;UnityEngine.Physics.SyncTransforms();
  for(int i=0;i<30;i++)p.TickMotion(UnityEngine.Vector3.zero,false,false,1f/60);
  cc.enabled=false;go.transform.position=new UnityEngine.Vector3(2008,-40.836f,2000);cc.enabled=true;
  bool recovered=p.RecoverIfFallen();
  if(!recovered||UnityEngine.Mathf.Abs(go.transform.position.x-2001)>.1f||go.transform.position.y<0||!cc.enabled)
   throw new System.Exception("FAIL last-supported/ledge recovery "+kid+" at "+go.transform.position);
  var velocity=typeof(FpsController).GetField("vy",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance);
  if((float)velocity.GetValue(p)!=0)throw new System.Exception("FAIL falling velocity retained");
  // Let gravity actually drop the controller over unsupported ground; TickMotion must recover automatically.
  cc.enabled=false;go.transform.position=new UnityEngine.Vector3(2008,.05f,2000);cc.enabled=true;
  for(int i=0;i<180;i++)p.TickMotion(UnityEngine.Vector3.zero,false,false,1f/60);
  if(UnityEngine.Mathf.Abs(go.transform.position.x-2001)>.1f||go.transform.position.y<0)throw new System.Exception("FAIL automatic recovery");
  cc.enabled=false;go.transform.position=new UnityEngine.Vector3(2001,-6.5f,2000);cc.enabled=true;
  if(p.RecoverIfFallen())throw new System.Exception("FAIL legitimate basement height recovered");
  results+=(kid?"kid":"adult")+": last-supported, ledge rejection, automatic fall, velocity reset, basement all pass; ";
  UnityEngine.Object.DestroyImmediate(go);
 }
 // Regression region surrounding the reported fall. Ground-fill collision must cover every sample.
 int missing=0;
 for(float x=7.5f;x<=12.5f;x+=.5f)for(float z=4f;z<=9f;z+=.5f)
  if(!System.Linq.Enumerable.Any(UnityEngine.Physics.RaycastAll(new UnityEngine.Vector3(x,-2,z),UnityEngine.Vector3.down,5f,~0,UnityEngine.QueryTriggerInteraction.Ignore),h=>h.normal.y>.5f))missing++;
 if(missing!=0)throw new System.Exception("FAIL exterior ground coverage: "+missing+"/121 missing");
 foreach(bool kid in new[]{true,false}) {
  var go=new UnityEngine.GameObject("GroundCoveragePlayer");var p=go.AddComponent<FpsController>();p.kid=kid;p.fallRecoveryY=-1000;
  var eye=new UnityEngine.GameObject("GroundCoverageEye");eye.transform.SetParent(go.transform,false);p.cam=eye.transform;
  go.transform.position=new UnityEngine.Vector3(9.5f,-2,7.5f);p.SendMessage("Start");UnityEngine.Physics.SyncTransforms();
  for(int i=0;i<240;i++)p.TickMotion(UnityEngine.Vector3.zero,false,false,1f/60);
  if(go.transform.position.y < -7 || !go.GetComponent<UnityEngine.CharacterController>().isGrounded)
   throw new System.Exception("FAIL actual ground support, recovery disabled: "+kid+" at "+go.transform.position);
  UnityEngine.Object.DestroyImmediate(go);
 }
 results+="exterior coverage121/121; actual kid/adult support with recovery disabled pass";
 return "PASS fall recovery: "+results;
} finally {
 UnityEngine.SceneManagement.SceneManager.SetActiveScene(original);
 UnityEditor.SceneManagement.EditorSceneManager.CloseScene(scene,true);
 UnityEngine.Cursor.lockState=cursor;UnityEngine.Cursor.visible=visible;
}
'''
run = subprocess.run([str(Path.home()/'.unity/bin/unity'),'command','eval','--code',CODE,
    '--caller','plugin','--skill','unity-cli','--project-path',str(ROOT/'unity/HomeAlone')],capture_output=True,text=True)
for line in run.stdout.splitlines():
    cols=line.split('\t')
    if len(cols)>2 and cols[0]=='eval':
        result=json.loads(cols[2]); value=result.get('result','')
        if result.get('success') and isinstance(value,str) and value.startswith('PASS fall recovery:'):
            print(value);raise SystemExit(0)
        print(result);raise SystemExit(1)
print(run.stdout,run.stderr);raise SystemExit(1)
