# Spike A

Visualization:

We are looking at an actor selecting elements from a field of colors.

When we have at least one selection, we recommend others according to some algorithm based on similarity.

The actor can ignore, accept or actively reject any of these

To model preference, ther is built-in aversion and attraction. So one corner is avoided, one is more actively sought, and one is neutral. This only applies to NEW selections made using the Add Biased button: red is avoided, green is favored nbd blue is neutral. This can be used to verify that the recommendations evolve approriately. 

In the evolution, we would expect the actor to gradually explore most of the green area, some of the blue area and less of the red area. We would also want out recommendations to be somewhat matching this pattern over time.

The prior recommendations leave a trace, so that it is possible to read the pattern of multiple recommendations.

Currently two scenarios are available.

## Current thoughts

The cycle of recommendations should be triggered whenever you add a new skill.

Algorithms:

- All assume at least 1 skill!
  
Assuming no retention of history:

- A: Original:
  - 1-6 skills:
    - get 2 adjacencies per skill -> 12
  - 7+
    - randomly select 6 and do like above
  - Anyway: shuffle the pack

  Implementation:
  - pick 6 skills at random
  - randomly select 2 adjacencies for each
  - shuffle the 12.

- B: Weighted locally:
  - Favor most recently added, but some near and some old distant
  - Weighted selection of initial skills provides better context
  - Oversampling by (average) 3 increases the variation

  Implementation:
  - pick the most recently added 2 skills
  - pick another 2 within the next 4
  - pick another 2 from the rest
  - find 2-3 related to these and return 12 after shuffling

These are not viable because they would increase the database load significantly:

- With rejections tracked:
  - Once rejected, the suggestion will not appear again for a while?
  
- With Recommendations tracked:
  - recommendations that have been made several times will not be presented
  - (Actually we are just showing in a deepening gray that the recommendation has been repeated)

## Next

Add the ability to save a series of images: these can be used for an animation

- Show current actor status
- Allow selection steps
- Persist common actor types

## How to Launch

Load from folder `SpikeA` into vscode.

Terminal -> `env\scripts\activate`
(If the environemnt gets broken, delete the files in Lib\site-packages and use `python3 -m venv env`
then use `python3 -m pip install --force-reinstall -r requirements.txt`)

- Use the green arrow at upperleft to launch `Python:flask`
- Ctrl-click the url in the terminal window output
- Ctrl-C to close.
