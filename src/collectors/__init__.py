from .fda_enforcement import FDAEnforcementCollector
from .fsis import FSISCollector
from .fsa_uk import FSAUKCollector
from .rasff import RASFFCollector

COLLECTORS = {
    "fda_enforcement": FDAEnforcementCollector,
    "fsis": FSISCollector,
    "fsa_uk": FSAUKCollector,
    "rasff": RASFFCollector,
}
