#!/usr/bin/env python3
import yaml
import random
from typing import Dict, Callable, Literal, Any

from google.genai import types

from src.engine.game import GoGame
from src.engine.render import render_board

COLOR_STATUS = Literal["human", "beginner", "intermdiate", "hard"]


def start_game(
    boardsize: int = 9,
    black: COLOR_STATUS = "human",
    white: COLOR_STATUS = "hard",
    user_id: str = "",
    state_dict: Dict[str, Any] = {},
    **kwargs,
) -> GoGame:
    new_game = GoGame(boardsize, black, white)
    state_dict[user_id] = new_game
    return new_game


def get_game_status(game: GoGame, **kwargs):
    img = render_board(game.board, random.randint(0, 500), (0, 0), f"cache/{game.id}")
    return img, game.board


def make_move(
    move: tuple[int, int],
    user_id: str = "",
    state_dict: Dict[str, Any] = {},
    game: GoGame = GoGame(),
    **kwargs,
) -> GoGame:
    if game.turn == "human":
        game.play_step(move)
        game.play_step()
    else:
        game.play_step()
    return game


from google.genai import types

def generate_function_declaration(tool_data: dict) -> types.FunctionDeclaration:
    """
    Converts a tool dictionary from the YAML into a Gemini FunctionDeclaration,
    correctly handling array types (which require a nested 'items' schema).
    """
    
    properties = {}
    required_params = []
    
    # 1. Iterate through all parameters defined in the YAML
    if 'parameters' in tool_data and tool_data['parameters']:
        for param_name, details in tool_data['parameters'].items():
            
            # Initialize the nested items schema
            items_schema = None 
            
            # Determine the main type from the YAML (e.g., 'array', 'string', 'integer')
            main_type_str = details.get('type', 'string').upper()
            
            # --- CRITICAL FIX: Handle 'array' type and create nested 'items' schema ---
            if main_type_str == 'ARRAY' and 'items' in details:
                 # The 'items' field in the YAML is a dictionary containing the item type
                 item_type_yaml_dict = details['items']
                 
                 # Create the Schema object for the array's contents
                 items_schema = types.Schema(
                    type=types.Type(item_type_yaml_dict.get('type', 'string').upper()),
                    # You could add item descriptions here if needed, but type is enough to solve the error
                 )
            
            # 2. Construct the main parameter Schema object
            properties[param_name] = types.Schema(
                type=types.Type(main_type_str), 
                description=details.get('logic', f"Parameter for {param_name}"),
                # Crucially, pass the items_schema (which is None for strings/ints, 
                # but a valid Schema object for arrays)
                items=items_schema 
            )
            
            # 3. Handle required fields
            if details.get('required'):
                required_params.append(param_name)

    # 4. Define the final parameters schema
    parameters_schema = types.Schema(
        type=types.Type.OBJECT,
        properties=properties,
        required=required_params
    )

    # 5. Create the FunctionDeclaration
    return types.FunctionDeclaration(
        name=tool_data['name'],
        description=tool_data['description'],
        parameters=parameters_schema
    )

# The ALL_TOOLS dictionary must be generated using this updated function.
# ALL_TOOLS = create_all_tools_schema("agent.yaml")

def create_all_tools_schema(yaml_file_path: str) -> dict:
    """Loads the YAML and creates a dictionary of FunctionDeclarations."""
    yaml_content: Dict[str, Any]
    with open(yaml_file_path, "r") as file:
        yaml_content: Dict[str, Any] = yaml.load(file, yaml.FullLoader)

    all_tools_schema = {}
    for tool_data in yaml_content.get("tools", []):
        func_declaration = generate_function_declaration(tool_data)
        all_tools_schema[tool_data["name"]] = func_declaration

    return all_tools_schema


ALL_TOOLS = create_all_tools_schema("src/config/tools.yaml")
