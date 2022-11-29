# OpenFAST simulations for the NREL 5MW turbine

This repository contains the data files and code to run simple simulations of
the NREL 5MW wind turbine using the OpenFAST simulation code.

## Simulations

Simulations are defined in subfolders of `simulations/`. You can add more variations by adding addition `.fst` files within an existing subfolder, or by creating a new subfolder. More details below.

### Baseline turbulent wind simulations

`baseline` at 12 m/s and `baseline_8ms` at 8 m/s

### Alternative controller

To demonstrate an [arbitrary] change to the controller code, the `controller_tweaked` simulations are the same as the `baseline` simulations but they use the `DISCON_tweaked` controller.

### Linearised models

- `linearised`
- `lineared_fixed_rotor_speed` -- how is this different from `linearised/trim_none_no_gen_dof`? I think it's not used?
- `linearised_trim_torque` -- think this is not used`

### Sinusoidal wind input

### Steady wind

- `steady_wind`
- `steady_wind_simplified` has only the generator speed and 1 tower mode active

## Analysis / results

The following Jupyter notebooks are in the `analysis/` folder.

### Results - compare turbulent to linearisation

Compares the results of
- `baseline_8ms/5MW_Land_DLL_WTurb_fixedspeed_toweronly`
- `linearised/trim_none_no_gen_dof`

### Results - compare sinusoidal to linearisation

Compares the results of
- `sinusoidal_just_tower_no_gen_dof`
- `sinusoidal_just_tower`
- (`sinusoidal_no_tower_no_gen_dof` -- TODO this doesn't exist yet)
- `linearised/trim_none_equilib`
- `linearised/trim_none_no_gen_dof`
- `linearised/trim_none_no_gen_dof_no_tower`

This shows for a simple condition with just 1 or 2 degrees of freedom how the linearised state-space model compares to the non-linear time-domain solution with sinusoidal uniform wind input.

### Effect of neglecting blade dynamics

Comparison between `baseline_8ms/5MW_Land_DLL_WTurb` and `baseline_8ms/5MW_Land_DLL_WTurb_nobladedof` 

(just as an example of how the results differ if we arbitrarily simplify the model by neglecting the flexibility of the blades)

### Results - steady state

Plots the results of `steady_wind` simulations

### Compare tweaked controller to original

Plots the results of the `baseline` simulations with the original controller against equivalent simulations `controller_tweaked` with the `DISCON_tweaked` controller.

## Installation

Use [conda](https://docs.conda.io/en/latest/) to install the Python packages to set up and analyse the simulations. All the necessary packages *should* (...) be listed in the `environment.yml` conda file, so all that should be necessary is to run in this folder:

``` shellsession
conda env create
conda activate openfast_env
```

Each time you open a new terminal, you need to re-run the `conda activate openfast_env` command to activate that conda environment.

### Installing OpenFAST on Mac OS

On Mac OS, the [OpenFAST](https://github.com/OpenFAST/openfast/) wind turbine simulation software can also be installed with conda. With your `openfast_env` conda environment activated, run

```shell
conda install -c conda-forge openfast
```

### Installing OpenFAST on Windows

On Windows, OpenFAST is not available via conda so must be downloaded directly from the [GitHub releases page](https://github.com/OpenFAST/openfast/releases/tag/v3.3.0). Download the following files and save them in the same directory as this project.

- `openfast_x64.exe`, saved as `openfast.exe`
- `TurbSim_x64.exe`, saved as `turbsim.exe`

## Running simulations

Simulations are managed using [doit](https://pydoit.org/) to keep track of which simulations need to be re-run when input parameters change, and to create sets of simulations (with different wind speeds, or different realisations of a turbulent wind field).

Basically, each subfolder of `simulations/` is copied into `runs/...` including any necessary variations. Then OpenFAST is run for each generated folder in `runs/`. The generation of variations is defined somewhat messily in the function `task_prepare_fast_input` within `dodo.py`.

Other doit tasks take care of:
- Generating turbulent wind field files based on the input parameters in the `wind/` folder
- Compiling the controller code into a DLL file for use within the simulations

You can run all out-of-date simulations using `doit run -v2 -n5`. Here `-v2` tells doit to print all output to the console (you can skip this if you want to see less detail). `-n5` tells doit to run up to 5 tasks in parallel; again you can skip this. 

You can list all the available tasks by running `doit list`, and then see subtasks by running `doit info TASK`. For example one of the subtasks listed by `doit info openfast` is `openfast:steady_wind:ws4.0:5MW_Land_DLL_Steady` which runs the simulation defined in `simulations/steady_wind/5MW_Land_DLL_Steady.fst`, placing the output in `runs/steady_wind/ws4.0/5MW_Land_DLL_Steady.out`.
