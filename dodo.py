#!/usr/bin/env python3

from doit import create_after
from doit.action import CmdAction
from pathlib import Path
import shutil
from subprocess import run
import re

############################################################
# Settings
############################################################

NUM_SEEDS = 1
STEADY_WIND_SPEEDS = [4, 6, 8, 10, 11.5, 12.5, 14, 16]


############################################################
# Input file rewriting helpers
############################################################

def copy_input_file_with_subs(source, target, subs):
    """Copy the given source file to target, making substitutions.

    subs should be a list of (regex, value, expected_number) tuples.
    """
    with open(source, "rt") as fin:
        result = fin.read()
    for regex, value, expected_number in subs:
        result, nsubs = regex.subn(value, result)
        if expected_number is not None and nsubs != expected_number:
            raise ValueError(f"Found {nsubs} match but expected {expected_number} in {source}: {regex}")

    tgt = Path(target)
    tgt.parent.mkdir(parents=True, exist_ok=True)
    with open(tgt, "wt") as fout:
        fout.write(result)

############################################################
# Sinusoidal wind files
############################################################

# The input data are hard coded in the `generate_inflow_gust.py` file in each
# simulation folder.

def clean_sinusoidal_wind_files(targets):
    print("XXX", targets)
    for target in targets:
        print("XXX", target)
        # target.unlink()


def task_sinusoidal_wind_files():
    for script_file in Path("simulations").rglob("generate_inflow_gust.py"):
        targets = [p.with_suffix(".wnd") for p in script_file.parent.glob("wind*.fst")]
        yield {
            "name": script_file.parent.name,
            "file_dep": [script_file],
            "targets": targets,
            "actions": [CmdAction(["python", script_file.name],
                                  shell=False,
                                  cwd=script_file.parent)],
            "clean": [(clean_sinusoidal_wind_files, targets)]
        }


############################################################
# Turbulent wind files
############################################################

RANDSEED1_REGEX = re.compile(r"^[0-9]+([ \t]+RandSeed1)", re.MULTILINE)

def copy_wind_input_file_with_seed(seed, dependencies, targets):
    copy_input_file_with_subs(dependencies[0], targets[seed], [
        (RANDSEED1_REGEX, f"{13420+seed}\\1", 1),
    ])


def task_prepare_wind_input():
    for input_file in Path("wind").glob("*.inp"):
        yield {
            "name": input_file.stem,
            "file_dep": [input_file],
            "targets": [
                Path("runs/wind_seeds") / f"{input_file.stem}_seed{i:02d}.inp"
                for i in range(NUM_SEEDS)
            ],
            "actions": [
                (copy_wind_input_file_with_seed, [i], {})
                for i in range(NUM_SEEDS)
            ],
        }


@create_after(executed="prepare_wind_input", target_regex=r"runs/wind_seeds/.*\.bts")
def task_turbsim():
    for p in Path("runs/wind_seeds").glob("*.inp"):
        yield {
            "name": p.stem,
            "file_dep": [p],
            "targets": [p.with_suffix(".bts")],
            "actions": [["turbsim", p]],
        }


############################################################
# Controller
############################################################


def prepare_discon_compilation(discon_folder : Path):
    """Set up CMake files for the given discon folder."""
    build_folder = discon_folder / "build"
    build_folder.mkdir(exist_ok=True)
    run(["cmake", ".."], cwd=build_folder)


def clean_discon_compilation():
    for build_dir in Path("controller").glob("*/build"):
        shutil.rmtree(build_dir)


def task_prepare_discon_compilation():
    controller_subfolders = [x for x in Path("controller").iterdir() if x.is_dir()]
    for discon_folder in controller_subfolders:
        yield {
            "name": discon_folder.name,
            "file_dep": [discon_folder / "CMakeLists.txt"],
            "targets": [discon_folder / "build" / "Makefile"],
            "actions": [(prepare_discon_compilation, [discon_folder], {})],
            "clean": [clean_discon_compilation],
        }


def task_compile_discon():
    controller_subfolders = [x for x in Path("controller").iterdir() if x.is_dir()]
    for discon_folder in controller_subfolders:
        yield {
            "name": discon_folder.name,
            "file_dep": [
                discon_folder / "build" / "Makefile",
                discon_folder / "DISCON.F90"
            ],
            "targets": [discon_folder / "build" / "DISCON.dll"],
            "actions": [CmdAction("make", cwd=discon_folder / "build")],
        }


############################################################
# Simulations
############################################################



FILENAME_BTS_REGEX = re.compile(r'^"[^"]+"([ \t]+FileName_BTS )', re.MULTILINE)
HWINDSPEED_REGEX = re.compile(r'^[ \t]*[0-9.]+([ \t]+HWindSpeed )', re.MULTILINE)
ROTSPEED_REGEX = re.compile(r'^[ \t]*[0-9.]+([ \t]+RotSpeed )', re.MULTILINE)


def copy_fast_input_files_with_seed(source_files, target_folder, seed):
    for source in source_files:
        if source.suffix == ".dat" and "InflowWind" in source.name:
            subs = [
                (FILENAME_BTS_REGEX, f'"../../../runs/wind_seeds/90m_12mps_twr_seed{seed:02d}.bts"\\1', 1),
            ]
        else:
            subs = []
        copy_input_file_with_subs(source, target_folder / source.name, subs)


