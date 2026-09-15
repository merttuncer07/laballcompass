from dataclasses import dataclass, asdict
@dataclass(frozen=True)
class Result:
    wealth_before:float; wealth_after:float; spent:float; test:bool; status:str
    def to_dict(self): return asdict(self)
def boundary_gated_wealth(*,wealth:float,price:float,lower_action:int,upper_action:int)->Result:
    if wealth<0 or price<0: raise ValueError('wealth and price must be nonnegative')
    crossed=lower_action!=upper_action
    if not crossed: return Result(wealth,wealth,0.0,False,'ACTION_INVARIANT_WEALTH_PRESERVED')
    if price>wealth: return Result(wealth,wealth,0.0,False,'BOUNDARY_PRESENT_INSUFFICIENT_WEALTH')
    return Result(wealth,wealth-price,price,True,'BOUNDARY_RELEASED_TESTING_WEALTH')
