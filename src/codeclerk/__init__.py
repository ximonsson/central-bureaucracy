import agents
import openai
import os


def agent(model: str, instr: str, temp: float = 0.0):
    """
    Creates an agent with the specified model, instructions, and temperature.

    Args:
        model (str): The model to use for the agent.
        instr (str): The instructions for the agent.
        temp (float, optional): The temperature for the model. Defaults to 0.0.

    Returns:
        agents.Agent: The created agent.
    """

    c = openai.AsyncOpenAI(base_url=os.environ["OPENAI_API_BASE"])
    m = agents.OpenAIChatCompletionsModel(openai_client=c, model=model)

    return agents.Agent(
        model=m,
        name="Code Clerk",
        instructions=instr,
        model_settings=agents.ModelSettings(temperature=temp),
        tools=[],
    )
