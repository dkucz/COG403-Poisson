# Clarion Decision-Making Simulation

This repository contains the simulation code used in the final project report on decision-making using the Clarion cognitive architecture. The simulation models a pure accuracy task in which a Clarion-based agent categorizes left- or right-oriented Gabor patches based on repeated input over time.

## Project Overview

The agent accumulates activation for each decision category across discrete time steps. A decision is made once the accumulated activation for either category exceeds a predefined threshold. This simulates evidence accumulation without relying on explicit stochastic sampling models like the Drift Diffusion Model. All variability in response times arises from internal stochasticity in Clarion’s decision mechanism.

## Repository Structure

```css
COG403-Poisson/
├── pyClarion/
├── agent.py
├── reaction_time_dist.png
└── README.md
```

## Requirements

- Python 3.13.1
- pyClarion
- matplotlib
- seaborn
- numpy
- statistics

## Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/dkucz/COG403-Poisson.git
cd COG403-Poisson
```

2. **Activate a Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```

3. **Install Necessary Packages**

```bash
pip install -e .
```

## Running the Simulation

To generate simulation results and the reaction time plot:

```bash
python agent.py
```

This will:
- Run 200 trials of the Clarion agent.
- Record reaction times.
- Output mean, median, and standard deviation of RTs.
- Generate and save a KDE plot of the RT distribution as reaction_time_dist.png.

## Notes

- The agent always produces correct responses, so no accuracy metric is reported.
- RT variability reflects decision timing differences due to stochastic selection within the Clarion architecture.
- The threshold was manually selected to produce RTs similar to human performance in pure accuracy tasks.
