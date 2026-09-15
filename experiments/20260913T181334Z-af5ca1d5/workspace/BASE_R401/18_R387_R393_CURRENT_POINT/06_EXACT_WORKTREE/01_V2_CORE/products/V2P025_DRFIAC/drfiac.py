from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    choice:str|None; blocked:tuple[str,...]; status:str
    def to_dict(self): return asdict(self)
def decision_relevant_firewall(*,channels:list[tuple[str,float,bool]])->Result:
    clean=[x for x in channels if not x[2]]
    blocked=tuple(x[0] for x in channels if x[2])
    if not clean:return Result(None,blocked,'FIREWALL_BLOCKED_ALL_DRE_CHANNELS')
    best=max(clean,key=lambda x:(x[1],x[0]))
    return Result(best[0],blocked,'DRE_RANKED_CLEAN_FIAC_CHANNEL')