def copy_fast_input_files_with_steady_wind(source_files, target_folder, wind_speed):
    for source in source_files:
        if source.suffix == ".dat" and "InflowWind" in source.name:
            subs = [
                (HWINDSPEED_REGEX, f'{wind_speed:02.1f}\\1', 1),
            ]
        else:
            subs = []
        copy_input_file_with_subs(source, target_folder / source.name, subs)


def copy_fast_input_files_with_rotor_speed(source_files, target_folder, rotor_speed):
    for source in source_files:
        if source.suffix == ".dat" and "ElastoDyn" in source.name and "Tower" not in source.name:
            subs = [
                (ROTSPEED_REGEX, f'{rotor_speed:02.1f}\\1', 1),
            ]
        else:
            subs = []
        copy_input_file_with_subs(source, target_folder / source.name, subs)


def clean_fast_run(simulation_folder):
    print("CLEAN", simulation_folder)
    shutil.rmtree(simulation_folder)


def task_prepare_fast_input():
    simulation_subfolders = [x for x in Path("simulations").iterdir() if x.is_dir()]
    for simulation_folder in simulation_subfolders:
        target_folder = Path("runs") / simulation_folder.name
        deps = list(simulation_folder.glob("*"))
        if simulation_folder.name.startswith("steady_wind"):
            yield {
                "name": simulation_folder.name,
                "file_dep": deps,
                "targets": [
                    target_folder / f"ws{ws:0.1f}" / p.name
                    for ws in STEADY_WIND_SPEEDS
                    for p in deps
                ],
                "actions": [
                    (copy_fast_input_files_with_steady_wind, [deps, target_folder / f"ws{ws:0.1f}", ws], {})
                    for ws in STEADY_WIND_SPEEDS
                ],
                "clean": [
                    (clean_fast_run, [target_folder / f"ws{ws:0.1f}"])
                    for ws in STEADY_WIND_SPEEDS
                ]
            }
        elif simulation_folder.name.startswith(("linearised",
                                                "sinusoidal")):
            LIN_WIND_SPEEDS = [8]
            LIN_ROTOR_SPEEDS = [8.5, 9.0, 9.5, 10.0, 10.5]
            if simulation_folder.name == "linearised_fixed_rotor_speed":
                yield {
                    "name": simulation_folder.name,
                    "file_dep": deps,
                    "targets": [
                        target_folder / f"rotor{rotor_speed:0.1f}" / p.name
                        for rotor_speed in LIN_ROTOR_SPEEDS
                        for p in deps
                    ],
                    "actions": [
                        (copy_fast_input_files_with_rotor_speed, [deps, target_folder / f"rotor{rotor_speed:0.1f}", rotor_speed], {})
                        for rotor_speed in LIN_ROTOR_SPEEDS
                    ],
                    "clean": [
                        (clean_fast_run, [target_folder / f"rotor{rotor_speed:0.1f}"])
                        for rotor_speed in LIN_ROTOR_SPEEDS
                    ]
                }
            else:
                yield {
                    "name": simulation_folder.name,
                    "file_dep": deps,
                    "targets": [
                        target_folder / f"ws{ws:0.1f}" / p.name
                        for ws in LIN_WIND_SPEEDS
                        for p in deps
                    ],
                    "actions": [
                        (copy_fast_input_files_with_steady_wind, [deps, target_folder / f"ws{ws:0.1f}", ws], {})
                        for ws in LIN_WIND_SPEEDS
                    ],
                    "clean": [
                        (clean_fast_run, [target_folder / f"ws{ws:0.1f}"])
                        for ws in LIN_WIND_SPEEDS
                    ]
                }
        else:
            yield {
                "name": simulation_folder.name,
                "file_dep": deps,
                "targets": [
                    target_folder / f"seed{i:02d}" / p.name
                    for i in range(NUM_SEEDS)
                    for p in deps
                ],
                "actions": [
                    (copy_fast_input_files_with_seed, [deps, target_folder / f"seed{i:02d}", i], {})
                    for i in range(NUM_SEEDS)
                ],
            }


DEPENDENCY_REGEX = re.compile(r'^"([^"]+\.(dat|dll|bts))".*', re.MULTILINE)

def get_fast_dependencies(path):
    # Find everything that looks like a filename
    if path.suffix not in (".dat", ".fst"):
        return []
    deps = [
        (path.parent / match.group(1)).resolve()
        for match in DEPENDENCY_REGEX.finditer(path.read_text())
    ]
    return deps + [subdep for dep in deps for subdep in get_fast_dependencies(dep)]


@create_after(executed="prepare_fast_input", target_regex=r"runs/.*/.*\.out")
def task_openfast():
    # Make a task for each kind of simulation
    for p in Path("runs").glob("*"):
        variants = {v: runs for v in p.iterdir() if (runs := list(v.glob("*.fst")))}
        if not variants:
            continue

        # Parent task to run all variants (seeds / windspeeds) of a simulation
        yield {
            "name": p.name,
            "task_dep": [f"openfast:{p.name}:{v.name}" for v in variants],
            "actions": [],
        }

        # Now for each variant...
        for v, runs in variants.items():
            # Parent task to run all seeds of a simulation
            yield {
                "name": f"{p.name}:{v.name}",
                "task_dep": [f"openfast:{p.name}:{v.name}:{r.stem}" for r in runs],
                "actions": [],
            }

            # Individual tasks to actually run each run
            for r in runs:
                yield {
                    "name": f"{p.name}:{v.name}:{r.stem}",
                    "file_dep": [r] + get_fast_dependencies(r),
                    "targets": [r.with_suffix(".out")],
                    "actions": [["openfast", r]],
                }
