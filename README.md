# cpm-scheduler

I kept working out critical paths by hand on small programmes, so I built this to do it in seconds. Give it a list of tasks with durations and dependencies, and it works out the early and late start and finish for every task, the total float, the critical path, and the overall project duration. It can also print a simple text Gantt chart.

Built with only the Python standard library, so there is nothing to
install beyond Python 3.9 or newer.

## Quick start

```bash
python -m cpm_scheduler examples/single-storey-house.json
python -m cpm_scheduler examples/single-storey-house.json --gantt
python -m cpm_scheduler examples/single-storey-house.csv --output schedule.txt
```

## Example output

```
ID  Task                            Dur  ES  EF  LS  LF  Float  Critical
--  ------------------------------  ---  --  --  --  --  -----  --------
 A  Site setup                        2   0   1   0   1      0       YES
 B  Excavation                        3   2   4   2   4      0       YES
 C  Footings and foundation           5   5   9   5   9      0       YES
 D  Ground floor slab                 4  10  13  10  13      0       YES
 E  Structural walls                  8  14  21  14  21      0       YES
 F  Roof structure                    6  22  27  24  29      2
 G  Roof covering                     4  28  31  30  33      2
 H  Electrical first fix              5  22  26  22  26      0       YES
 I  Plumbing first fix                5  22  26  22  26      0       YES
 J  Plastering and screed             7  27  33  27  33      0       YES
 K  Painting                          6  34  39  34  39      0       YES
 L  Final inspection and handover     2  40  41  40  41      0       YES

Project duration: 42 days
Critical path: A -> B -> C -> D -> E -> H -> I -> J -> K -> L
```

Days are counted from day 0, the programme start. A task starts the
day after its latest predecessor finishes. A task with zero float is
critical: any delay to it delays the whole project.

## Input format

Tasks can be given as JSON or CSV. Each task needs an `id`, a `name`,
a `duration` in whole days, and a list of `predecessors` (the ids of
tasks that must finish first). Tasks with no predecessors start on
day 0.

JSON:

```json
{
  "tasks": [
    {"id": "A", "name": "Site setup", "duration": 2, "predecessors": []},
    {"id": "B", "name": "Excavation", "duration": 3, "predecessors": ["A"]}
  ]
}
```

CSV (predecessors separated by commas inside quotes):

```csv
id,name,duration,predecessors
A,Site setup,2,
B,Excavation,3,A
```

The tool checks the input and reports a clear error for duplicate
task ids, unknown predecessors, negative durations, and dependency
cycles.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers the forward and backward passes, float and the
critical path, zero-duration tasks, input validation, and the bundled
example programme in both JSON and CSV form.

## Scope note

This is a portfolio project for learning and demonstration. The
example programme in the `examples` folder is fictional sample data
with illustrative durations, not a real project programme. The tool
does date arithmetic on whole days only: it does not handle working
calendars, weekends, resource levelling, or cost loading.

## License

MIT. See `LICENSE`.
