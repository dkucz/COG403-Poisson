from pyClarion import Agent, Input, Choice, ChunkStore, Event, FixedRules, Family, Atoms, Atom, Site, FixedRules, Priority
from datetime import timedelta


class Parameters(Atoms):
    left_accumulator: Atom              # Left accumulator 
    right_accumulator: Atom             # Right accumulator
    threshold: Atom         # Threshold for activation of a choice

class IO(Atoms):
    input: Atom             
    output: Atom

# output ** decision

class Decision(Atoms):
    nil: Atom              # No choice
    left: Atom             # Left choice
    right: Atom            # Right choice

class PRWData(Family):
    parameters: Parameters
    io: IO
    decision: Decision

class AccumulationRule(FixedRules):
    def update(self, 
        dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        choice = self.choice.main[0]
        main = (self.rules.riw[0]
            .mul(choice, by=self.mul_by)
            .sum(by=self.sum_by)
            .with_default(c=self.main.const))
        td_input = (self.rules.rhw[0]
            .mul(choice)
            .sum(by=self.rules.rhs.td.input.index.kf)
            .with_default(c=self.rules.rhs.td.input.const))
        self.system.schedule(self.update, 
            self.main.update(main),
            # override this method, and instead of overwriting the chunk add to the chunk 
            self.rules.rhs.td.input.add_inplace(td_input),
            dt=dt, priority=priority)
        
    def clear(self, dt: timedelta = timedelta(), priority: int = Priority.PROPAGATION) -> None:
        choice = self.choice.main[0]
        main = (
            self.rules.riw[0]
            .mul(choice, by=self.mul_by)
            .sum(by=self.sum_by)
            .with_default(c=self.main.const))
        td_input = (self.rules.rhw[0]
            .mul(0))
        # need to update the rhs.td.input.update with an empty NumDict. 
        # Maybe must multiply td_input by 0 instead of choice?
        self.system.schedule(self.update, 
            self.main.update(main), 
            self.rules.rhs.td.input.update(td_input), 
            dt=dt, priority=priority)
        
class AccumulationRule2(FixedRules):
    accumulator: Site

    def __init__(self, name, p, r, c, d, v, *, sd = 1):
        super().__init__(name, p, r, c, d, v, sd=sd)
        self.accumulator = Site(self.rhs.td.main.index, {}, 0)

    def update_accumulator(self, 
        dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        self.system.schedule(self.update_accumulator,
            # override this method, and instead of overwriting the chunk add to the chunk 
            self.accumulator.add_inplace(self.rhs.td.main[0]),
            dt=dt, priority=priority)
        
        self.make_choice()

    # self.rhs.td.main[0] represents the data in the site currently 

    def clear_accumulator(self, dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        self.system.schedule(self.clear_accumulator, self.accumulator.push({}), dt=dt, priority=priority)

    def resolve(self, event: Event) -> None:
        super().resolve(event)
        if event.source == self.rhs.td.update:
            self.update_accumulator()

    def make_choice(self) -> None:
        curr_accumulator = self.rhs.td.main[0]

        if curr_accumulator > self.threshold:
            pass
            # select right as the choice

            self.clear_accumulator()

        if curr_accumulator < -self.threshold:
            pass
            # select left as the choice

            self.clear_accumulator()

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