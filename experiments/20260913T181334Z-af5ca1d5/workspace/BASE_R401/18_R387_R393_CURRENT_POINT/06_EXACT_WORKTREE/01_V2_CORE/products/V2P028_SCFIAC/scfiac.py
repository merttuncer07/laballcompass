from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    choice:str|None; blocked_suspect:tuple[str,...]; blocked_support:tuple[str,...]; status:str
    def to_dict(self): return asdict(self)
def support_constrained_firewall(*,channels:list[tuple[str,float,bool,bool]])->Result:
    # name, value, suspect, supported
    suspect=tuple(x[0] for x in channels if x[2])
    unsupported=tuple(x[0] for x in channels if not x[3])
    good=[x for x in channels if not x[2] and x[3]]
    if not good:return Result(None,suspect,unsupported,'NO_SAFE_SUPPORTED_CHANNEL')
    best=max(good,key=lambda x:(x[1],x[0]))
    return Result(best[0],suspect,unsupported,'SUPPORT_AND_FIREWALL_GATED_ACQUISITION')
