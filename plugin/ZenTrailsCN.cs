using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using UnityEngine;
using TMPro;

namespace ZenTrailsCN
{
    // Small UI touch-up shipped with the Chinese patch.
    //
    // In the segment info bubble's "更多" view the three row labels (thickness,
    // glow, layer order) were laid out around the width of the original English
    // words. With Chinese labels the rows come out ragged: "辉光" is indented by
    // about one label width and the layer-order value box sits one column to the
    // right of the other two.
    //
    // This makes all three value boxes share one column and every label end flush
    // against it - what the rows look like in the English original.
    //
    //   * value boxes - step the box (with its +/-/? buttons) into one column
    //   * label texts - TMP's left margin moves only the rendered glyphs, so the
    //                   box stays put; the margin -> pixel ratio is measured per
    //                   label rather than assumed
    //
    // Everything is measured in the panel's own coordinate space (walking
    // localPosition/localScale up the hierarchy), so the panel can be patched
    // while it is still collapsed at scale 0, before its first appearance.
    // The layer-order label is a special case: it is authored with a huge left
    // margin, so shifting it has to come with an equal negative right margin,
    // otherwise its text area shrinks and the label wraps onto two lines.
    [BepInPlugin("zentrails.cn.ui", "Zen Trails Chinese UI", "1.1.0")]
    public class ZenCNPlugin : BaseUnityPlugin
    {
        private static readonly string[] Rows = { "LineThickness", "Glow", "LayerOrder" };
        private const float Gap = 6f;                    // space between a label's right edge and the box column
        private const float Eps = 0.4f;                  // panel units, below this nothing is touched
        private const float LayerOrderMarginX = -270f;   // calibrated for this build
        private const float LayerOrderMarginZ = -262f;   // keeps the text area wide enough for one line

        private readonly List<RectTransform> known = new List<RectTransform>();
        private readonly Dictionary<int, string> sigs = new Dictionary<int, string>();
        private readonly Dictionary<int, float> shown = new Dictionary<int, float>();
        private readonly HashSet<int> crossChecked = new HashSet<int>();
        private string logPath;
        private int frame;
        private bool warned;

        private void Awake()
        {
            logPath = Path.Combine(Paths.GameRootPath, "BepInEx", "zen_cn.log");
            try
            {
                File.WriteAllText(logPath, "=== ZenTrailsCN UI " + DateTime.Now.ToString("HH:mm:ss") + " ===\r\n",
                    new UTF8Encoding(false));
            }
            catch (Exception) { }
        }

        private void Log(string s)
        {
            try { File.AppendAllText(logPath, s + "\r\n", new UTF8Encoding(false)); }
            catch (Exception) { }
        }

        private void Update()
        {
            frame++;
            try { Tick(); }
            catch (Exception e)
            {
                if (!warned)
                {
                    warned = true;
                    Log("ERR " + e.GetType().Name + ": " + e.Message);
                }
            }
        }

        private void Tick()
        {
            // right after start keep looking often, later only now and then
            int period = frame < 600 ? 15 : 180;
            if (frame % period == 0) Scan();

            for (int i = known.Count - 1; i >= 0; i--)
            {
                var p = known[i];
                if (p == null) { known.RemoveAt(i); continue; }
                Check(p);
            }
        }

        private void Scan()
        {
            foreach (var rt in Resources.FindObjectsOfTypeAll<RectTransform>())
            {
                if (rt == null || rt.name != "AestheticsPanel") continue;
                if (FindChild(rt, Rows[0]) == null || FindChild(rt, Rows[1]) == null || FindChild(rt, Rows[2]) == null) continue;
                bool have = false;
                foreach (var k in known) if (k == rt) { have = true; break; }
                if (have) continue;
                known.Add(rt);
                sigs[rt.GetInstanceID()] = "";
                Log("panel found (" + (rt.gameObject.activeInHierarchy ? "active" : "inactive")
                    + ", scale " + rt.localScale.x.ToString("F3") + ")");
            }
        }

