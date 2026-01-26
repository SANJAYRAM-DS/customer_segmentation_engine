import numpy as np

def safe_log1p(x):
    x = np.asarray(x)
    cap = np.nanpercentile(x, 99)
    return np.log1p(np.clip(x, 0, cap))


def safe_log1p_with_caps(x, caps):
    x = np.asarray(x)
    return np.log1p(np.clip(x, 0, caps))
