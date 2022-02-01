import pandas as pd
import numpy as np
from numpy import linalg
from pyFAST.input_output import FASTLinearizationFile

def read_out(filename):
    df = pd.read_table(filename, sep="\t", skiprows=[0, 1, 2, 3, 4, 5, 7], index_col=0, dtype=np.float64)
    units = df.iloc[0]
    df = df.iloc[1:].astype(float)
    df.index = df.index.astype(float)
    df = df[df.index >= 30]
    return df


def get_input_output_lin(lins, iu, iy, matrix="D"):
    """Get the operating point and gradient for output iy w.r.t. input iu.
    
    Averages over the azimuths."""
    
    # Operating point
    y0 = lins["y"].map(lambda y: y[iy]).unstack().T.mean()
    
    # State-space matrix from inputs to outputs
    dydu = lins[matrix].map(lambda D: D[iy, iu]).unstack().T.mean()

    return y0, dydu


def load_lins(simulation_name, wind_speeds, run_name):
    lins = pd.DataFrame.from_dict({
        (wind_speed, i_azimuth): FASTLinearizationFile(
            f"../runs/{simulation_name}/ws{wind_speed:0.1f}/{run_name}.{i_azimuth}.lin"
        )
        for wind_speed in wind_speeds
        for i_azimuth in range(1, 13)
    }, orient="index")
    return lins


def print_state(X, lins):
    for i in range(len(X)):
        print(f"{abs(X[i]): 7.2f} @ {np.angle(X[i], deg=True): >4.0f}º "
              f"{lins.iloc[0]['x_info']['Description'][x_idx[i]]}")
        
        
def harmonic_timeseries(w, X):
    T = 2 * np.pi / w
    t = np.linspace(0, T, 100)
    return t, np.real(X[:, np.newaxis] * np.exp(1j * w * t[np.newaxis, :]))