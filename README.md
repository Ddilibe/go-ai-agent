# Go Game in Python

**Project:** A playable Go (Weiqi/Baduk) game implemented in Python.

**Goals:**

* Provide a clean, extensible Python implementation of the board game *Go* (configurable board sizes: 9x9, 13x13, 19x19).
* Render the board and game state with **Pillow** (PIL) for image-based UI and exportable PNGs.
* Ship a pluggable AI opponent interface — start with a simple baseline (rule-based / random / heuristic) and provide hooks for more advanced brains (MCTS, neural policy/value networks using PyTorch or TensorFlow).
* Keep code modular so contributors can replace the rendering, UI, or AI with minimal friction.

---

## Table of contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [Installation](#installation)
5. [Quick start](#quick-start)
6. [Gameplay and rules summary](#gameplay-and-rules-summary)
7. [AI design overview](#ai-design-overview)
8. [Rendering with Pillow](#rendering-with-pillow)
9. [Development roadmap](#development-roadmap)
10. [License](#license)

---

## Features

* Playable Go on configurable board sizes (9x9, 13x13, 19x19).
* CLI-driven game loop with image output after each move (PNG snapshots created via Pillow).
* Two-player human vs human (local), human vs AI, and AI vs AI modes.
* Simple and documented AI interface so you can plug in different strategies:

  * `RandomAgent` (baseline)
  * `HeuristicAgent` (capture heuristics / liberty awareness)
  * `MCTSAgent` (Monte Carlo Tree Search) — scaffold included
  * `NNAgent` (policy/value network) — scaffold + model save/load hooks
* Game rules implemented: capturing, liberties, ko rule (basic), pass/score counting (territory and/or area — configurable)
* Unit tests for core game logic (captures, liberties, valid moves).

---

## Tech stack

* Python 3.10+ (recommended)
* Pillow (PIL) — for board rendering and image export
* NumPy — board arrays and numeric helpers
* pytest — for running tests

---

## Project structure (recommended)

```
go-python/
├── README.md
├── pyproject.toml / requirements.txt
├── src/
│   ├── go/
│   │   ├── __init__.py
│   │   ├── board.py          # Board class, rules, move validation, capture logic
│   │   ├── game.py           # Game loop, turn management, scoring
│   │   ├── render.py         # Pillow-based rendering utilities
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   ├── random_agent.py
│   │   │   ├── heuristic_agent.py
│   │   │   ├── mcts_agent.py
│   │   │   └── nn_agent.py
│   │   └── utils.py
├── examples/
│   ├── play_human_vs_ai.py
│   ├── render_demo.py
├── models/                   # saved NN weights / checkpoints
├── cache/                    # snapshot images, logs
├── tests/
│   ├── test_board.py
│   └── test_rules.py
└── docs/
    └── design_notes.md
```

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourname/go-python.git
cd go-python
```

2. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
.venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
# or using pyproject: pip install -e .[dev]
```

**Minimum pip requirements example** (put in `requirements.txt`):

```
Pillow>=10.0
numpy>=1.26
pytest
# Optional for AI agents:
torch>=2.0  # or tensorflow>=2.12
```

---

## Quick start

Run a small demo that plays a human vs random AI on a 9x9 board and writes PNG snapshots to `cache/`:

```bash
python examples/play_human_vs_ai.py --board-size 9 --output-dir cache
```

`play_human_vs_ai.py` should launch a CLI loop that prints the board coordinates and after each move produces `cache/step_0001.png`, `cache/step_0002.png`, etc.

---

## Gameplay and rules summary

This implementation focuses on the essential rules needed to play:

* Stones are placed on intersections.
* Groups of stones with no liberties are captured and removed.
* The Ko rule is enforced (basic single-position repetition prevention).
* Passing is allowed; two consecutive passes end the game.
* Scoring options: area scoring or territory scoring (configurable in `game.py`).

Refer to `docs/design_notes.md` for details about edge cases and scoring ties.

---

## AI design overview

The repository includes an `agents` interface so alternative brains are easy to plug in.

### Agent interface (recommended minimal API)

```python
class BaseAgent:
    def __init__(self, color: int, board_size: int):
        self.color = color

    def select_move(self, board: np.ndarray, legal_moves: List[Tuple[int,int]]) -> Optional[Tuple[int,int]]:
        """Return (row,col) or None to pass."""
```

### Suggested Agent progression

1. **RandomAgent** — picks uniformly from legal moves.
2. **HeuristicAgent** — prioritizes captures, avoids self-atari, prefers larger liberties.
3. **MCTSAgent** — Monte Carlo Tree Search with playouts; good mid-term step before NN training.
4. **NNAgent** — train a policy/value network using self-play data; use PyTorch/TensorFlow. Provide training/evaluation scripts in `examples/`.

**Notes on training**: If you plan to train a neural-network agent, provide an experience buffer, game record format (SGF or a simple numpy encoding), and evaluation matches (ELO-style) to track improvements.

---

## Rendering with Pillow

The `render.py` module will provide functions like:

* `draw_board(board: np.ndarray, size: int, square_px: int = 40) -> PIL.Image` — returns a PIL Image of the board.
* `annotate_move(img: Image, move: Tuple[int,int], label: str)` — draws move numbers or highlights.

Rendering tips:

* Keep margins for coordinates and star points (hoshi) for 9x9/13x13/19x19.
* Use anti-aliased circles for stones and subtle shadows to improve visual clarity.
* Export snapshots as PNG with filenames containing move index and player.

---

## Development roadmap

Planned incremental tasks:

1. Core rules & board representation (board.py) — **baseline**
2. CLI game loop & snapshot rendering (game.py + render.py) — **baseline**
3. Agents: RandomAgent & HeuristicAgent — **baseline**
4. Unit tests covering capturing, ko, scoring — **baseline**
5. MCTSAgent scaffold & basic implementation — **next**
6. NNAgent scaffold (training pipeline, model save/load) — **next**
7. Optional: GUI (tkinter / web-based) that consumes snapshots or integrates directly
8. Optional: SGF import/export, game viewer

---

## Contributing

* Open an issue for bugs or feature requests.
* Follow the code style in `src/` (PEP8). Tests must be added for new logic.
* Use meaningful commit messages and open a PR against `main`.

---

## Tests

Run tests with:

```bash
pytest -q
```

Write tests under `tests/` that assert correctness of basic rules (captures and liberties) before touching AI components.

---

## License

This project is MIT licensed. Include a `LICENSE` file with the MIT text.

---

## Next steps I can help with

If you'd like I can:

* scaffold the Python package with the files listed above,
* implement `board.py` (board representation, move validation, capture logic),
* implement `render.py` (Pillow rendering utilities) and provide example PNGs,
* implement baseline agents (`RandomAgent`, `HeuristicAgent`), or
* outline an MCTS implementation or a neural training pipeline.

Tell me which piece you want next and I’ll scaffold it.
