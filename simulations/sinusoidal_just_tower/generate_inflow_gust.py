#!/usr/bin/env python3

"""Generate an OpenFAST InflowWind uniform wind file with a sinusoidal gust

The file can start with comments, then the following space/tab/comma delimited
data:

Column Description Units
1 Tdat Time s
2 Vh_ref Horizontal wind speed at RefHt |vectorial u+v| m/s
3 Delta Wind direction, positive clockwise looking down deg
4 VZ Vertical wind speed (w component) m/s
5 HLinShr Horizontal linear wind-shear parameter -
6 VShr Vertical power-law wind-shear exponent -
7 VLinShr Vertical linear wind-shear parameter -
8 VGust Horizontal gust speed m/s

"""

import numpy as np


def write_uniform_gust(output_filename, t, v_gust, header=""):
    """Write just the gust element of a uniform inflow file.#

    The gust is not subject to wind shear or direction.
    """

    Vh_ref = np.zeros_like(t)
    Delta = np.zeros_like(t)
    VZ = np.zeros_like(t)
    HLinShr = np.zeros_like(t)
    VShr = np.zeros_like(t)
    VLinShr = np.zeros_like(t)
    assert len(v_gust) == len(t), "array lengths must match"
    columns = np.c_[t, Vh_ref, Delta, VZ, HLinShr, VShr, VLinShr, v_gust]

    np.savetxt(output_filename, columns, header=header)


def sinusoidal_wind(mean, amplitude, frequency, tmax, n=100):
    """Generate sinusoidal curve at given frequency (rad/s)"""
    period = 2 * np.pi / frequency
    t = np.linspace(0, tmax, round(n * tmax / period))
    v = mean + amplitude * np.sin(frequency * t)
    return t, v


if __name__ == "__main__":
    tmax = 700
    write_uniform_gust("wind_8ms_0.1ms_0.1rads.wnd", *sinusoidal_wind(8, 0.1, 0.1, tmax))
    write_uniform_gust("wind_8ms_1ms_0.1rads.wnd", *sinusoidal_wind(8, 1, 0.1, tmax))
    write_uniform_gust("wind_8ms_1ms_1rads.wnd", *sinusoidal_wind(8, 1, 1, tmax))
    write_uniform_gust("wind_8ms_2ms_1rads.wnd", *sinusoidal_wind(8, 2, 1, tmax))
    write_uniform_gust("wind_8ms_3ms_1rads.wnd", *sinusoidal_wind(8, 3, 1, tmax))
    write_uniform_gust("wind_8ms_4ms_1rads.wnd", *sinusoidal_wind(8, 4, 1, tmax))
    write_uniform_gust("wind_8ms_5ms_1rads.wnd", *sinusoidal_wind(8, 5, 1, tmax))
    write_uniform_gust("wind_8ms_6ms_1rads.wnd", *sinusoidal_wind(8, 6, 1, tmax))
    write_uniform_gust("wind_8ms_7ms_1rads.wnd", *sinusoidal_wind(8, 7, 1, tmax))
