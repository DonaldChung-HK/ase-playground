"""This test ensures that logging to a text file and to the trajectory file are
reporting the same values as in the ContourExploration object."""

import pytest
from ase.lattice.cubic import FaceCenteredCubic
from ase.md.contour_exploration import ContourExploration
import numpy as np
from ase.calculators.emt import EMT
from ase import io


def test_logging():

    size = 2
    md_temp = 300
    seed = 19460926

    atoms = FaceCenteredCubic(directions=[[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                              symbol='Al',
                              size=(size, size, size),
                              pbc=True)

    atoms.calc = EMT()
    atoms.rattle(stdev=0.18, seed=seed)

    rng = np.random.RandomState(seed)

    initial_energy = atoms.get_potential_energy()

    name = 'test_logging'
    traj_name = name + '.traj'
    log_name = name + '.log'

    dyn = ContourExploration(atoms,
                             maxstep=1.0,
                             parallel_drift=0.05,
                             remove_translation=True,
                             force_parallel_step_scale=None,
                             use_fs=True,
                             angle_limit=20,
                             loginterval=1,
                             initialize_old=True,
                             rng=rng,
                             trajectory=traj_name,
                             logfile=log_name,
                             )

    energy_target = initial_energy
    dev = (atoms.get_potential_energy() - energy_target) / len(atoms)
    energy_targets = [energy_target]
    kappas = [dyn.kappa]
    stepsizes = [dyn.step_size]
    deviation_per_atom = [dev]

    # we shift the target_energy to ensure it's actaully being logged when it
    # changes.
    de = 0.001 * len(atoms)

    # these print statements, mirror the log file.
    #print(energy_target, dyn.kappa, dyn.step_size, dev)

    for i in range(0, 5):
        energy_target = initial_energy + de * i

        dyn.energy_target = energy_target
        dyn.run(1)
        dev = (atoms.get_potential_energy() - energy_target) / len(atoms)
        #print(energy_target, dyn.kappa, dyn.step_size, dev)

        energy_targets.append(energy_target)
        kappas.append(dyn.kappa)
        stepsizes.append(dyn.step_size)
        deviation_per_atom.append(dev)

    # Now we check the contents of the log file
    # assert log file has correct length
    with open(log_name) as fd:
        length = len(fd.readlines())
    assert length == 7, length

    with io.Trajectory(traj_name, 'r') as traj, open(log_name, 'r') as fd:
        # skip the first line because it's a small initialization step
        lines = fd.readlines()[1:]
        for i, (im, line) in enumerate(zip(traj, lines)):

            log_energy_target = float(line.split()[1])
            assert np.allclose(log_energy_target, energy_targets[i], atol=1e-5)

            log_energy = float(line.split()[2])
            assert np.allclose(log_energy, im.get_potential_energy(), atol=1e-5)

            log_kappa = float(line.split()[3])
            assert np.allclose(log_kappa, kappas[i], atol=1e-5)

            log_step_size = float(line.split()[4])
            assert np.allclose(log_step_size, stepsizes[i], atol=1e-5)

            log_dev = float(line.split()[5])
            assert np.allclose(log_dev, deviation_per_atom[i], atol=1e-5)
