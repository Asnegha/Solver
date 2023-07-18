from flask import Flask, render_template
# import pandas as pd
# from pylab import *
# import matplotlib
# import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import numpy as np

app = Flask(__name__)


@app.route("/")
def hello_world():
  shifts, shiftRequirements = gp.multidict({
    "Mon1": 3,
    "Tue2": 2,
    "Wed3": 4,
    "Thu4": 4,
    "Fri5": 5,
    "Sat6": 6,
    "Sun7": 5,
    "Mon8": 2,
    "Tue9": 2,
    "Wed10": 3,
    "Thu11": 4,
    "Fri12": 6,
    "Sat13": 7,
    "Sun14": 5
  })
  # ...
  # Amount each worker is paid to work one shift.
  # Amount each worker is paid to work one shift.
  workers, pay = gp.multidict({"Amy": 10, "Bob": 12, "Cathy": 10, "Dan": 8})

  # Worker availability: defines on which day each employed worker is available.

  # Worker availability: defines on which day each employed worker is available.

  availability = gp.tuplelist([
    ('Amy', 'Tue2'), ('Amy', 'Wed3'), ('Amy', 'Fri5'), ('Amy', 'Sun7'),
    ('Amy', 'Tue9'), ('Amy', 'Wed10'), ('Amy', 'Thu11'), ('Amy', 'Fri12'),
    ('Amy', 'Sat13'), ('Amy', 'Sun14'), ('Bob', 'Mon1'), ('Bob', 'Tue2'),
    ('Bob', 'Fri5'), ('Bob', 'Sat6'), ('Bob', 'Mon8'), ('Bob', 'Thu11'),
    ('Bob', 'Sat13'), ('Cathy', 'Wed3'), ('Cathy', 'Thu4'), ('Cathy', 'Fri5'),
    ('Cathy', 'Sun7'), ('Cathy', 'Mon8'), ('Cathy', 'Tue9'),
    ('Cathy', 'Wed10'), ('Cathy', 'Thu11'), ('Cathy', 'Fri12'),
    ('Cathy', 'Sat13'), ('Cathy', 'Sun14'), ('Dan', 'Tue2'), ('Dan', 'Wed3'),
    ('Dan', 'Fri5'), ('Dan', 'Sat6'), ('Dan', 'Mon8'), ('Dan', 'Tue9'),
    ('Dan', 'Wed10'), ('Dan', 'Thu11'), ('Dan', 'Fri12'), ('Dan', 'Sat13'),
    ('Dan', 'Sun14')
  ])

  # Create initial model.
  m = gp.Model("workforce5")

  # Initialize assignment decision variables.

  x = m.addVars(availability, vtype=GRB.BINARY, name="x")

  # Slack decision variables determine the number of extra workers required to satisfy the requirements
  # of each shift
  slacks = m.addVars(shifts, name="Slack")

  # Auxiliary variable totSlack to represent the total number of extra workers required to satisfy the
  # requirements of all the shifts.
  totSlack = m.addVar(name='totSlack')
  # Auxiliary variable totShifts counts the total shifts worked by each employed worker
  totShifts = m.addVars(workers, name="TotShifts")
  # Constraint: All shifts requirements most be satisfied.

  shift_reqmts = m.addConstrs(
    (x.sum('*', s) + slacks[s] == shiftRequirements[s] for s in shifts),
    name='shiftRequirement')
  # Constraint: set the auxiliary variable (totSlack) equal to the total number of extra workers
  # required to satisfy shift requirements

  num_temps = m.addConstr(totSlack == slacks.sum(), name='totSlack')

  # Constraint: compute the total number of shifts for each worker

  num_shifts = m.addConstrs((totShifts[w] == x.sum(w, '*') for w in workers),
                            name='totShifts')
  # Auxiliary variables.
  # minShift is the minimum number of shifts allocated to workers
  # maxShift is the maximum number of shifts allocated to workers

  minShift = m.addVar(name='minShift')

  maxShift = m.addVar(name='maxShift')

  # Constraint:
  # The addGenConstrMin() method of the model object m adds a new general constraint that
  # determines the minimum value among a set of variables.
  # The first argument is the variable whose value will be equal to the minimum of the other variables,
  # minShift in this case.
  # The second argument is the set variables over which the minimum will be taken, (totShifts) in
  # this case.
  # Recall that the totShifts variable is defined over the set of worker and determines the number of
  # shifts that an employed worker will work. The third argument is the name of this constraint.

  min_constr = m.addGenConstrMin(minShift, totShifts, name='minShift')

  # Constraint:
  # Similarly, the addGenConstrMax() method of the model object m adds a new general
  # constraint that determines the maximum value among a set of variables.

  max_constr = m.addGenConstrMax(maxShift, totShifts, name='maxShift')

  # Set global sense for ALL objectives.
  # This means that all objectives of the model object m are going to be minimized
  m.ModelSense = GRB.MINIMIZE
  m.setObjectiveN(totSlack, index=0, priority=2, reltol=0.2, name='TotalSlack')
  m.setObjectiveN(maxShift - minShift, index=1, priority=1, name='Fairness')
  m.optimize()
  status = m.Status
  if status == GRB.Status.INF_OR_UNBD or status == GRB.Status.INFEASIBLE or status == GRB.Status.UNBOUNDED:
    return "The model cannot be solved because it is infeasible or unbounded"
    sys.exit(0)
# If the optimization status of the model is not optimal for some other reason, we report that
# situation.
  if status != GRB.Status.OPTIMAL:
    return "Optimization was stopped with status ' + str(status)"
    sys.exit(0)

    # Print total slack and the number of shifts worked for each worker
# The KPIs for this optimization number is the number of extra worked required to satisfy
# demand and the number of shifts that each employed worker is working.
  solution = {}
  shifts_sol = {}
  solution['Total slack required'] = str(totSlack.X)
  assignments_all = {}
  gant = {}

  assignments = dict()
  for [w, s] in availability:
    if x[w, s].x == 1:
      if w in assignments:
        assignments[w].append(s)
      else:
        assignments[w] = [s]

    # print(pd.DataFrame.from_records(list(solution.items()), columns=['KPI', 'Value']))
    # print('-'*50)

  for w in workers:
    shifts_sol[w] = int(totShifts[w].X)
    assignments_all[w] = assignments.get(w, [])


# print('Shifts')
# print(pd.DataFrame.from_records(list(shifts_sol.items()), columns=['Worker', 'Number of shifts']))

# y_pos = np.arange(len(shifts_sol.keys()))
# plt.bar(y_pos,shifts_sol.values() , align='center')
# plt.xticks(y_pos, shifts_sol.keys())
# plt.show()

# print('-'*50)
  for w in assignments_all:
    gant[w] = [w]
    for d in shifts:
      gant[w].append('*' if d in assignments_all[w] else '-')

  return render_template("home.html",
                         value=list(shifts_sol.values()),
                         label=list(shifts_sol.keys()),
                         gant=gant)

if __name__ == "__main__":
  app.run(host='0.0.0.0', debug=True)
