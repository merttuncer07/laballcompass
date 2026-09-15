"""Importable access to the consolidated R38 kernel collection."""
import importlib.util,sys
from pathlib import Path
SOURCE=next((Path(__file__).parent/'BASE_R401/18_R387_R393_CURRENT_POINT/06_EXACT_WORKTREE/03_LCB_EXECUTABLE_AND_EVIDENCE/prototypes').glob('*__r38.py'))
_name='_laballcompass_consolidated_r38'
if _name not in sys.modules:
    _spec=importlib.util.spec_from_file_location(_name,SOURCE)
    _module=importlib.util.module_from_spec(_spec);sys.modules[_name]=_module;_spec.loader.exec_module(_module)
else:_module=sys.modules[_name]
__all__=sorted(name for name,value in vars(_module).items() if isinstance(value,type) and value.__module__==_name)
globals().update({name:getattr(_module,name) for name in __all__})
