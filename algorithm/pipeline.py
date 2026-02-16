import pandas as pd
import numpy as np
from collections import deque
import re
from pathlib import Path
import xlwings as xw
import matplotlib.pyplot as plt
import matplotlib
import warnings
import json
from typing import Callable
from dataclasses import dataclass


#(window, rot_window, std_threshold, rot_threshold, hit_count)
#(window, count, std_threshold)
STD_ALG_PARAMS = (10, 10, 0.20)
ORP_DATA_PATH = str(Path.cwd()) +'/algorithm/temp'
TEMP_DATA_PATH = str(Path.cwd()) +'/algorithm/temp'
TIME_COL = 'time(s)'
VALUE_COL = 'mvs'
ALG_MODE = 3
DO_NOT_USE = []
# Include only files whose names contain one of these date strings (e.g. "11_18_2025").
# Leave empty to include all dates.
DATE_FILTERS = ["02_11_2026", "02_10_2026"]

warnings.filterwarnings('ignore')

class SlidingExpFit:
    """
    Fit y(t) ≈ E_inf + A * exp(-k t) on a sliding window.
    Assumes time already zeroed at injection/peak.
    """
    def __init__(self, window:int, E_inf:float):
        self.window = window
        self.E_inf = E_inf
        self.buf = deque(maxlen=window)

    def update(self, t: float, y: float):
        """
        Add one point and return (A, k) or (None, None) until we can fit.
        """
        # we need y > E_inf for log
        if y <= self.E_inf:
            # if we fall at/below baseline, model not valid anymore
            self.buf.clear()
            return None, None

        self.buf.append((t, y))
        if len(self.buf) < 2:
            return None, None

        t_arr = np.fromiter((p[0] for p in self.buf), dtype=float)
        y_arr = np.fromiter((p[1] for p in self.buf), dtype=float)

        z = np.log(y_arr - self.E_inf)

        t_mean = t_arr.mean()
        z_mean = z.mean()

        s_tt = np.sum((t_arr - t_mean) ** 2)
        if s_tt == 0:
            return None, None

        s_tz = np.sum((t_arr - t_mean) * (z - z_mean))
        beta = s_tz / s_tt            # slope in z = alpha + beta t
        alpha = z_mean - beta * t_mean

        k = -beta                     # because z = ln A - k t
        A = np.exp(alpha)

        if k <= 0:
            return None, None

        return A, k
    

#for algs
class SlidingSlopeLR:
    #using ordinary least squares (OLS)
    def __init__(self, window):
        self.window = window
        self.time_deq = deque(maxlen=window)
        self.mv_deq = deque(maxlen=window)

    def update(self, t, v):
        self.time_deq.append(t)
        self.mv_deq.append(v)

        if len(self.time_deq) < self.window:
            return None

        t_arr = np.fromiter(self.time_deq, dtype=float)
        v_arr = np.fromiter(self.mv_deq, dtype=float)

        t_mean = t_arr.mean()
        v_mean = v_arr.mean()

        numerator = np.sum((t_arr - t_mean) * (v_arr - v_mean))
        denominator = np.sum((t_arr - t_mean)**2)

        return numerator / denominator if denominator != 0 else 0.0
    
#for algs
class SlidingSTD:
    def __init__(self, window):
        self.window = window
        self.value_deq = deque(maxlen=window)
    
    def update(self, v):
        self.value_deq.append(v)

        if len(self.value_deq) != self.window:
            return None
        
        std = np.std(self.value_deq)

        return std

def extract_files(bad_format=False, date_filters=None) -> dict:
    '''
    extract text files path into a dict, key is reaction concentration
    file name format: 8C72H20_11_12_2010_r1.txt or .csv
    program will output data as:

    time(s) mvs
    0.201 100
    0.402 150
    etc..

    bad format has form (to be changed)

    time: 0.201, mvs: 200
    time: 0.401, mvs: 100

    '''
    parsed_files = {}
    if date_filters is None:
        date_filters = DATE_FILTERS
    
    for file in Path(ORP_DATA_PATH).iterdir():
        file_name = file.name
        print(file_name)
        if date_filters and not any(date in file_name for date in date_filters):
            continue
        conc_str = file_name[: file_name.find("C")]
        if conc_str.isdigit() and int(conc_str) in DO_NOT_USE:
            print(f"Skipping concentration {conc_str} for file: {file_name}")
            continue
        df = None
        if bad_format:
            df = pd.read_csv(file, delimiter=',').drop(columns='delete')
        else:
            df = pd.read_csv(file, delimiter=',')
        if file.suffix == ".txt":
            df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce").astype(float)
            df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce").astype(float)
        
        #parsed_files[file_name] = tuple(zip(*(df[col] for col in df.columns))) #will be in the format ((time, mvs), (time, mvs))
        parsed_files[file_name] = df

    return parsed_files

def filter_by_10seconds_after_maxima(df:pd.DataFrame) -> pd.DataFrame:
    '''
    filters dataframe to only include data 10 seconds after maxima
    '''
    df = df.copy()
    max_val = df[VALUE_COL].max()
    first_index = df[df[VALUE_COL] == max_val].index[0]
    time_of_first = df.loc[first_index, TIME_COL]

    df = df[df[TIME_COL] >= time_of_first + 10].copy()
    df[TIME_COL] = df[TIME_COL] - (time_of_first + 10)
    return df

def filter_data_to_start_at_relative_maxima(df:pd.DataFrame, target_threshold) -> pd.DataFrame:
    '''
    filters dataframe to only include data after maxima
    '''
    df = df.copy()
    rel = target_threshold / df[VALUE_COL].max()
    df[VALUE_COL] = df[VALUE_COL] * rel

    return df

