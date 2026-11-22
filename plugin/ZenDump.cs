using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using BepInEx;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using TMPro;

namespace ZenDump
{
    [BepInPlugin("zen.dump", "ZenDump", "1.1")]
    public class ZenDumpPlugin : BaseUnityPlugin
    {
        private string outPath;
        private string diagPath;
        private string reqPath;
        private string clickLog;

        private void Awake()
        {
            string b = Path.Combine(Paths.GameRootPath, "BepInEx");
            outPath = Path.Combine(b, "dump_texts.txt");
            diagPath = Path.Combine(b, "diag.txt");
            reqPath = Path.Combine(b, "click_req.txt");
            clickLog = Path.Combine(b, "click_log.txt");
            Logger.LogInfo("ZenDump ready -> " + outPath);
        }

        private void Update()
        {
            try
            {
                if (Input.GetKeyDown(KeyCode.F9)) { Dump(); }
                if (Input.GetKeyDown(KeyCode.F10)) { Diag(); }
                if (Input.GetKeyDown(KeyCode.F11)) { DoRequests(); }
            }
            catch (Exception e) { Logger.LogError("ZenDump: " + e); }
        }

        private static string PathOf(Transform t)
        {
            var sb = new StringBuilder(t.name);
            var p = t.parent;
            int guard = 0;
            while (p != null && guard++ < 64) { sb.Insert(0, p.name + "/"); p = p.parent; }
            return sb.ToString();
        }

        private static string Esc(string s)
        {
            return s.Replace("\r", "\\r").Replace("\n", "\\n");
        }

        private void Write(string path, string text)
        {
            File.WriteAllText(path, text, new UTF8Encoding(false));
        }

        // ---------- F9: dump every text ----------
        private void Dump()
        {
            var sb = new StringBuilder();
            sb.AppendLine("=== DUMP " + DateTime.Now.ToString("HH:mm:ss") + " ===");

            var tmps = Resources.FindObjectsOfTypeAll<TextMeshProUGUI>();
            int n1 = 0;
            sb.AppendLine("-- TMP --");
            foreach (var t in tmps)
            {
                if (t == null) continue;
                var txt = t.text;
                if (string.IsNullOrEmpty(txt)) continue;
                n1++;
                sb.Append(PathOf(t.transform)).Append("\t")
                  .Append(t.gameObject.activeInHierarchy ? "A" : "H").Append("\t")
                  .Append(Esc(txt)).AppendLine();
            }
            sb.AppendLine("-- TMP COUNT " + n1 + " --");

            var leg = Resources.FindObjectsOfTypeAll<Text>();
            int n2 = 0;
            sb.AppendLine("-- TEXT --");
            foreach (var t in leg)
            {
                if (t == null) continue;
                var txt = t.text;
                if (string.IsNullOrEmpty(txt)) continue;
                n2++;
                sb.Append(PathOf(t.transform)).Append("\t")
                  .Append(t.gameObject.activeInHierarchy ? "A" : "H").Append("\t")
                  .Append(Esc(txt)).AppendLine();
            }
            sb.AppendLine("-- TEXT COUNT " + n2 + " --");

            Write(outPath, sb.ToString());
        }

