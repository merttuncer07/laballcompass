from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    explore_hidden:bool; action_margin:float; hidden_effect_bound:float; status:str
    def to_dict(self): return asdict(self)
def hidden_population_explore(*,action_margin:float,hidden_mass:float,max_effect_per_mass:float)->Result:
    if action_margin<0 or not 0<=hidden_mass<=1 or max_effect_per_mass<0: raise ValueError('invalid shell')
    b=hidden_mass*max_effect_per_mass
    ex=b>=action_margin
    return Result(ex,action_margin,b,'HIDDEN_POPULATION_CAN_TIP_DECISION' if ex else 'HIDDEN_POPULATION_BOUND_ACTION_INVARIANT')