def filter_data_to_start_at_adjusted_maxima(df:pd.DataFrame, target_threshold) -> pd.DataFrame:
    '''
    filters dataframe to only include data after maxima
    '''
    df = df.copy()
    offset = target_threshold - df[VALUE_COL].max()
    df[VALUE_COL] = df[VALUE_COL] + offset

    return df

def filter_data_for_analysis(df: pd.DataFrame, file_name: str | None = None) -> pd.DataFrame:
    df = filter_manual_injection_delay_by_maxima_indv(df, file_name)
    #df = filter_data_to_start_at_relative_maxima(df, 30)
    return df

def _safe_mean(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    values = values[~np.isnan(values)]
    if values.size == 0:
        return None
    return float(np.mean(values))

def _rolling_std_avg(series: pd.Series, window: int) -> float | None:
    series = pd.to_numeric(series, errors="coerce")
    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=0)
    return _safe_mean(rolling_std)

def calculate_avg_std_deviation_quartiles(
    df: pd.DataFrame,
    rolling_window: int = 10,
) -> dict:
    df = df.copy()
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")
    df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce")

    time_series = df[TIME_COL].dropna()
    if time_series.empty:
        return {
            "std_q1": None,
            "std_q2": None,
            "std_q3": None,
            "std_q4": None,
        }

    q1 = time_series.quantile(0.25)
    q2 = time_series.quantile(0.50)
    q3 = time_series.quantile(0.75)

    results = {}
    results["std_q1"] = _rolling_std_avg(
        df.loc[df[TIME_COL] <= q1, VALUE_COL],
        rolling_window,
    )
    results["std_q2"] = _rolling_std_avg(
        df.loc[(df[TIME_COL] > q1) & (df[TIME_COL] <= q2), VALUE_COL],
        rolling_window,
    )
    results["std_q3"] = _rolling_std_avg(
        df.loc[(df[TIME_COL] > q2) & (df[TIME_COL] <= q3), VALUE_COL],
        rolling_window,
    )
    results["std_q4"] = _rolling_std_avg(
        df.loc[df[TIME_COL] > q3, VALUE_COL],
        rolling_window,
    )
    return results

def _concentration_sort_key(file_name: str) -> tuple[int, str]:
    match = re.match(r"^(\d+)C", file_name)
    if match:
        return int(match.group(1)), file_name
    return float("inf"), file_name

def filter_manual_injection_delay(parsed_files:dict) -> dict:

    for file_name, parsed_df in parsed_files.items():
        '''
        We want to filter out negative ORP, since the automated injected mechanism and alg will start at the same time, 
        so we can assume values will spike (over 0) when stopping mechanisms is triggered.
        Therefore we want values > 0, since the spike is almost instantaneous, this will filter out the injection delay.
        '''
        df = parsed_df
        print(df.columns)
        mask = df[VALUE_COL] > 0
        first_index = mask.idxmax()
        time_of_first = df.loc[first_index, TIME_COL]
        print("time of injection:", time_of_first, "file:", file_name)
        df = df.iloc[first_index:].copy()
        df[TIME_COL] = df[TIME_COL] - time_of_first

        parsed_files[file_name] = df
        

    return parsed_files

def filter_manual_injection_delay_by_maxima(parsed_files:dict) -> dict:
    for file_name, parsed_df in parsed_files.items():
        
        df = parsed_df

        max_val = df[VALUE_COL].max()
        first_index = df[df[VALUE_COL] == max_val].index[0]
        time_of_first = df.loc[first_index, TIME_COL]

        print("time of injection:", time_of_first, "file:", file_name, "maxima:", max_val)
        df = df.loc[first_index:].copy()

        df[TIME_COL] = df[TIME_COL] - time_of_first

        parsed_files[file_name] = df
                

    return parsed_files

def filter_manual_injection_by_jump_greater_than_threshold(df, file_name, threshold=10) -> dict:
    df = df.copy()
    df[VALUE_COL] = pd.to_numeric(df[VALUE_COL], errors="coerce")
    df[TIME_COL] = pd.to_numeric(df[TIME_COL], errors="coerce")

    diff = df[VALUE_COL].diff()
    mask = diff > threshold
    first_index = mask.idxmax()
    time_of_first = df.loc[first_index, TIME_COL]
    print("time of injection:", time_of_first, "file:", file_name)
    df = df.iloc[first_index:].copy()
    df[TIME_COL] = df[TIME_COL] - time_of_first

    return df

def filter_manual_injection_delay_by_greater_than_zero_indv(df, file_name) -> dict:
    mask = df[VALUE_COL] > 0
    first_index = mask.idxmax()
    time_of_first = df.loc[first_index, TIME_COL]
    print("time of injection:", time_of_first, "file:", file_name)
    df = df.iloc[first_index:].copy()
    df[TIME_COL] = df[TIME_COL] - time_of_first

    return df

def filter_manual_injection_delay_by_maxima_indv(parsed_file, file_name):
   
    df = parsed_file

    max_val = df[VALUE_COL].max()
    first_index = df[df[VALUE_COL] == max_val].index[0]
    time_of_first = df.loc[first_index, TIME_COL]

    print("time of injection:", time_of_first, "file:", file_name, "maxima:", max_val)
    df = df.loc[first_index:].copy()

    df[TIME_COL] = df[TIME_COL] - time_of_first
                
    return df

def get_reaction_mins(data):
    df = data
    min_val = df[VALUE_COL].min()
    return min_val