        // ---------- F10: input diagnostics ----------
        private void Diag()
        {
            var sb = new StringBuilder();
            sb.AppendLine("time=" + DateTime.Now.ToString("HH:mm:ss.fff"));
            sb.AppendLine("isFocused=" + Application.isFocused);
            sb.AppendLine("isPlaying=" + Application.isPlaying);
            sb.AppendLine("screen=" + Screen.width + "x" + Screen.height + " full=" + Screen.fullScreen);
            sb.AppendLine("cursor.lockState=" + Cursor.lockState);
            sb.AppendLine("cursor.visible=" + Cursor.visible);
            sb.AppendLine("mousePosition=" + Input.mousePosition.x + "," + Input.mousePosition.y);
            sb.AppendLine("mousePresent=" + Input.mousePresent);
            sb.AppendLine("getMouseButton=" + Input.GetMouseButton(0));
            sb.AppendLine("anyKey/MouseDelta=" + Input.GetAxis("Mouse X") + "," + Input.GetAxis("Mouse Y"));
            sb.AppendLine("touchCount=" + Input.touchCount);

            var es = EventSystem.current;
            sb.AppendLine("eventSystem=" + (es == null ? "null" : es.GetType().Name));
            if (es != null)
            {
                sb.AppendLine("pointerOverUI=" + es.IsPointerOverGameObject());
                var sel = es.currentSelectedGameObject;
                sb.AppendLine("selected=" + (sel == null ? "-" : PathOf(sel.transform)));
                var all = Resources.FindObjectsOfTypeAll<Selectable>();
                int hit = 0;
                string hitPath = "-";
                foreach (var s in all)
                {
                    if (s == null || !s.gameObject.activeInHierarchy) continue;
                    if (s.IsInteractable() && es.IsPointerOverGameObject() ) { }
                    hit++;
                }
                sb.AppendLine("selectablesActive=" + hit);
                sb.AppendLine("pointerHit=" + hitPath);
            }

            Write(diagPath, sb.ToString());
        }

        // ---------- F11: scripted UI actions ----------
        // Format of click_req.txt, one per line:
        //   click:<path substring>[:all]
        //   text:<path substring>|<value>        (sets InputField value + fires onValueChanged/onEndEdit)
        //   toggle:<path substring>              (toggles a Toggle / Button)
        // Lines starting with '#' or empty are skipped.
        private void DoRequests()
        {
            var log = new StringBuilder();
            log.AppendLine("=== " + DateTime.Now.ToString("HH:mm:ss.fff") + " ===");
            if (!File.Exists(reqPath)) { log.AppendLine("no click_req.txt"); Write(clickLog, log.ToString()); return; }
            var lines = File.ReadAllLines(reqPath, Encoding.UTF8);
            foreach (var raw in lines)
            {
                var line = raw == null ? "" : raw.Trim();
                if (line.Length == 0 || line.StartsWith("#")) continue;
                try
                {
                    if (line == "list")
                    {
                        List(log);
                    }
                    else if (line.StartsWith("props:"))
                    {
                        Props(line.Substring(6), log);
                    }
                    else if (line.StartsWith("types:"))
                    {
                        Types(line.Substring(6), log);
                    }
                    else if (line.StartsWith("call:"))
                    {
                        Call(line.Substring(5), log);
                    }
                    else if (line.StartsWith("freeze:"))
                    {
                        Freeze(line.Substring(7), log);
                    }
                    else if (line.StartsWith("show:"))
                    {
                        Show(line.Substring(5), log);
                    }
                    else if (line.StartsWith("select:"))
                    {
                        SelectSegment(line.Substring(7), log);
                    }
                    else if (line.StartsWith("find:"))
                    {
                        Find(line.Substring(5), log);
                    }
                    else if (line.StartsWith("callat:"))
                    {
                        // callat:<Type>:<Method>:<path substring>
                        var parts = line.Substring(7).Split(new char[] { ':' }, 3);
                        if (parts.Length < 3) { log.AppendLine("bad callat"); }
                        else CallAt(parts[0], parts[1], parts[2], log);
                    }
                    else if (line.StartsWith("align:"))
                    {
                        AlignLabels(line.Substring(6), log);
                    }
                    else if (line.StartsWith("click:"))
                    {
                        string arg = line.Substring(6);
                        bool all = arg.EndsWith(":all");
                        if (all) arg = arg.Substring(0, arg.Length - 4);
                        int n = Click(arg, all, log);
                        log.AppendLine("click '" + arg + "' -> " + n);
                    }
                    else if (line.StartsWith("click="))
                    {
                        int n = ClickExact(line.Substring(6), log);
                        log.AppendLine("click exact -> " + n);
                    }
                    else if (line.StartsWith("toggle:"))
                    {
                        int n = Toggle(line.Substring(7), log);
                        log.AppendLine("toggle -> " + n);
                    }
                    else if (line.StartsWith("text:"))
                    {
                        string arg = line.Substring(5);
                        int bar = arg.IndexOf('|');
                        string sub = bar < 0 ? arg : arg.Substring(0, bar);
                        string val = bar < 0 ? "" : arg.Substring(bar + 1);
                        int n = SetText(sub, val, log);
                        log.AppendLine("text '" + sub + "' -> " + n);
                    }
                    else log.AppendLine("?? " + line);
                }
                catch (Exception e) { log.AppendLine("ERR " + line + " : " + e.Message); }
            }
            Write(clickLog, log.ToString());
        }

