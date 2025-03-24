from pyClarion import Agent, Input, Choice, ChunkStore, FixedRules, Family, Atoms, Atom, FixedRules

class Parameters(Atoms):
    left: Atom              # Left accumulator 
    right: Atom             # Right accumulator
    threshold: Atom         # Threshold for activation of a choice

class IO(Atoms):
    input: Atom             
    output: Atom

class Decision(Atoms):
    left: Atom             # Sum to one for a left choice
    right: Atom            # Sum to one for a right choice

class PRWData(Family):
    parameters: Parameters
    io: IO
    decision: Decision

data = PRWData()
with Agent('agent', d=data) as agent:
    data_in = Input("data_in", d=data, v=data)
    chunks = ChunkStore("chunks", c=data, d=data, v=data)
    chunks.bu.input = data_in.main

io = data.io
parameters = data.parameters

chunk_defs = [
    + io.input ** parameters.left,
    - io.input ** parameters.right
]