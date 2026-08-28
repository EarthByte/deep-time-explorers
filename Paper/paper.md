---
title: 'Deep Time Explorers: Zero-Install Jupyter Notebooks for Teaching Plate Tectonics to Primary School Students'
tags:
  - Earth science education
  - plate tectonics
  - Jupyter notebook
  - primary education
  - geoscience
  - Python
authors:
  - name: R. Dietmar Müller
    orcid: 0000-0002-3334-5764
    affiliation: 1
affiliations:
  - name: EarthByte Group, School of Geosciences, University of Sydney, Australia
    index: 1
date: 25 August 2026
bibliography: paper.bib
---

# Summary

Deep Time Explorers is a suite of six self-contained Jupyter notebooks that
introduces plate tectonics to Year 4 students (ages 9-10) using the same
real, peer-reviewed deep-time reconstruction data that researchers use, with
none of the software installation that normally stands in the way. Each
notebook drives a single big idea through an interactive widget: a time
slider that redraws the continents and their plate-velocity arrows over 300
million years; a coastline "jigsaw" that lets students test Wegener's own
evidence for continental drift; a map of real earthquakes plotted against
plate boundaries; a simplified ocean-current journey that changes when a
deep-time sea gateway opens or closes; a postcard generator that reconstructs
where any Australian town used to sit at any age; and a fossil-and-rock
"climate detective" map spanning six geological ages. Every background,
coastline, plate boundary, earthquake location, and fossil-climate point is
generated once from real EarthByte data products [@scotese2018paleodem;
@boucot2013climate] using `pygplates`, `PlateTectonicTools`, and `GPlately`
[@muller2018gplates; @mather2024gplately], then cached as plain image and
CSV files. This means the student-facing notebooks depend only on `numpy`,
`pandas`, `matplotlib`, and `ipywidgets` — no `gplately`, `pygplates`, or
`cartopy` needs to be installed on a school computer. The suite is also
packaged as a static JupyterLite site [@jupyterlite], so it runs entirely
inside a web browser via Pyodide, with no installation or account of any
kind, making it usable on a shared classroom Chromebook. Each notebook pairs
its interactive figure with explanatory narrative text — a stated "mission"
for the student, plot-language explanations of what the data actually shows,
and reflection questions — and the suite links explicitly to strands of the
NSW Science and Technology K-6 syllabus and the Australian Curriculum v9.

![Sample outputs from two of the six notebooks. **(a)** Notebook 1
("Continents on the Move") at the 300 Ma end of its time slider, showing the
real reconstructed Pangaea supercontinent with paleo-elevation and plate
boundaries. **(b)** Notebook 6 ("Fossil Climate Detectives") at 80 Ma,
showing real fossil and rock climate-indicator locations as picture icons,
with a legend row giving each icon's count at that
age.](figures/figure1_sample_outputs.png)

# Statement of Need

Plate tectonics is typically introduced to primary-aged students through
static diagrams, animations, or physical jigsaw-puzzle activities. These are
effective for the basic "the continents used to fit together" idea, but they
stop short of what makes the underlying science compelling: that a
continent's position at any point in the last several hundred million years
can be *calculated*, from real magnetic, fossil, and geological evidence, by
software that professional Earth scientists use every day. Existing
open-source tooling for deep-time plate reconstruction — `GPlates`, its
Python bindings `pygplates`, and the higher-level `GPlately` package
[@muller2018gplates; @mather2024gplately] — is built for researchers and
university students, requires a scientific Python (conda) environment, and
exposes an API with a correspondingly steep learning curve. There was no
existing bridge from that real, research-grade data and software down to a
form usable by a 9- or 10-year-old on a shared school computer with no
software installed and a single lesson's worth of attention. Deep Time
Explorers is that bridge: a teacher (or student, given a browser) needs no
prior exposure to Python, Jupyter, or plate tectonics software, only a
willingness to move a slider and look at a map. The project grew directly
out of an existing classroom precedent — a Year 4 teacher and EarthByte
alumnus already runs an ocean-current particle-tracking notebook with his
own class — which suggested that a plate-tectonics sibling, built the same
way, could occupy the same real-code, real-data, highly-visual niche for a
different Earth science topic.

# Learning objectives and instructional design

Each notebook is built around one manipulable figure and one central
question a student can answer just by watching it change: *where were the
continents, how fast did they move, do real coastlines actually fit
together, do earthquakes cluster where the theory predicts, how does a
closing ocean gateway change a current's path, where did my own town used to
be, and what do fossils and rock types tell us about a climate nobody could
observe directly?* Every notebook opens with a short "Your mission" prompt
naming the specific slider or control to try, and most close with a "Try
this next!" extension and one or more open reflection questions rather than
a single correct answer — for example, Notebook 2 asks students to compare
how closely two 300-million-year-old coastlines line up and to consider why
a reconstruction would not be expected to match perfectly everywhere.
Two notebooks (2 and 5) also include a short "how do scientists actually
know this?" section that connects the visual result back to real evidence —
magnetic striping on the ocean floor, and the same plate-motion model used
throughout the suite — so the tool is not presented as a black box.

