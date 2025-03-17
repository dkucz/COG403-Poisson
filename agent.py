from pyClarion import Atom, Atoms

class Parameters(Atoms):
    lambda_left: Atom       # Poisson rate for left option
    lambda_right: Atom      # Poisson rate for right option
    sd: Atom                # Standard deviation
    threshold: Atom         # Threshold for activation of a choice

class IO(Atoms):
    input: Atom             
    output: Atom

class Decision(Atoms):
    left: Atom             # Sum to one for a left choice
    right: Atom            # Sum to one for a right choice