        // Patch when the panel's content changed, and re-verify once when a
        // collapsed panel starts to open. Both are cheap no-ops once settled.
        private void Check(RectTransform panel)
        {
            int id = panel.GetInstanceID();
            string sig;
            if (!sigs.TryGetValue(id, out sig)) { sig = ""; sigs[id] = ""; }

            float scale = panel.localScale.x;
            float prev;
            if (!shown.TryGetValue(id, out prev)) prev = -1f;
            shown[id] = scale;
            bool justOpened = scale > 0.02f && prev >= 0f && prev <= 0.02f;

            string now = Signature(panel);
            if (now == sig && !justOpened) return;
            sigs[id] = now;

            Patch(panel, !crossChecked.Contains(id));
            crossChecked.Add(id);
        }

        private static string Signature(RectTransform panel)
        {
            var sb = new StringBuilder();
            sb.Append(panel.rect.width).Append('x').Append(panel.rect.height);
            foreach (var n in Rows)
            {
                var row = FindChild(panel, n);
                var tmp = row == null ? null : row.GetComponent<TextMeshProUGUI>();
                sb.Append('|').Append(tmp == null ? "-" : tmp.text);
            }
            return sb.ToString();
        }

        private static Transform FindChild(Transform root, string name)
        {
            if (root == null) return null;
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
                if (t != null && t.name == name) return t;
            return null;
        }

        // x of a point given in `t`'s local space, expressed in the panel's space.
        // Walks up with localPosition/localScale, so it works at any panel scale
        // (including the collapsed scale 0) and never divides by zero.
        private static float PanelX(RectTransform panel, Transform t, float localX)
        {
            float x = localX;
            var cur = t;
            int guard = 0;
            while (cur != null && cur != panel && guard++ < 32)
            {
                x = cur.localPosition.x + x * cur.localScale.x;
                cur = cur.parent;
            }
            return x;
        }

        private static bool CharSpan(TextMeshProUGUI t, RectTransform panel, out float left, out float right)
        {
            left = right = 0f;
            if (t == null) return false;
            if (string.IsNullOrEmpty(t.text) || t.text.Trim().Length == 0) return false;
            t.ForceMeshUpdate();
            var ti = t.textInfo;
            if (ti == null || ti.characterCount == 0) return false;

            float lx = float.MaxValue, rx = float.MinValue;
            for (int i = 0; i < ti.characterCount; i++)
            {
                var ci = ti.characterInfo[i];
                if (!ci.isVisible) continue;
                float a = PanelX(panel, t.transform, ci.bottomLeft.x);
                float b = PanelX(panel, t.transform, ci.topRight.x);
                if (a > b) { float tmp = a; a = b; b = tmp; }
                if (a < lx) lx = a;
                if (b > rx) rx = b;
            }
            if (rx <= lx) return false;
            left = lx;
            right = rx;
            return true;
        }

        private static bool BoxLeft(RectTransform box, RectTransform panel, out float x)
        {
            x = 0f;
            if (box == null || box.rect.width == 0f) return false;
            float a = PanelX(panel, box, box.rect.xMin);
            float b = PanelX(panel, box, box.rect.xMax);
            x = Mathf.Min(a, b);
            return true;
        }

        // several passes in one frame, so the user never sees an intermediate state
        private void Patch(RectTransform panel, bool verify)
        {
            for (int it = 0; it < 6; it++)
                if (!AlignOnce(panel, it, verify && it == 0)) break;
        }

