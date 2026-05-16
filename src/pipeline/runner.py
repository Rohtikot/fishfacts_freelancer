import inspect
from src.pipeline.registry import STEP_REGISTRY

class Pipeline:
    def __init__(self, steps, context=None):
        self.steps = steps
        self.context = context or {}

    def run(self, df):
        for step in self.steps:
            func = STEP_REGISTRY[step['name']]
            params = step.get('params', {})

            # get function signature
            sig = inspect.signature(func)

            # only pass accepted args
            valid_kwargs = {
                k: v
                for k, v in {**params, **self.context}.items()
                if k in sig.parameters
            }

            df = func(df, **valid_kwargs)
        return df
