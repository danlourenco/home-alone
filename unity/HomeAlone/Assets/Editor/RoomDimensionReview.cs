using System;
using System.Linq;
using System.Text;
using UnityEngine;

public static partial class SurveyBuilder
{
    public static string ReviewRoomDimensions()
    {
        var buzz=GameObject.Find("BuzzBedroomDetails");var bath=GameObject.Find("ParentsEnsuiteDetails");
        if(!buzz||!bath)throw new InvalidOperationException("Furnished rooms missing.");
        var b=new StringBuilder("Unity world metres; source-film scale remains unverified.\n");
        foreach(var s in new[]{(buzz,"Buzz wooden bed"),(buzz,"Window chest of drawers"),(bath,"Rounded bath - provisional fit"),(bath,"Brass framed shower - open entrance")}){
            var node=s.Item1.transform.Find(s.Item2);var rs=node.GetComponentsInChildren<Renderer>();var bounds=rs[0].bounds;foreach(var r in rs.Skip(1))bounds.Encapsulate(r.bounds);
            b.AppendLine(s.Item2+": bounds "+bounds.min.ToString("F3")+" .. "+bounds.max.ToString("F3")+"; size "+bounds.size.ToString("F3"));
        }
        var bed=buzz.transform.Find("Buzz wooden bed").GetComponentsInChildren<Renderer>();
        var chest=buzz.transform.Find("Window chest of drawers").GetComponentsInChildren<Renderer>();
        b.AppendLine("Bed-to-chest projected clearance including posts/handles: "+(bed.Min(r=>r.bounds.min.z)-chest.Max(r=>r.bounds.max.z)).ToString("F3"));
        b.AppendLine("Mattress world size: "+bed.Single(r=>r.name=="Mattress").bounds.size.ToString("F3"));
        b.AppendLine("Bath bowl rim inner ellipse: 0.980 x 1.049 m; bowl floor approx 0.640 x 0.685 m, from profile radii and local scale.");
        b.AppendLine("Shower tray: "+bath.GetComponentsInChildren<Renderer>().Single(r=>r.name=="Shower tray").bounds.size.ToString("F3"));
        b.AppendLine("No movie-room error percentage can be derived from these model measurements alone.");
        return b.ToString();
    }
}
