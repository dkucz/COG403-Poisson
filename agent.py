from pyClarion import Agent, Input, Choice, FixedRules, Family, Atoms, Atom, Site, FixedRules, Priority, Process, keyform
from datetime import timedelta
import statistics
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


# Define atoms and structure
class IO(Atoms):
    input: Atom             
    output: Atom

class Direction(Atoms):
    left: Atom
    right: Atom

class PRWData(Family):
    io: IO
    direction: Direction

# Accumulator process for top-down integration
class Accumulator(Process):
    """
    Accumulates activation over time from repeated input signals.
    Once the total activation surpasses a threshold, it signals decision readiness.
    """
    main: Site
    input: Site
    lax = ("input",)

    def __init__(self, name, d, v, threshold):
        """
        Initialize a new Accumulation process. 
        """
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
        """
        Adds current input to accumulated value and schedules the next update.
        """
        
        main = self.main[0].sum(self.input[0])

        self.system.schedule(self.update,
            self.main.update(main,),
            dt=dt, priority=priority)

    def clear(self, dt: timedelta = timedelta(), 
        priority: int = Priority.PROPAGATION
    ) -> None:
        """
        Clears the accumulator for the next trial.
        """
        self.system.schedule(self.clear, self.main.update({}), dt=dt, priority=priority)

    def above_threshold(self, dt: timedelta = timedelta(), priority: int = Priority.PROPAGATION) -> None:
        """
        Signals that the threshold has been crossed.
        """
        self.system.schedule(self.above_threshold, dt=dt, priority=priority)

    def resolve(self, event) -> None:
        """
        Handles incoming events and triggers updates. Also triggers an above_threshold check 
        if an accumulation site reaches the threshold.
        """
        updates = [ud for ud in event.updates if isinstance(ud, Site.Update)]

        if self.input.affected_by(*updates):
            self.update()

        if event.source == self.update and self.main[0].max().c > self.threshold:
            self.above_threshold()


# Agent with Clarion modules
class AccumulationAgent(Agent):
    """
    A Clarion agent that accumulates evidence from input chunks and makes decisions based on a threshold.
    """
    accumulator: Accumulator
    data_in: Input
    choice: Choice
    fixed_rules: FixedRules

    def __init__(self, name, **families):
        """
        Initialize a new pyClarion Agent with Accumulation.
        """
        super().__init__(name, **families)

        with self:
            self.data_in = Input("data_in", (data, data))
            self.fixed_rules = FixedRules("fixed_rules", p=p, r=data, c=data, d=data, v=data, sd=0.2)
            self.choice = Choice('choice', p, (data.io.output, data.direction), sd=0.2)
            self.accumulator = Accumulator("accumulator", data.io.output, data.direction, threshold=4)
            self.fixed_rules.rules.lhs.bu.input = self.data_in.main
            self.accumulator.input = self.fixed_rules.rules.rhs.td.main
            self.choice.input = self.accumulator.main

    def resolve(self, event):
        """
        Handles event triggering and resets for new trials.
        """
        if event.source == agent.accumulator.above_threshold:
            self.choice.select()
        
        if event.source == self.choice.select:
            agent.system.queue.clear()
            self.accumulator.clear()


# Initialize agent and model components
p = Family()
data = PRWData()
agent = AccumulationAgent("agent", d=data, p=p)

io = data.io
direction = data.direction

# Define decision rules
rule_defs = [
    + io.input ** direction('X')
    >>
    + io.output ** direction("X")
]

# Generate 200 trials (100 per category)
trials = (
    [+ io.input ** direction.left for _ in range(100)] +
    [+ io.input ** direction.right for _ in range(100)]
)

agent.fixed_rules.rules.compile(*rule_defs)

results = []

dt = timedelta(seconds=1)

# Run simulation across all trials
for trial in trials:
    agent.accumulator.clear()

    agent.data_in.send(trial)

    agent.fixed_rules.trigger(dt=timedelta(seconds=1))

    while agent.system.queue:
        event = agent.system.advance()

        if event.source == agent.choice.select:
            results.append((event.time, agent.choice.poll()))
            break

        if event.source == agent.fixed_rules.trigger:
            agent.fixed_rules.trigger(dt=timedelta(0, 0, 0, 50))

# Compute reaction times based on stimulus-to-decision timing
rts = []
last_end_time = timedelta(seconds=0)

for (end_time, _) in results:
    trial_start_time = last_end_time + timedelta(seconds=1)
    rt = (end_time - trial_start_time).total_seconds()
    rts.append(rt)
    last_end_time = end_time

# Add residual motor time
for i in range(len(rts)):
    rts[i] = rts[i] + 0.239

# Print RT statistics
mean_rt = statistics.mean(rts)
median_rt = statistics.median(rts)
stdev_rt = statistics.stdev(rts)

print(f"Mean RT: {mean_rt:.3f} seconds")
print(f"Median RT: {median_rt:.3f} seconds")
print(f"Standard Deviation: {stdev_rt:.3f} seconds")

min_rt = min(rts)
max_rt = max(rts)
print(f"Min RT: {min_rt:.3f}s, Max RT: {max_rt:.3f}s")

# Plot RT distribution
plt.figure(figsize=(8, 5))
sns.kdeplot(rts, fill=True, linewidth=2)
plt.title("Reaction Time Distribution")
plt.xlabel("RT (seconds)")
plt.ylabel("Density")
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.axvline(np.mean(rts), color='red', linestyle='--', label=f"Mean RT: {np.mean(rts):.3f}s")
plt.legend()
plt.savefig("reaction_time_kde.png")
plt.close()