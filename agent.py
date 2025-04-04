from pyClarion import Agent, Input, Choice, FixedRules, Family, Atoms, Atom, Site, FixedRules, Priority, Process, keyform
from datetime import timedelta

class IO(Atoms):
    input: Atom             
    output: Atom

class Direction(Atoms):
    left: Atom             # Left choice
    right: Atom            # Right choice

class PRWData(Family):
    io: IO
    direction: Direction

###################################################### Accumulator Class

class Accumulator(Process):
    main: Site
    input: Site
    lax = ("input",)

    def __init__(self, name, d, v, threshold):
        super().__init__(name)
        self.system.check_root(d, v)
        idx_d = self.system.get_index(keyform(d))
        idx_v = self.system.get_index(keyform(v))
        self.main = Site(idx_d * idx_v, {}, 0)
        self.input = Site(idx_d * idx_v, {}, 0)
        self.threshold = threshold

    def update(self, 
        dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        
        main = self.main[0].sum(self.input[0])

        self.system.schedule(self.update,
            self.main.update(main,),
            dt=dt, priority=priority)

    def clear(self, dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        self.system.schedule(self.clear, self.main.update({}), dt=dt, priority=priority)

    def above_threshold(self, dt: timedelta = timedelta(), priority: int = Priority.PROPAGATION) -> None:
        self.system.schedule(self.above_threshold, dt=dt, priority=priority)

    def resolve(self, event) -> None:
        updates = [ud for ud in event.updates if isinstance(ud, Site.Update)]

        if self.input.affected_by(*updates):
            self.update()

        if event.source == self.update and self.main[0].max().c > self.threshold:
            print("ABOVE THRESHOLD")
            self.above_threshold()

############################################## Accumulation Agent Class

class AccumulationAgent(Agent):
    accumulator: Accumulator
    data_in: Input
    choice: Choice
    fixed_rules: FixedRules

    def __init__(self, name, **families):
        super().__init__(name, **families)

        with self:
            self.data_in = Input("data_in", (data, data))
            self.fixed_rules = FixedRules("fixed_rules", p=p, r=data, c=data, d=data, v=data, sd=1e-4)
            self.choice = Choice('choice', p, (data.io.output, data.direction), sd=1e-4)
            self.accumulator = Accumulator("accumulator", data.io.output, data.direction, threshold=4)
            self.fixed_rules.rules.lhs.bu.input = self.data_in.main
            self.accumulator.input = self.fixed_rules.rules.rhs.td.main
            self.choice.input = self.accumulator.main

    def resolve(self, event):
        if event.source == agent.accumulator.above_threshold:
            self.choice.select()
        
        if event.source == self.choice.select:
            self.accumulator.clear()

p = Family()
data = PRWData()
agent = AccumulationAgent("agent", d=data, p=p)

io = data.io
direction = data.direction

rule_defs = [
    + io.input ** direction('X')
    >>
    + io.output ** direction("X")
]

trials = [
    + io.input ** direction.left,

    + io.input ** direction.right
]

agent.fixed_rules.rules.compile(*rule_defs)

trial_one = trials.pop(0)

agent.data_in.send(trial_one)

agent.fixed_rules.trigger()

results = []

steps = 0

while agent.system.queue and steps < 40:
    steps += 1
    event = agent.system.advance()
    print(event)
    if event.source == agent.choice.select:
        results.append((event.time, agent.choice.poll()))
    if event.source == agent.fixed_rules.trigger:
        print("TRIGGERING FIXED RULES AGAIN")
        agent.fixed_rules.trigger(dt=timedelta(0, 0, 0, 50))

print(agent.fixed_rules.rules.rhs.td.main[0])
print(agent.accumulator.main[0])
print(f"Results: {results}")


# I don't get a result