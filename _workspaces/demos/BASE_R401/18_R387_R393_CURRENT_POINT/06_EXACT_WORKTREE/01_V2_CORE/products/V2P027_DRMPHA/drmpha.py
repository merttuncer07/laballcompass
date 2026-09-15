from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    audit_order:tuple[str,...]; selected:str|None; status:str
    def to_dict(self): return asdict(self)
def decision_relevant_holdout_audit(*,development_scores:dict[str,float],protected_losses:dict[str,float])->Result:
    if set(development_scores)!=set(protected_losses): raise ValueError('policy sets must match')
    order=tuple(sorted(development_scores,key=lambda k:(-development_scores[k],k)))
    if not order:return Result(order,None,'NO_POLICIES')
    # holdout consulted only after order freeze; selected is protected best for audit reporting, not reranking the order
    selected=min(protected_losses,key=lambda k:(protected_losses[k],k))
    return Result(order,selected,'DRE_ORDER_FROZEN_BEFORE_PROTECTED_HOLDOUT')
