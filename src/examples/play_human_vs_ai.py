#!/usr/bin/env python3
from engine.game import GoGame

if __name__ == "__main__":
    # Human (Black) vs AI (Intermediate)
    game = GoGame(board_size=9, black="human", white="intermediate", output_dir="cache")
    game.play()
