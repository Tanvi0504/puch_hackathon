import re
from typing import Dict, Optional

SCOPES = ["today", "week", "weekly", "month", "monthly"]

def normalize_scope(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s = s.lower()
    if s in ("weekly",): return "week"
    if s in ("monthly",): return "month"
    if s in ("today","week","month"): return s
    return None

def parse(text: str) -> Dict[str, Optional[str]]:
    t = text.strip().lower()

    # add
    m = re.match(r"(add|append|put|create|new)\s+(?P<what>.+?)\s+(to\s+)?(my\s+)?(?P<scope>today|this week|week|weekly|this month|month|monthly)", t)
    if m:
        what = m.group("what")
        sc = m.group("scope").replace("this ","")
        return {"intent":"add", "scope": normalize_scope(sc), "text": what}

    # list/show
    m = re.match(r"(show|list|view|see)(\s+my)?\s+(?P<scope>today|this week|week|weekly|this month|month|monthly)?", t)
    if m:
        sc = m.group("scope")
        if sc: sc = sc.replace("this ","")
        return {"intent":"list", "scope": normalize_scope(sc), "text": None}

    # complete/done
    m = re.match(r"(complete|done|finish|tick|mark)\s+(?P<what>.+)", t)
    if m:
        return {"intent":"complete", "scope": None, "text": m.group("what")}

    # delete/remove
    m = re.match(r"(delete|del|remove|drop|cancel)\s+(?P<what>.+)", t)
    if m:
        return {"intent":"delete", "scope": None, "text": m.group("what")}

    # quick patterns
    if t in ("today","week","weekly","month","monthly"):
        return {"intent":"list", "scope": normalize_scope(t), "text": None}
    if t in ("list","show", "tasks"):
        return {"intent":"list", "scope": None, "text": None}
    if t in ("help","hi","hello"):
        return {"intent":"help", "scope": None, "text": None}

    return {"intent":"unknown", "scope": None, "text": text}