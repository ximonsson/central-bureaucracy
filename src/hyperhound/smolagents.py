import smolagents
import mlflow
import os


class Model(mlflow.pyfunc.PythonModel):
    def __init__(self, model_id="hyper-hound", prompt="prompts:/hyper-hound@champion"):
        self.prompt = mlflow.load_prompt(prompt)

        model = smolagents.OpenAIServerModel(
            model_id=model_id,
            api_base=os.environ["OPENAI_API_BASE"],
            api_key=os.environ["OPENAI_API_KEY"],
            temperature=0,
        )

        self.agent = smolagents.ToolCallingAgent(
            tools=[smolagents.DuckDuckGoSearchTool()], model=model
        )

    def predict(self, context, model_input, params=None) -> str:
        return self.agent.run(
            self.prompt.template + f"Now search '{model_input}'", max_steps=2
        )