def zip_dfs_into_tuples(parsed_files:dict) -> dict:

    for file_name, parsed_file in parsed_files.items():
        df = parsed_file
        parsed_files[file_name] = tuple(zip(df[TIME_COL].to_numpy(), df[VALUE_COL].to_numpy())) #dfs become ((time, mvs), (time, mvs))
    
    return parsed_files


def zip_dfs_into_tuples_indv(parsed_file):

   
    df = parsed_file
    df = tuple(zip(df[TIME_COL].to_numpy(), df[VALUE_COL].to_numpy())) #dfs become ((time, mvs), (time, mvs))
    
    return df


def std_deviation_alg(window=10, std_threshold=0.2, hit_threshold=10, data=None):
    '''
    uses: standard deviation as a stopping criteria
    '''
    std_arr = []
    time_arr = []
    mvs_arr = []
    stop_result = None

    std_c = SlidingSTD(window=window)
    arr = deque(maxlen=window)
    hits = 0
    for time, mvs in data:
        arr.append(mvs)
        std = std_c.update(mvs)
        std_arr.append(std), time_arr.append(time), mvs_arr.append(mvs)
        if std is not None:
            if std < std_threshold:
                hits += 1
                if hits == hit_threshold:
                    stop_result = pd.DataFrame({
                                                    "mvs": [mvs], 
                                                    "std" : [std], 
                                                    "time" : [time]
                                                })
            else:
                hits = 0
    return stop_result, pd.DataFrame({
                                "time" : time_arr,
                                "mvs": mvs_arr, 
                                "std" : std_arr
                                    })


def std_deviation_rate_of_change_alg(window=10, rot_window=10, std_threshold=10, rot_threshold=2, hit_threshold=10, data=None):
    '''
    best alg out of the three:
    uses: OLS, ordinary least squares as an estimator for the slope, combined with standard deviation
    
    '''
    std_arr = []
    time_arr = []
    rot_arr = []
    mvs_arr = []
    stop_result = None

    slope = SlidingSlopeLR(rot_window)
    std_c = SlidingSTD(window=window)
    arr = deque(maxlen=window)
    hits = 0
    for time, mvs in data:
        arr.append(mvs)
        rot = slope.update(time, mvs)
        std = std_c.update(mvs)
        std_arr.append(std), time_arr.append(time), rot_arr.append(rot), mvs_arr.append(mvs)
        if std is not None and rot is not None:
            if abs(rot) < rot_threshold and std < std_threshold:
                hits += 1
                if hits == hit_threshold:
                    stop_result = pd.DataFrame({
                                                    "mvs": [mvs], 
                                                    "ols_rot" : [rot], 
                                                    "std" : [std], 
                                                    "time" : [time]
                                                })
            else:
                hits = 0
    return (stop_result, pd.DataFrame({
                                "time" : time_arr,
                                "mvs": mvs_arr, 
                                "ols_rot" : rot_arr, 
                                "std" : std_arr
                                    }))

def std_deviation_rate_of_change_alg_two(window=10, rot_window=10, threshold=5, hit_threshold=10, data=None):
    '''
    best alg out of the three:
    uses: OLS, ordinary least squares as an estimator for the slope, combined with standard deviation
    
    '''
    std_arr = []
    time_arr = []
    rot_arr = []
    mvs_arr = []
    stop_result = {}

    slope = SlidingSlopeLR(rot_window)
    std_c = SlidingSTD(window=window)
    arr = deque(maxlen=window)
    hits = 0
    for time, mvs in data:
        arr.append(mvs)
        rot = slope.update(time, mvs)
        std = std_c.update(mvs)
        std_arr.append(std), time_arr.append(time), rot_arr.append(rot), mvs_arr.append(mvs)
        if std is not None and rot is not None:
            curr = rot - std
            if abs(curr) < threshold:
                hits += 1
                if hits == hit_threshold:
                    stop_result = pd.DataFrame({
                                                    "mvs": [mvs], 
                                                    "ols_rot" : [rot], 
                                                    "std" : [std], 
                                                    "time" : [time]
                                                })
            else:
                hits = 0
    return stop_result, pd.DataFrame({
                                "time" : time_arr,
                                "mvs": mvs_arr, 
                                "ols_rot" : rot_arr, 
                                "std" : std_arr
                                    })

def sliding_exp_stop(
    data,
    E_inf: float,
    window: int = 15,
    completion: float = 0.75,   # 75% of decay completed
    k_stability_hits: int = 5,  # how many consecutive stable fits to require
    k_tol_rel: float = 0.05     # relative tolerance for k stability (5%)
):
    """
    data: iterable of (time, mvs) after injection, time already zeroed.
    E_inf: estimated final baseline ORP for this run.
    Returns:
        stop_result_df, debug_df
    """
    fitter = SlidingExpFit(window=window, E_inf=E_inf)

    times, mvs_list, A_list, k_list, t_target_list = [], [], [], [], []
    last_k = None
    stable_hits = 0
    stop_result = None

    for t, y in data:
        A, k = fitter.update(t, y)
        times.append(t)
        mvs_list.append(y)
        A_list.append(A)
        k_list.append(k)

        if A is None or k is None:
            t_target_list.append(None)
            continue

        # target time for chosen completion fraction
        t_target = (1.0 / k) * np.log(1.0 / (1.0 - completion))
        t_target_list.append(t_target)

        # check k stability
        if last_k is not None and last_k > 0:
            rel_diff = abs(k - last_k) / last_k
            if rel_diff < k_tol_rel:
                stable_hits += 1
            else:
                stable_hits = 0
        last_k = k

        # stopping condition: we are past predicted target
        # AND k has been stable for a few iterations
        if stable_hits >= k_stability_hits and t >= t_target:
            stop_result = pd.DataFrame(
                {
                    "time": [t],
                    "mvs": [y],
                    "A": [A],
                    "k": [k],
                    "t_target": [t_target],
                }
            )
            break

    debug_df = pd.DataFrame(
        {
            "time": times,
            "mvs": mvs_list,
            "A": A_list,
            "k": k_list,
            "t_target": t_target_list,
        }
    )

    return stop_result, debug_df