        private bool AlignOnce(RectTransform panel, int pass, bool log)
        {
            var labels = new TextMeshProUGUI[3];
            var boxes = new RectTransform[3];
            for (int i = 0; i < 3; i++)
            {
                var row = FindChild(panel, Rows[i]);
                if (row == null) return false;
                labels[i] = row.GetComponent<TextMeshProUGUI>();
                if (labels[i] == null) return false;
                boxes[i] = FindChild(row, "InputField (TMP)") as RectTransform;
                if (boxes[i] == null) return false;
            }

            bool changed = false;
            var bl = new float[3];
            for (int i = 0; i < 3; i++)
                if (!BoxLeft(boxes[i], panel, out bl[i])) return false;
            float common = Mathf.Min(bl[0], Mathf.Min(bl[1], bl[2]));

            // 1) one column for the three value boxes
            for (int i = 0; i < 3; i++)
            {
                float d = common - bl[i];
                if (Mathf.Abs(d) < Eps) continue;
                float sc = labels[i].transform.localScale.x;
                if (Mathf.Abs(sc) < 0.01f) continue;
                foreach (Transform ch in labels[i].transform)
                {
                    var crt = ch as RectTransform;
                    if (crt == null) continue;
                    crt.anchoredPosition = new Vector2(crt.anchoredPosition.x + d / sc, crt.anchoredPosition.y);
                }
                changed = true;
                if (log) Log("p" + pass + "  box " + Rows[i] + " step " + d.ToString("F2"));
            }

            // 2) layer order: fixed calibrated margins
            var lo = labels[2];
            var lm = lo.margin;
            if (Mathf.Abs(lm.x - LayerOrderMarginX) > 0.01f || Mathf.Abs(lm.z - LayerOrderMarginZ) > 0.01f)
            {
                lo.margin = new Vector4(LayerOrderMarginX, lm.y, LayerOrderMarginZ, lm.w);
                lo.ForceMeshUpdate();
                changed = true;
                if (log) Log("p" + pass + "  LayerOrder margin set");
            }

            // 3) the other two labels end flush against the box column
            float targetRight = common - Gap;
            for (int i = 0; i < 2; i++)
            {
                float left, right;
                if (!CharSpan(labels[i], panel, out left, out right)) return changed;
                float need = targetRight - right;
                if (log)
                {
                    Log("p" + pass + "  " + Rows[i] + " glyphs " + left.ToString("F2") + ".." + right.ToString("F2")
                        + " need " + need.ToString("F2") + " (box " + bl[i].ToString("F2") + ")");
                    if (panel.lossyScale.x > 0.01f) CrossCheck(labels[i], panel, left, right);
                }
                if (Mathf.Abs(need) < 0.3f) continue;
                if (ShiftText(labels[i], panel, need, log)) changed = true;
            }
            return changed;
        }

        // one-off sanity comparison between the local-space walk used here and the
        // world-space conversion used while the panel was visible during development
        private void CrossCheck(TextMeshProUGUI t, RectTransform panel, float lleft, float lright)
        {
            try
            {
                var b = t.textBounds;
                float wl = panel.InverseTransformPoint(t.transform.TransformPoint(new Vector3(b.min.x, b.min.y, 0f))).x;
                float wr = panel.InverseTransformPoint(t.transform.TransformPoint(new Vector3(b.max.x, b.max.y, 0f))).x;
                if (wl > wr) { float tmp = wl; wl = wr; wr = tmp; }
                Log("  check " + t.gameObject.name + " local " + lleft.ToString("F2") + ".." + lright.ToString("F2")
                    + " worldBounds " + wl.ToString("F2") + ".." + wr.ToString("F2"));
            }
            catch (Exception) { }
        }

        // moves only the rendered glyphs; the row's box and buttons stay where they are
        private bool ShiftText(TextMeshProUGUI t, RectTransform panel, float need, bool log)
        {
            var m0 = t.margin;
            float l0, r0;
            if (!CharSpan(t, panel, out l0, out r0)) return false;

            t.margin = new Vector4(m0.x + 100f, m0.y, m0.z - 100f, m0.w);
            t.ForceMeshUpdate();
            float l1, r1;
            if (!CharSpan(t, panel, out l1, out r1)) { t.margin = m0; return false; }
            float k = (r1 - r0) / 100f;

            if (Mathf.Abs(k) < 0.02f)
            {
                t.margin = m0;
                if (log) Log("  margin ineffective on " + t.gameObject.name + " k=" + k.ToString("F4"));
                return false;
            }

            float d = need / k;
            t.margin = new Vector4(m0.x + d, m0.y, m0.z - d, m0.w);
            t.ForceMeshUpdate();
            float l2, r2;
            CharSpan(t, panel, out l2, out r2);
            if (log)
                Log("  " + t.gameObject.name + " margin " + m0.x.ToString("F1") + "->" + (m0.x + d).ToString("F1")
                    + " k=" + k.ToString("F4") + " right " + r0.ToString("F2") + "->" + r2.ToString("F2"));
            return true;
        }
    }
}