All six notebooks follow this same mission-narrative-reflection-extension
pattern deliberately, so that a teacher who has only had time to skim one
notebook can confidently run any of the other five without additional
preparation — a practical constraint given that a Year 4 lesson is short and
a teacher new to Jupyter should never need to read source code to use the
material. Narrative text is written to a reading level a fluent Year 4
student can manage unaided: short sentences, technical terms defined the
first time they appear, and no assumed science vocabulary beyond what the
NSW Stage 2 syllabus already introduces. This is also why all reconstruction
computation happens ahead of time in `export_data.py` rather than inside the
student notebooks (see below): the only cognitive load left for a student is
the Earth science question itself, not `pygplates` syntax or a conda
environment. Reflection questions are open-ended by design rather than
right-or-wrong, intended to prompt classroom discussion rather than a graded
answer; the "Try this next!" prompts give early finishers a concrete way to
go further without requiring the whole class to move on together — for
example, Notebook 6 defines a "cold" (ice-age) climate icon that is
deliberately left switched off by default and invites students to add it
back in themselves.

# Design and implementation

All deep-time data is pre-computed by a single script, `export_data.py`,
which runs once in a full `gplately` conda environment and writes plain
PNG basemaps and CSV/GeoJSON tables into a `data/` folder. The student
notebooks only ever read these cached files, which is what allows them to
run with nothing beyond `numpy`, `pandas`, `matplotlib`, and `ipywidgets`,
and to run unmodified inside JupyterLite. Basemaps combine real
paleo-elevation from the Scotese & Wright (2018) PaleoDEM
[@scotese2018paleodem] with plate boundaries reconstructed to the same age
and typed by kind (ridges, transforms, subduction zones) using `GPlately`'s
own plotting layer, so the coastlines and boundary lines are guaranteed to
come from the same underlying plate model. Notebook 3's earthquake layer
uses the public USGS earthquake catalog [@usgs_earthquake_catalog], and
Notebook 6's fossil-climate layer uses the Boucot et al. (2013)
climate-sensitive lithology compilation [@boucot2013climate], both
reconstructed back through time with the same reconstruction machinery. A
GitHub Actions workflow rebuilds and redeploys the JupyterLite site directly
from the repository's six canonical notebooks and `data/` folder on every
push, so there is no separate, hand-maintained "web copy" of the material
that could drift out of sync with the notebooks a teacher would open
locally.

# Future work and evaluation

Deep Time Explorers has not yet been used with real students, and its most
important open question is an empirical one: whether the design choices
above actually build correct intuitions in a 9- or 10-year-old, rather than
just providing an enjoyable slider to play with. A classroom pilot is
planned with the Year 4 class whose teacher's existing ocean-current
notebook inspired this project (see Statement of Need), using a short
pre/post assessment — for example, asking students to sketch or describe
where a named continent was at a given age, and why earthquakes happen where
they do — alongside a teacher-facing survey covering lesson length,
technical friction, and which of the six notebooks worked best in a single
sitting. That feedback is expected to drive several likely follow-ups:
broadening Notebook 6's climate categories with real reef-occurrence data
from the Paleobiology Database, already used elsewhere in the parent
GPlately-pyGMT tutorial suite, to give students a literal coral-reef icon
rather than the closest available proxy; extending the plate-boundary
overlay past its current 100 Ma resolution limit as higher-resolution
deep-time topologies become available; and self-hosting the Pyodide runtime
JupyterLite depends on, to remove the suite's one remaining reliance on an
external CDN at load time. A successful pilot would also make it possible to
describe this work in venues that specifically require classroom evidence,
such as the *Journal of Geoscience Education*'s curriculum-and-instruction
category, as a natural follow-on to this software-focused submission.

# AI-assisted development

Generative AI (Claude, Anthropic) was used substantially throughout this
project's development: drafting and iterating notebook code and narrative
text, designing the project's logo, and assembling the JupyterLite
deployment workflow, under the direction and review of the author, who
verified all resulting figures, data provenance, and curriculum claims. No
part of the underlying scientific data or plate reconstruction methodology
was AI-generated; all reconstructions come from the same published data
products and open-source EarthByte software cited above.

# Status and availability

The source code, notebooks, and JupyterLite deployment are openly available
under the MIT license at <https://github.com/EarthByte/deep-time-explorers>,
with a live, browser-only version at
<https://earthbyte.github.io/deep-time-explorers/lab/index.html>.

# Acknowledgements

This work builds directly on the EarthByte Group's GPlately + pyGMT
tutorial suite and its accompanying open data products.

# References