def sliding_exp(*, data, E_inf, window, completion, k_stability_hits, k_tol_rel):
    stop_result, debug_df = sliding_exp_stop(E_inf=E_inf,
                                             window=window,
                                             completion=completion,
                                             k_stability_hits=k_stability_hits,
                                             k_tol_rel=k_tol_rel,
                                             data=data)
    return stop_result, debug_df


def std_ols_alg_2t(*, data, window, rot_window, std_threshold, rot_threshold, hit_threshold):
    stop_result, debug_df = std_deviation_rate_of_change_alg(window=window, 
                                                             rot_window=rot_window, 
                                                             std_threshold=std_threshold, 
                                                             rot_threshold=rot_threshold, 
                                                             hit_threshold=hit_threshold,
                                                             data=data)
    return stop_result, debug_df

def std_ols_alg_1t(*, data, window, rot_window, threshold, hit_threshold):
    stop_result, debug_df = std_deviation_rate_of_change_alg_two(window=window, 
                                                                 rot_window=rot_window, 
                                                                 threshold=threshold, 
                                                                 hit_threshold=hit_threshold,
                                                                 data=data)
    return stop_result, debug_df

def codex_alg(*, data, completion, flat_seconds, slope_threshold, rot_window, tail_seconds):
    points = list(data)
    if not points:
        return None, pd.DataFrame(columns=["time", "mvs", "ols_rot", "completion", "flat_s"])

    times = [t for t, _ in points]
    mvs_vals = [m for _, m in points]

    end_time = times[-1]
    tail_vals = [m for t, m in points if t >= end_time - tail_seconds]
    if not tail_vals:
        tail_count = max(1, len(mvs_vals) // 10)
        tail_vals = mvs_vals[-tail_count:]
    E_inf = float(np.median(tail_vals))

    A0 = mvs_vals[0] - E_inf
    if A0 == 0:
        A0 = 1e-9

    slope = SlidingSlopeLR(rot_window)
    flat_duration = 0.0
    last_t = None
    stop_result = None

    time_arr = []
    mvs_arr = []
    rot_arr = []
    completion_arr = []
    flat_arr = []

    for t, mvs in points:
        rot = slope.update(t, mvs)
        completion_val = 1.0 - ((mvs - E_inf) / A0)
        if rot is not None and last_t is not None:
            if abs(rot) <= slope_threshold:
                flat_duration += (t - last_t)
            else:
                flat_duration = 0.0
        last_t = t

        time_arr.append(t)
        mvs_arr.append(mvs)
        rot_arr.append(rot)
        completion_arr.append(completion_val)
        flat_arr.append(flat_duration)

        if rot is not None and completion_val >= completion and flat_duration >= flat_seconds:
            stop_result = pd.DataFrame(
                {
                    "time": [t],
                    "mvs": [mvs],
                    "ols_rot": [rot],
                    "completion": [completion_val],
                    "flat_s": [flat_duration],
                }
            )
            break

    debug_df = pd.DataFrame(
        {
            "time": time_arr,
            "mvs": mvs_arr,
            "ols_rot": rot_arr,
            "completion": completion_arr,
            "flat_s": flat_arr,
        }
    )

    return stop_result, debug_df
                

@dataclass
class AlgoSpec:
    name: str
    func: Callable[..., tuple[pd.DataFrame, pd.DataFrame]]
    params: dict



RUNS = [
    [
    # ============================
    # 1. FAST-RESPONSE PROFILES
    # (small window, low stability, loose tolerance)
    # ============================
    AlgoSpec(
        name="STD_OLS_1T_fast1",
        func=std_deviation_alg,
        params={"window": 10, "std_threshold": 2, "hit_threshold": 3},
    ),
    AlgoSpec(
        name="STD_OLS_1T_fast2",
        func=std_deviation_alg,
        params={"window": 10, "std_threshold": 0.05, "hit_threshold": 5},

    ),
    AlgoSpec(
        name="STD_OLS_1T_fast3",
        func=std_deviation_alg,
        params={"window": 10, "std_threshold": 0.05, "hit_threshold": 7},
    ),
    # ============================
    # 2. BALANCED PROFILES
    # (moderate window, moderate stability, realistic for comp)
    # ============================
    AlgoSpec(
        name="STD_OLS_1T_bal1",
        func=std_deviation_alg,
        params={"window": 15, "std_threshold": 0.08, "hit_threshold": 10},
    ),
    AlgoSpec(
        name="STD_OLS_1T_bal2",
        func=std_deviation_alg,
        params={"window": 20, "std_threshold": 0.07, "hit_threshold": 12},
    ),
    AlgoSpec(
        name="STD_OLS_1T_bal3",
        func=std_deviation_alg,
        params={"window": 25, "std_threshold": 0.05, "hit_threshold": 15},
    ),
    # ============================          
    # 3. STABILITY-HEAVY PROFILES

    # (large window, many hits, strict tolerance)
    # ============================
    AlgoSpec(
        name="STD_OLS_1T_stable1",
        func=std_deviation_alg,
        params={"window": 30, "std_threshold": 0.03, "hit_threshold": 20},
    ),
    AlgoSpec(
        name="STD_OLS_1T_stable2",
        func=std_deviation_alg,
        params={"window": 35, "std_threshold": 0.02, "hit_threshold": 25},
    ),
    AlgoSpec(
        name="STD_OLS_1T_stable3",
        func=std_deviation_alg,
        params={"window": 40, "std_threshold": 0.01, "hit_threshold": 30},
    ),
    # ============================
    # 4. LATE-PHASE / HIGH-COMPLETION
    # (aggressive completion %, closer to true E_inf)
    # ============================
    AlgoSpec(
        name="STD_OLS_1T_late1",
        func=std_deviation_alg,
        params={"window": 20, "std_threshold": 0.05, "hit_threshold": 15},
    ),
    AlgoSpec(
        name="STD_OLS_1T_late2",
        func=std_deviation_alg,
        params={"window": 25, "std_threshold": 0.04, "hit_threshold": 18},
    ),
    AlgoSpec(
        name="STD_OLS_1T_late3",
        func=std_deviation_alg,
        params={"window": 30, "std_threshold": 0.03, "hit_threshold": 20},
    ),

    ]
]

'''[

    # ============================
    # 1. FAST-RESPONSE PROFILES
    # (small window, low stability, loose tolerance)
    # ============================
    AlgoSpec(
        name="test1",
        func=std_deviation_rate_of_change_alg_two,
        params={"window": 10, "rot_window": 10, "threshold": 5, "hit_threshold": 5},
    ),
    AlgoSpec(
        name="test2",
        func=std_deviation_rate_of_change_alg_two,
        params={"window": 10, "rot_window": 10, "threshold": 2, "hit_threshold": 10},
    ),
    AlgoSpec(
        name="test3",
        func=std_deviation_rate_of_change_alg_two,
        params={"window": 10, "rot_window": 10, "threshold": 1, "hit_threshold": 10},
    ),
    AlgoSpec(
        name="STD_OLS_1T_temp_opt3",
        func=std_deviation_rate_of_change_alg_two,
        params={
            "window": 10,
            "rot_window": 10,
            "threshold": 2.6671907037180524,
            "hit_threshold": 10,
        },
    ),
],

[
    AlgoSpec(
        name="CODEX_DECAY_FLAT_80PCT_3S",
        func=codex_alg,
        params={
            "completion": 0.80,
            "flat_seconds": 3.0,
            "slope_threshold": 0.5,
            "rot_window": 10,
            "tail_seconds": 5.0,
        },
    ),
    AlgoSpec(
        name="CODEX_DECAY_FLAT_80PCT_2S",
        func=codex_alg,
        params={
            "completion": 0.80,
            "flat_seconds": 2.0,
            "slope_threshold": 0.5,
            "rot_window": 10,
            "tail_seconds": 5.0,
        },
    ),
    AlgoSpec(
        name="CODEX_DECAY_FLAT_80PCT_4S",
        func=codex_alg,
        params={
            "completion": 0.80,
            "flat_seconds": 4.0,
            "slope_threshold": 0.5,
            "rot_window": 10,
            "tail_seconds": 5.0,
        },
    ),
    AlgoSpec(
        name="CODEX_DECAY_FLAT_85PCT_3S",
        func=codex_alg,
        params={
            "completion": 0.85,
            "flat_seconds": 3.0,
            "slope_threshold": 0.5,
            "rot_window": 10,
            "tail_seconds": 5.0,
        },
    ),
    AlgoSpec(
        name="CODEX_DECAY_FLAT_75PCT_3S",
        func=codex_alg,
        params={
            "completion": 0.75,
            "flat_seconds": 3.0,
            "slope_threshold": 0.5,
            "rot_window": 10,
            "tail_seconds": 5.0,
        },
    ),
],

[
    # ============================
    # 1. FAST-RESPONSE PROFILES
    # (small window, low stability, loose tolerance)
    # ===========================
    AlgoSpec(
        name="EXP_DECAY_fast1",
        func=sliding_exp_stop,
        params={"window": 6, "completion": 0.60, "k_stability_hits": 2, "k_tol_rel": 0.15},
    ),
    AlgoSpec(
        name="EXP_DECAY_fast2",
        func=sliding_exp_stop,
        params={"window": 8, "completion": 0.65, "k_stability_hits": 2, "k_tol_rel": 0.10},
    ),
    AlgoSpec(
        name="EXP_DECAY_fast3",
        func=sliding_exp_stop,
        params={"window": 10, "completion": 0.70, "k_stability_hits": 3, "k_tol_rel": 0.12},
    ),


    # ============================
    # 2. BALANCED PROFILES
    # (moderate window, moderate stability, realistic for comp)
    # ============================

    AlgoSpec(
        name="EXP_DECAY_bal1",
        func=sliding_exp_stop,
        params={"window": 12, "completion": 0.75, "k_stability_hits": 4, "k_tol_rel": 0.07},
    ),
    AlgoSpec(
        name="EXP_DECAY_bal2",
        func=sliding_exp_stop,
        params={"window": 15, "completion": 0.75, "k_stability_hits": 5, "k_tol_rel": 0.05},
    ),
    AlgoSpec(
        name="EXP_DECAY_bal3",
        func=sliding_exp_stop,
        params={"window": 20, "completion": 0.80, "k_stability_hits": 4, "k_tol_rel": 0.06},
    ),


    # ============================
    # 3. STABILITY-HEAVY PROFILES
    # (large window, many hits, strict tolerance)
    # ============================

    AlgoSpec(
        name="EXP_DECAY_stable1",
        func=sliding_exp_stop,
        params={"window": 18, "completion": 0.75, "k_stability_hits": 7, "k_tol_rel": 0.04},
    ),
    AlgoSpec(
        name="EXP_DECAY_stable2",
        func=sliding_exp_stop,
        params={"window": 20, "completion": 0.80, "k_stability_hits": 8, "k_tol_rel": 0.03},
    ),
    AlgoSpec(
        name="EXP_DECAY_stable3",
        func=sliding_exp_stop,
        params={"window": 25, "completion": 0.75, "k_stability_hits": 10, "k_tol_rel": 0.02},
    ),


    # ============================
    # 4. LATE-PHASE / HIGH-COMPLETION
    # (aggressive completion %, closer to true E_inf)
    # ============================

    AlgoSpec(
        name="EXP_DECAY_late1",
        func=sliding_exp_stop,
        params={"window": 12, "completion": 0.85, "k_stability_hits": 5, "k_tol_rel": 0.06},
    ),
    AlgoSpec(
        name="EXP_DECAY_late2",
        func=sliding_exp_stop,
        params={"window": 15, "completion": 0.90, "k_stability_hits": 6, "k_tol_rel": 0.05},
    ),
    AlgoSpec(
        name="EXP_DECAY_late3",
        func=sliding_exp_stop,
        params={"window": 20, "completion": 0.92, "k_stability_hits": 6, "k_tol_rel": 0.04},
    ),'''



def run_alg(spec: AlgoSpec, data, min):
    stop_df = None
    debug_df = None
    if min is not None:
        stop_df, debug_df = spec.func(data=data, E_inf=min, **spec.params)
    else:
        stop_df, debug_df = spec.func(data=data, **spec.params)
    return stop_df, debug_df



def to_excel(df_total:pd.DataFrame, df_stop:pd.DataFrame, file_name:str, path):

    """
    all_data:
        dict or DataFrame with full series, expected keys/cols:
            "time", "mvs", "ols_rot", "std"

    stopping_data:
        dict like:
            {
                "mvs": mvs_scalar_or_array,
                "ols_rot": rot_scalar_or_array (optional),
                "std": std_scalar_or_array (optional),
                "time": time_scalar_or_array
            }

    file_name:
        original file Path or str (e.g. CSV path)

    path:
        base output folder for Excel files
    
    """

    # Extract scalar stop time/mvs for plotting
    stop_time = float(df_stop["time"].iloc[0])
    stop_mvs = float(df_stop["mvs"].iloc[0])

    # ---------- build output path ----------
    base_path = Path(path).expanduser()
    base_path.mkdir(parents=True, exist_ok=True)

    file_name = Path(file_name)
    out_path = base_path / (file_name.stem + ".xlsx")

    # ---------- create workbook & sheet ----------
    wb = xw.Book()
    sheet_name = file_name.stem or "Sheet1"
    sht = wb.sheets[0]
    sht.name = sheet_name

    # ---------- write total data (A:D) ----------
    # A: time, B: mvs, C: ols_rot, D: std
    sht["A1"].value = df_total

    # ---------- write stopping data (G:H) ----------
    sht["G1"].value = "Stopping points"
    sht["G2"].value = df_stop  # headers in G2, data from G3

    # ---------- compute linear fit and R^2 ----------
    x = df_total["time"].to_numpy(dtype=float)
    y = df_total["mvs"].to_numpy(dtype=float)

    if len(x) < 2:
        wb.save(out_path)
        return

    coeffs = np.polyfit(x, y, 1)  # slope, intercept
    slope, intercept = coeffs
    y_fit = slope * x + intercept

    y_mean = y.mean()
    ss_tot = np.sum((y - y_mean) ** 2)
    ss_res = np.sum((y - y_fit) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else np.nan

    # ---------- build stop marker series (NaN except at stop) ----------
    # find nearest index to stop_time
    idx_stop = int(np.argmin(np.abs(x - stop_time)))
    stop_mvs_plot = np.full_like(y, np.nan, dtype=float)
    stop_mvs_plot[idx_stop] = stop_mvs

    # ---------- write chart data block (J:M) ----------
    # J: time, K: mvs, L: fit_mvs, M: stop_mvs_plot
    chart_df = pd.DataFrame(
        {
            "time": x,
            "mvs": y,
            "fit_mvs": y_fit,
            "stop_mvs": stop_mvs_plot,
        }
    )
    sht["J1"].value = chart_df

    # write R^2 in a convenient place
    sht["O1"].value = "R^2"
    sht["O2"].value = float(r2)

    # ---------- create chart from chart_df ----------
    chart = sht.charts.add(
        left=sht.range("K1").left,
        top=sht.range("N1").top,
        width=500,
        height=300,
    )
    chart.name = "mvs_vs_time"
    chart.chart_type = "line"

    # set source data to the chart block (time + mvs + fit + stop)
    chart.set_source_data(sht.range("J1").expand())

    # Notes:
    # - For a line chart, Excel uses the first column (time) as the category axis
    #   and plots each of the remaining columns (mvs, fit_mvs, stop_mvs) as a series.
    # - stop_mvs is NaN everywhere except at the stopping index, so it shows as
    #   isolated markers, not a line.

    wb.save(out_path)



def print_results(res):
    if res is None:
        print("alg did not find a stopping point")

    else:
        print(res)


def safe_excel_writer(path, sheet_name):
    path = Path(path)
    file_exists = path.exists()

    if file_exists:
        # Append to existing file
        return pd.ExcelWriter(
            path, engine="openpyxl", mode="a", if_sheet_exists="overlay"
        )
    else:
        # Create new file
        return pd.ExcelWriter(
            path, engine='auto'
        )


def save_results_and_plot(
    all_data: dict | pd.DataFrame,
    stopping_data: dict,
    file_name,
    out_dir: str | Path,
    show: bool = False,
    first: bool = True,
    curr_row=0,
    cols=None
):
    """
    Save raw data to Excel and produce ONE overlaid matplotlib chart.

    Generic version:
      - First column in `cols` is treated as x-axis (e.g. time)
      - All remaining columns in `cols` are plotted vs x
      - Stopping data is expected to have the same columns
    """

    # ----- Normalize full data -----
    if isinstance(all_data, pd.DataFrame):
        if cols is None:
            cols = list(all_data.columns)
        df = all_data.loc[:, cols].copy()
    else:
        # all_data is a dict of arrays
        if cols is None:
            cols = list(all_data.keys())
        for key in cols:
            if key not in all_data:
                raise KeyError(f"Missing: {key}")
        arrs = {k: np.atleast_1d(v) for k, v in all_data.items()}
        df = pd.DataFrame(arrs)[cols]

    # ----- Normalize stopping data -----
    stop = {k: np.atleast_1d(v) for k, v in stopping_data.items()}
    df_stop = pd.DataFrame(stop)

    # make sure df_stop has ALL columns in cols; add missing ones as NaN
    for c in cols:
        if c not in df_stop.columns:
            df_stop[c] = np.nan
    #df_stop = df_stop[cols]

    # ----- Build output paths -----
    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    file_stem = Path(file_name).stem
    excel_path = out_dir / "results.xlsx"
    plot_path = out_dir / f"{file_stem}.png"

    # ----- Save Excel -----
    with safe_excel_writer(excel_path, "total") as writer:
        df.to_excel(writer, sheet_name=file_name, index=False)
        if first:
            df_stop.to_excel(writer, sheet_name="calibration", index=False)
        else:
            df_stop.to_excel(
                writer,
                sheet_name="calibration",
                index=False,
                startrow=curr_row,
                header=False,
            )

    # ----- Extract arrays -----
    x_col = cols[0]           # e.g. "time"
    y_cols = cols[1:]         # all other series to plot

    x = df[x_col].to_numpy(float)
    x_stop = df_stop[x_col].to_numpy(float)

    # ----- Plot all curves on ONE axis -----
    plt.figure(figsize=(9, 5))

    # Plot each y column
    for y_name in y_cols:
        y = df[y_name].to_numpy(float)
        plt.plot(x, y, label=y_name, linewidth=1.8)

    # stopping markers + annotations
    for y_name in y_cols:
        y_stop = df_stop[y_name].to_numpy(float)
        plt.scatter(x_stop, y_stop, s=60)

        # annotate each stopping point with its value
        for xs, ys in zip(x_stop, y_stop):
            plt.annotate(
                f"{y_name}={ys:.3f}",
                (xs, ys),
                textcoords="offset points",
                xytext=(10, 5),
                ha="left",
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", fc="yellow", alpha=0.3),
            )

    # additionally annotate time on first y series only (if present)
    if y_cols:
        first_y_name = y_cols[0]
        first_y_stop = df_stop[first_y_name].to_numpy(float)
        for xs, ys in zip(x_stop, first_y_stop):
            plt.annotate(
                f"{x_col}={xs:.3f}",
                (xs, ys),
                textcoords="offset points",
                xytext=(10, -15),
                ha="left",
                fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", fc="cyan", alpha=0.3),
            )

    plt.xlabel(x_col)
    plt.title(f"{file_stem} Full Diagnostic Chart")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(plot_path, dpi=150)
    if show:
        plt.show()

    return plt


def plot_mvs_and_std_over_time(
    parsed_files: dict,
    out_dir: str | Path | None = None,
    rolling_window: int = 10,
    apply_filter: bool = False,
):
    if out_dir is None:
        out_dir = Path.home() / "Desktop" / "mvs_std_plots"

    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    output_paths = {}
    for file_name, df in parsed_files.items():
        working_df = df.copy()
        if apply_filter:
            working_df = filter_data_for_analysis(working_df, file_name)

        working_df[TIME_COL] = pd.to_numeric(working_df[TIME_COL], errors="coerce")
        working_df[VALUE_COL] = pd.to_numeric(working_df[VALUE_COL], errors="coerce")
        working_df = working_df.dropna(subset=[TIME_COL, VALUE_COL])
        if working_df.empty:
            continue

        working_df = working_df.sort_values(TIME_COL)

        time_vals = working_df[TIME_COL]
        mvs_vals = working_df[VALUE_COL]

        rolling_std = mvs_vals.rolling(
            window=rolling_window, min_periods=rolling_window
        ).std(ddof=0)
        expanding_std = mvs_vals.expanding(min_periods=1).std(ddof=0)

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(time_vals, mvs_vals, label="mvs", color="tab:blue", linewidth=1.6)
        ax1.set_xlabel(TIME_COL)
        ax1.set_ylabel("mvs", color="tab:blue")
        ax1.tick_params(axis="y", labelcolor="tab:blue")

        ax2 = ax1.twinx()
        ax2.plot(
            time_vals,
            rolling_std,
            label=f"rolling_std_{rolling_window}",
            color="tab:orange",
            linewidth=1.4,
        )
        ax2.plot(
            time_vals,
            expanding_std,
            label="expanding_std",
            color="tab:green",
            linestyle="--",
            linewidth=1.4,
        )
        ax2.set_ylabel("std", color="tab:green")
        ax2.tick_params(axis="y", labelcolor="tab:green")

        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(handles1 + handles2, labels1 + labels2, loc="best")

        file_stem = Path(file_name).stem
        ax1.set_title(f"{file_stem} mvs + std over time")
        ax1.grid(True, linestyle="--", alpha=0.4)
        fig.tight_layout()

        plot_path = out_dir / f"{file_stem}_mvs_std.png"
        fig.savefig(plot_path, dpi=150)
        plt.close(fig)

        output_paths[file_name] = plot_path

    return output_paths


def plot_stop(out_dir, alg_params, stopping_data: pd.DataFrame):
    if stopping_data.empty:
        print("No stopping data available; skipping calibration curve.")
        return None
    time_s = stopping_data['time'].to_numpy()
    conc   = stopping_data['concentration'].to_numpy(dtype=float)

    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    file_stem = Path("calibration_curve").stem
    excel_path = out_dir / "results.xlsx"
    plot_path  = out_dir / f"{file_stem}.png"

    # ----- Exponential fit: ln C = α + β t -----
    log_conc = np.log(conc)
    beta, alpha = np.polyfit(time_s, log_conc, 1)    # slope, intercept

    # Predicted concentrations at data points
    log_conc_pred = alpha + beta * time_s
    conc_pred     = np.exp(log_conc_pred)

    # R² on concentration
    residuals = conc - conc_pred
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((conc - np.mean(conc))**2)
    r2 = 1 - ss_res / ss_tot

    # ------------------ Plot ------------------
    plt.figure(figsize=(10, 5))

    # Scatter points
    plt.scatter(time_s, conc, s=60)

    # Trendline (dotted) -- exponential model
    x_fit = np.linspace(time_s.min(), time_s.max(), 200)
    y_fit = np.exp(alpha + beta * x_fit)
    plt.plot(x_fit, y_fit, linestyle='dotted')

    # Labels and title
    plt.xlabel("Time (s)")
    plt.ylabel("Concentration of Glucose")
    plt.title(f"Calibration 1 {alg_params}")

    # Text annotation: C(t) = C0 * exp(β t)
    C0 = np.exp(alpha)
    eq_text = (
        f"C(t) = {C0:.3f}·exp({beta:.4f}·t)\n"
        f"$R^2$ = {r2:.4f}"
    )
    plt.text(time_s.mean() + 1,
             conc.min() + 1,
             eq_text)

    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xlim(time_s.min() - 1, time_s.max() + 1)
    plt.ylim(0, conc.max() + 2)

    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    # plt.show()
    return r2


def main_for_algo(spec: AlgoSpec, base_relative_path: str, final_data: dict):
    excel_path = str(Path.home()) + base_relative_path

    df_all_stopping_data = pd.DataFrame(
        columns=["mvs", "ols_rot", "std", "time", "concentration"]
    )

    is_first_iteration = True
    row = 0

    for file, data in final_data.items():
        print(f"Running {spec.name} for: {file}")
        #add maxima, minimum and tuple function
        min = None
        if 'EXP' in spec.name:
            min = get_reaction_mins(data)
        #data = filter_manual_injection_delay_by_maxima_indv(data, file)
        #data = filter_manual_injection_by_jump_greater_than_threshold(data, file, threshold=10)
        data = filter_data_for_analysis(data, file)
        data = zip_dfs_into_tuples_indv(data)
        stop_df, total_df = run_alg(spec, data, min)

        if "ols_rot" not in total_df.columns:
            total_df["ols_rot"] = np.nan
        if "std" not in total_df.columns:
            total_df["std"] = np.nan
        
        df_stop = None
        df_total = None
        if stop_df is None:
            print(f"Algorithm did not find a stopping point for this run. {file}")
            continue
        else:
            df_stop = stop_df.copy()
            df_total = total_df

        df_stop["concentration"] = file[: str(file).find("C")]
        df_all_stopping_data = pd.concat(
            [df_all_stopping_data, df_stop], ignore_index=True
        )

        save_results_and_plot(
            all_data=df_total,
            stopping_data=df_stop,
            file_name=file,
            out_dir=excel_path,
            show=False,
            first=is_first_iteration,
            curr_row=row,
        )

        if is_first_iteration:
            row += 2
            is_first_iteration = False
        else:
            row += 1

    r2 = plot_stop(out_dir=excel_path, alg_params=spec.params, stopping_data=df_all_stopping_data)
    return r2



if __name__ == '__main__':

    files = extract_files(False, DATE_FILTERS)
    plot_mvs_and_std_over_time(files)
    #files = filter_manual_injection_delay_by_maxima(files)
    #final_data = zip_dfs_into_tuples(files)
    

    avg_std_by_file = {}
    for file_name, df in files.items():
        filtered_df = filter_data_for_analysis(df, file_name)
        avg_std_by_file[file_name] = calculate_avg_std_deviation_quartiles(
            filtered_df,
        )

    r2_by_spec = {}
    for alg in RUNS:
        for spec in alg:
            out_rel = f"/Desktop/chem_e_res/{spec.func.__name__}1/{spec.name}"
            print("running params:", spec.name)
            r2 = main_for_algo(spec, out_rel, files)
            r2_by_spec[f"{spec.func.__name__} {spec.name}"] = r2
            print()
    print("R^2 by spec:", r2_by_spec)
    json_path = Path.cwd() / "r2_by_spec.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(r2_by_spec, f, indent=2)
    print(f"R^2 JSON written to {json_path}")

    std_json_path = Path.cwd() / "avg_std_by_file.json"
    with std_json_path.open("w", encoding="utf-8") as f:
        ordered_avg_std_by_file = dict(
            sorted(avg_std_by_file.items(), key=lambda item: _concentration_sort_key(item[0]))
        )
        json.dump(ordered_avg_std_by_file, f, indent=2)
    print(f"Avg std JSON written to {std_json_path}")
        