        private class Cand
        {
            public Button b;
            public string path;
            public bool act;
        }

        // shortest path first: the intended button is normally the outermost match
        private int Click(string sub, bool all, StringBuilder log)
        {
            var cands = new List<Cand>();
            foreach (var b in Resources.FindObjectsOfTypeAll<Button>())
            {
                if (b == null) continue;
                string p = PathOf(b.transform);
                if (p.IndexOf(sub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                cands.Add(new Cand { b = b, path = p, act = b.gameObject.activeInHierarchy });
            }
            cands.Sort(delegate (Cand x, Cand y)
            {
                if (x.act != y.act) return x.act ? -1 : 1;
                return x.path.Length.CompareTo(y.path.Length);
            });
            int n = 0;
            foreach (var c in cands)
            {
                log.AppendLine("  hit[" + (c.act ? "A" : "H") + "] " + c.path);
                c.b.onClick.Invoke();
                n++;
                if (!all) break;
            }
            return n;
        }

        private int ClickExact(string path, StringBuilder log)
        {
            foreach (var b in Resources.FindObjectsOfTypeAll<Button>())
            {
                if (b == null) continue;
                string p = PathOf(b.transform);
                if (p != path) continue;
                log.AppendLine("  exact[" + (b.gameObject.activeInHierarchy ? "A" : "H") + "] " + p);
                b.onClick.Invoke();
                return 1;
            }
            log.AppendLine("  exact miss: " + path);
            return 0;
        }

        private void Props(string sub, StringBuilder log)
        {
            var tmps = Resources.FindObjectsOfTypeAll<TextMeshProUGUI>();
            foreach (var t in tmps)
            {
                if (t == null) continue;
                string p = PathOf(t.transform);
                if (p.IndexOf(sub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                var rt = t.rectTransform;
                log.AppendLine("TMP " + p);
                log.AppendLine("  text=" + Esc(t.text ?? ""));
                log.AppendLine("  align=" + t.alignment + " fontSize=" + t.fontSize
                    + " autoSize=" + t.enableAutoSizing + " min/max=" + t.fontSizeMin + "/" + t.fontSizeMax
                    + " charSpace=" + t.characterSpacing + " wordSpace=" + t.wordSpacing
                    + " overflow=" + t.overflowMode + " wrap=" + t.enableWordWrapping
                    + " margins=" + t.margin);
                log.AppendLine("  rect pos=" + rt.anchoredPosition + " size=" + rt.sizeDelta
                    + " pivot=" + rt.pivot + " anchorMin/Max=" + rt.anchorMin + "/" + rt.anchorMax
                    + " offsetMin/Max=" + rt.offsetMin + "/" + rt.offsetMax
                    + " worldRect=" + t.GetPixelAdjustedRect());
                log.AppendLine("  parent=" + (rt.parent == null ? "-" : rt.parent.name + " size=" + ((RectTransform)rt.parent).sizeDelta));
            }
            foreach (var t in Resources.FindObjectsOfTypeAll<Text>())
            {
                if (t == null) continue;
                string p = PathOf(t.transform);
                if (p.IndexOf(sub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                var rt = t.rectTransform;
                log.AppendLine("TXT " + p);
                log.AppendLine("  text=" + Esc(t.text ?? "") + " align=" + t.alignment + " fontSize=" + t.fontSize
                    + " bestFit=" + t.resizeTextForBestFit + " min/max=" + t.resizeTextMinSize + "/" + t.resizeTextMaxSize
                    + " hOverflow=" + t.horizontalOverflow + " vOverflow=" + t.verticalOverflow
                    + " lineSpacing=" + t.lineSpacing);
                log.AppendLine("  rect pos=" + rt.anchoredPosition + " size=" + rt.sizeDelta + " pivot=" + rt.pivot);
            }
        }

        private static Type FindType(string name)
        {
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts;
                try { ts = asm.GetTypes(); }
                catch (Exception) { continue; }
                foreach (var x in ts)
                {
                    if (x != null && (x.Name == name || x.FullName == name)) return x;
                }
            }
            return null;
        }

        private static Transform FindByPath(string pathSub)
        {
            Transform best = null;
            int bestLen = int.MaxValue;
            bool exact = pathSub.StartsWith("=");
            if (exact) pathSub = pathSub.Substring(1);
            foreach (var t in Resources.FindObjectsOfTypeAll<Transform>())
            {
                if (t == null || t.root == null) continue;
                string p = PathOf(t);
                bool hit = exact ? p == pathSub : p.IndexOf(pathSub, StringComparison.OrdinalIgnoreCase) >= 0;
                if (!hit) continue;
                if (p.Length < bestLen) { best = t; bestLen = p.Length; }
            }
            return best;
        }

        private void Freeze(string pathSub, StringBuilder log)
        {
            Show(pathSub, log);
            var t = FindByPath(pathSub);
            if (t == null) return;
            var rt = t as RectTransform;
            if (rt != null && rt.localScale.x < 0.5f)
            {
                rt.localScale = Vector3.one;
                log.AppendLine("  scale forced to 1");
            }
            foreach (var mb in t.GetComponentsInChildren<MonoBehaviour>(true))
            {
                if (mb == null) continue;
                if (mb.GetType().Name.IndexOf("InfoPanel", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    mb.enabled = false;
                    log.AppendLine("  disabled " + mb.GetType().Name + " on " + PathOf(mb.transform));
                }
            }
            if (rt != null && rt.localScale.x < 0.5f) { rt.localScale = Vector3.one; log.AppendLine("  scale forced after disable"); }
            foreach (var tmp in t.GetComponentsInChildren<TextMeshProUGUI>(true)) tmp.ForceMeshUpdate();
            log.AppendLine("  final scale=" + (rt == null ? "-" : rt.localScale.ToString()));
        }

        private void Show(string pathSub, StringBuilder log)
        {
            var t = FindByPath(pathSub);
            if (t == null) { log.AppendLine("no object matching " + pathSub); return; }
            log.AppendLine("found " + PathOf(t));
            var chain = new List<Transform>();
            for (var c = t; c != null; c = c.parent) chain.Add(c);
            for (int i = chain.Count - 1; i >= 0; i--)
            {
                if (!chain[i].gameObject.activeSelf)
                {
                    chain[i].gameObject.SetActive(true);
                    log.AppendLine("  activated " + PathOf(chain[i]));
                }
                var cg = chain[i].GetComponent<CanvasGroup>();
                if (cg != null && cg.alpha < 0.99f)
                {
                    cg.alpha = 1f;
                    log.AppendLine("  alpha=1 " + PathOf(chain[i]));
                }
            }
            foreach (var tmp in t.GetComponentsInChildren<TextMeshProUGUI>(true))
            {
                tmp.ForceMeshUpdate();
            }
            var rt = t as RectTransform;
            if (rt != null) log.AppendLine("  rect pos=" + rt.anchoredPosition + " size=" + rt.sizeDelta + " scale=" + rt.localScale);
        }

        private void SelectSegment(string pathSub, StringBuilder log)
        {
            var segType = FindType("Segment");
            var cdType = FindType("ClickAndDrag");
            if (segType == null) { log.AppendLine("no Segment type"); return; }
            if (cdType == null) { log.AppendLine("no ClickAndDrag type"); return; }
            UnityEngine.Object[] segs;
            try { segs = UnityEngine.Object.FindObjectsOfType(segType); }
            catch (Exception e) { log.AppendLine("FindObjectsOfType(Segment) failed: " + e.GetType().Name + " " + e.Message); return; }
            log.AppendLine("segments: " + segs.Length);
            object chosen = null;
            string chosenPath = null;
            foreach (var s in segs)
            {
                var c = s as Component;
                if (c == null) continue;
                string p = PathOf(c.transform);
                log.AppendLine("  seg " + p);
                if (chosen == null && (pathSub == "*" || p.IndexOf(pathSub, StringComparison.OrdinalIgnoreCase) >= 0))
                {
                    chosen = s;
                    chosenPath = p;
                }
            }
            if (chosen == null) { log.AppendLine("no segment matched " + pathSub); return; }
            var cd = UnityEngine.Object.FindObjectOfType(cdType);
            if (cd == null) { log.AppendLine("no ClickAndDrag instance"); return; }
            var m = cdType.GetMethod("ModifyBoxSelection", System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            if (m == null) { log.AppendLine("no ModifyBoxSelection"); return; }
            try
            {
                m.Invoke(cd, new object[] { chosen });
                log.AppendLine("ModifyBoxSelection(" + chosenPath + ") ok");
            }
            catch (Exception e) { log.AppendLine("ModifyBoxSelection err: " + e.GetType().Name + " " + e.Message); }
        }

        private void Find(string typeName, StringBuilder log)
        {
            Type t = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts;
                try { ts = asm.GetTypes(); }
                catch (Exception) { continue; }
                foreach (var x in ts)
                {
                    if (x != null && (x.Name == typeName || x.FullName == typeName)) { t = x; break; }
                }
                if (t != null) break;
            }
            if (t == null) { log.AppendLine("type not found " + typeName); return; }
            var objs = UnityEngine.Object.FindObjectsOfType(t);
            log.AppendLine("-- " + t.FullName + " instances: " + objs.Length + " --");
            foreach (var o in objs)
            {
                var c = o as Component;
                if (c == null) continue;
                log.AppendLine("  [" + (c.gameObject.activeInHierarchy ? "A" : "H") + "] " + PathOf(c.transform)
                    + (c is Behaviour ? (((Behaviour)c).enabled ? "" : " (disabled)") : ""));
            }
        }

        private void CallAt(string typeName, string methodName, string pathSub, StringBuilder log)
        {
            Type t = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts;
                try { ts = asm.GetTypes(); }
                catch (Exception) { continue; }
                foreach (var x in ts)
                {
                    if (x != null && (x.Name == typeName || x.FullName == typeName)) { t = x; break; }
                }
                if (t != null) break;
            }
            if (t == null) { log.AppendLine("type not found " + typeName); return; }
            foreach (var o in UnityEngine.Object.FindObjectsOfType(t))
            {
                var c = o as Component;
                if (c == null) continue;
                string p = PathOf(c.transform);
                if (p.IndexOf(pathSub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                var m = t.GetMethod(methodName, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic
                    | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static);
                if (m == null) { log.AppendLine("no method " + methodName); return; }
                try
                {
                    var res = m.Invoke(m.IsStatic ? null : (object)o, null);
                    log.AppendLine("called " + t.FullName + "." + methodName + " at " + p + " -> " + res);
                }
                catch (Exception e) { log.AppendLine("call err " + p + " : " + e.Message); }
                return;
            }
            log.AppendLine("no instance matching " + pathSub);
        }

        private void Types(string pattern, StringBuilder log)
        {
            int n = 0;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts;
                try { ts = asm.GetTypes(); }
                catch (Exception) { continue; }
                foreach (var t in ts)
                {
                    if (t == null || t.FullName == null) continue;
                    if (t.FullName.IndexOf(pattern, StringComparison.OrdinalIgnoreCase) < 0) continue;
                    n++;
                    var ms = new List<string>();
                    try
                    {
                        foreach (var m in t.GetMethods(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic
                                 | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.DeclaredOnly))
                        {
                            if (m.Name.StartsWith("get_") || m.Name.StartsWith("set_") || m.Name.StartsWith("add_") || m.Name.StartsWith("remove_")) continue;
                            var ps = m.GetParameters();
                            if (ps.Length > 1) continue;
                            var sb2 = new StringBuilder(m.Name);
                            sb2.Append("(");
                            for (int i = 0; i < ps.Length; i++)
                            {
                                if (i > 0) sb2.Append(", ");
                                sb2.Append(ps[i].ParameterType.Name);
                            }
                            sb2.Append(")");
                            ms.Add(sb2.ToString());
                        }
                    }
                    catch (Exception) { }
                    log.AppendLine(asm.GetName().Name + " :: " + t.FullName + (typeof(MonoBehaviour).IsAssignableFrom(t) ? " [MB]" : "") );
                    if (ms.Count > 0) log.AppendLine("    " + string.Join("  ", ms.ToArray()));
                    if (n > 120) { log.AppendLine("...(truncated)"); return; }
                }
            }
            log.AppendLine("-- types matching '" + pattern + "': " + n + " --");
        }

        private void Call(string spec, StringBuilder log)
        {
            int i = spec.IndexOf(':');
            string typeName = i < 0 ? spec : spec.Substring(0, i);
            string methodName = i < 0 ? "" : spec.Substring(i + 1);
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type[] ts;
                try { ts = asm.GetTypes(); }
                catch (Exception) { continue; }
                foreach (var t in ts)
                {
                    if (t == null || t.FullName == null) continue;
                    if (t.Name != typeName && t.FullName != typeName) continue;
                    object target = null;
                    if (typeof(MonoBehaviour).IsAssignableFrom(t)) target = UnityEngine.Object.FindObjectOfType(t);
                    var m = t.GetMethod(methodName, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic
                        | System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Static);
                    if (m == null) { log.AppendLine("no method " + methodName + " on " + t.FullName); continue; }
                    try
                    {
                        var res = m.Invoke(m.IsStatic ? null : target, null);
                        log.AppendLine("called " + t.FullName + "." + methodName + " on " + (target == null ? "null" : PathOf(((Component)target).transform)) + " -> " + res);
                    }
                    catch (Exception e) { log.AppendLine("call err " + t.FullName + "." + methodName + " : " + e.Message); }
                    return;
                }
            }
            log.AppendLine("type not found: " + typeName);
        }

        // left-align a group of labels: align:<label1,label2,...>  (names searched under AestheticsPanel)
        private void AlignLabels(string spec, StringBuilder log)
        {
            string[] names = spec.Split(',');
            var parentT = FindByPath("AestheticsPanel");
            if (parentT == null) { log.AppendLine("no AestheticsPanel"); return; }
            var parent = parentT.gameObject;
            var list = new List<TextMeshProUGUI>();
            foreach (var nm in names)
            {
                var go = FindChild(parent.transform, nm.Trim());
                if (go == null) { log.AppendLine("missing label " + nm); continue; }
                var tmp = go.GetComponent<TextMeshProUGUI>();
                if (tmp == null) { log.AppendLine("no TMP on " + nm); continue; }
                tmp.ForceMeshUpdate();
                list.Add(tmp);
            }
            var pt = parent.transform;
            var lefts = new List<float>();
            var widths = new List<float>();
            foreach (var t in list)
            {
                var b = t.textBounds;
                float lx = pt.InverseTransformPoint(t.transform.TransformPoint(new Vector3(b.min.x, 0f, 0f))).x;
                float rx = pt.InverseTransformPoint(t.transform.TransformPoint(new Vector3(b.max.x, 0f, 0f))).x;
                lefts.Add(lx);
                widths.Add(rx - lx);
                log.AppendLine("  " + t.gameObject.name + " text='" + t.text + "' left=" + lx.ToString("F2") + " right=" + rx.ToString("F2") + " w=" + (rx - lx).ToString("F2"));
            }
            float target = lefts[0];
            for (int k = 1; k < lefts.Count; k++) target = Mathf.Min(target, lefts[k]);
            log.AppendLine("  target left=" + target.ToString("F2"));
            for (int k = 0; k < list.Count; k++)
            {
                float d = target - lefts[k];
                if (Mathf.Abs(d) < 0.01f) { log.AppendLine("  " + list[k].gameObject.name + " ok"); continue; }
                var rt = list[k].rectTransform;
                rt.anchoredPosition = new Vector2(rt.anchoredPosition.x + d, rt.anchoredPosition.y);
                int kids = 0;
                foreach (Transform ch in rt)
                {
                    var crt = ch as RectTransform;
                    if (crt == null) continue;
                    crt.anchoredPosition = new Vector2(crt.anchoredPosition.x - d, crt.anchoredPosition.y);
                    kids++;
                }
                log.AppendLine("  " + list[k].gameObject.name + " shift " + d.ToString("F2") + " (children " + kids + ")");
            }
        }

        private static GameObject FindChild(Transform root, string name)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == name) return t.gameObject;
            }
            return null;
        }

        private void List(StringBuilder log)
        {
            int n = 0;
            foreach (var b in Resources.FindObjectsOfTypeAll<Button>())
            {
                if (b == null) continue;
                n++;
                log.AppendLine("BTN\t" + (b.gameObject.activeInHierarchy ? "A" : "H") + "\t" + PathOf(b.transform));
            }
            foreach (var t in Resources.FindObjectsOfTypeAll<Toggle>())
            {
                if (t == null) continue;
                log.AppendLine("TGL\t" + (t.gameObject.activeInHierarchy ? "A" : "H") + "\t" + PathOf(t.transform));
            }
            foreach (var f in Resources.FindObjectsOfTypeAll<TMP_InputField>())
            {
                if (f == null) continue;
                log.AppendLine("INP\t" + (f.gameObject.activeInHierarchy ? "A" : "H") + "\t" + PathOf(f.transform) + "\t" + Esc(f.text ?? ""));
            }
            log.AppendLine("-- buttons " + n + " --");
        }

        private int Toggle(string sub, StringBuilder log)
        {
            var tgs = Resources.FindObjectsOfTypeAll<Toggle>();
            foreach (var t in tgs)
            {
                if (t == null || !t.gameObject.activeInHierarchy) continue;
                if (PathOf(t.transform).IndexOf(sub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                log.AppendLine("  hit " + PathOf(t.transform));
                t.isOn = !t.isOn;
                return 1;
            }
            return 0;
        }

        private int SetText(string sub, string val, StringBuilder log)
        {
            var ifs = Resources.FindObjectsOfTypeAll<TMP_InputField>();
            foreach (var f in ifs)
            {
                if (f == null || !f.gameObject.activeInHierarchy) continue;
                if (PathOf(f.transform).IndexOf(sub, StringComparison.OrdinalIgnoreCase) < 0) continue;
                log.AppendLine("  hit " + PathOf(f.transform));
                f.text = val;
                f.onValueChanged.Invoke(val);
                f.onEndEdit.Invoke(val);
                return 1;
            }
            return 0;
        }
    }
}
