from typing import Dict, TypedDict, List


Seconds = int
Height = int
ETH = float 
BASE = float
RAI = float
exaRAI = float
UNI = float
ETH_per_BASE = float
RAI_per_BASE = float
BASE_per_RAI = float
BASE_per_RAI_Seconds = float
BASE_per_Seconds = float
BASE_per_ETH = float
Percentage_Per_Second = float
Percentage = float
Per_BASE = float
Per_BASE_Seconds = float
Per_RAY = float
Run = int
Timestep = int
Gwei = int

class CDP_Metric(TypedDict):
    cdp_count: int
    open_cdp_count: int
    closed_cdp_count: int
    mean_cdp_collateral: float
    median_cdp_collateral: float


class OptimalValues(TypedDict):
    u_1: RAI
    u_2: RAI
    v_1: RAI
    v_2: RAI
