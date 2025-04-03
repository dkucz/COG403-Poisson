from pyClarion import Agent, Input, Choice, ChunkStore, Event, FixedRules, Family, Atoms, Atom, Site, FixedRules, Priority
from datetime import timedelta


# class Parameters(Atoms):
#     left_accumulator: Atom              # Left accumulator 
#     right_accumulator: Atom             # Right accumulator
#     threshold: Atom         # Threshold for activation of a choice

class IO(Atoms):
    input: Atom             
    output: Atom

# output ** decision

class Direction(Atoms):
    left: Atom             # Left choice
    right: Atom            # Right choice

class PRWData(Family):
    io: IO
    direction: Direction

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

    def __init__(self, name, p, r, c, d, v, *, sd = 1, threshold):
        super().__init__(name, p, r, c, d, v, sd=sd)
        self.accumulator = Site(self.rules.rhs.td.main.index, {}, 0)
        self.threshold = threshold

    def update_accumulator(self, 
        dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        print("updating accumulator")
        self.system.schedule(self.update_accumulator,
            self.accumulator.update(self.rules.rhs.td.main[0], method=Site.add_inplace),
            dt=dt, priority=priority)

    # self.rhs.td.main[0] represents the data in the site currently 

    def clear_accumulator(self, dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        self.system.schedule(self.clear_accumulator, self.accumulator.update({}), dt=dt, priority=priority)

    def resolve(self, event: Event) -> None:
        super().resolve(event)
        if event.source == self.rules.rhs.td.update:
            self.update_accumulator()
        
        if event.source == self.update_accumulator:
            curr_accumulator = self.rules.rhs.td.main[0]

            if curr_accumulator.max().c > self.threshold:
                self.choice.select()
                # this causes further event updates and this ruins everything
                # as the choice process or whatever schedules an update in the topdown section
                # which triggers update accumulator
                # and then this loops

        if event.source == self.choice.select:
            self.clear_accumulator()

p = Family()
data = PRWData()
with Agent('agent', d=data, p=p) as agent:
    data_in = Input("data_in", (data, data))
    accumulation_rules = AccumulationRule2("accumulation_rules", p=p, r=data, c=data, d=data, v=data, sd=1e-4, threshold=10)
    choice = Choice('choice', p, (data.io.input, data.direction), sd=1e-4)
    accumulation_rules.rules.lhs.bu.input = data_in.main
    choice.input = accumulation_rules.rules.rhs.td.main

io = data.io
direction = data.direction

rule_defs = [
    + io.input ** direction('X')
    >>
    + io.output ** direction("X")
]

trials = [
    +0.5 * io.input ** direction.left,

    + io.input ** direction.right
]

results = []

dt = timedelta(seconds=1)

accumulation_rules.rules.compile(*rule_defs)

trial_one = trials.pop(0)

data_in.send(trial_one)

accumulation_rules.trigger()

steps = 0

while agent.system.queue:
    steps += 1
    event = agent.system.advance()
    print(event)
    if event.source == accumulation_rules.choice.select:
        results.append((event.time, choice.poll()))
    # else:
    #     data_in.send(trial_one)

# while agent.system.queue:
#     event = agent.system.advance()
#     if not agent.system.queue:
#         data_in.send(trial_one, dt=dt)
#         accumulation_rules.trigger(dt=dt)
#     print(accumulation_rules.rules.rhs.td.main[0].max())
#     if event.source == choice.select:
#         results.append((event.time, choice.poll()))

print("\n")
for i in range(len(results)):
    print(f"Found the following data at position {i}: {results[i]} \n")


# for time, actions in results:
#     print(time, actions)