import mlflow
import hyperhound


def init_hyperhound(prompt_path: str):
    """
    Initialize Hyper Hound.

    Ags:
        prompt_path: path to the prompt file
    """

    if prompt_path.startswith("prompts:/"):
        prompt = mlflow.load_prompt(prompt_path).template
    else:
        with open(prompt_path) as f:
            prompt = f.read()

    model_id = "hyper-hound"

    return hyperhound.create_graph(model_id, prompt)
