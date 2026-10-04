from pydantic import Field
from typing import final
from datetime import datetime
import uuid
from typing import Any
from functools import wraps
from collections.abc import Callable
import time


from schemas import Span, Trace


active_trace = None


def trace_step(step_name: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            global active_trace

            #if no trace is active, just run the function normally
            if active_trace is None:
                return func(*args, **kwargs)
            


            # start the span and capture inputs and confidence score
            span = Span(
                span_id=str(uuid.uuid4()),
                step_name=step_name,
                start_time=datetime.utcnow(),
                
                #convert inputs to dict assumes Pydantiv models for inputs
                input_data={"args":[a.model_dump() if hasattr(a, 'model_dump') else str(a) for a in args]},
                


            )   

            start_time = time.time()
            try:
                #execute the actual pipeline step
                result = func(*args,**kwargs)

                #capture the succesful output
                span.output_data = result.model_dump() if hasattr(result, "model_dump") else {"raw": str(result)}
                
                

                #Automtically extract confidence score present in Pydantic result object 
                if hasattr(result, "confidence_score"):
                    span.confidence = getattr(result, "confidence_score")
                return result

                #handle low confidence spans as priamry suspects

            except Exception as e:
                #capture failure
                span.error = str(e)
                active_trace.status = "failed"
                raise e

            finally: 
                #stop timmer and save span to teh active trace
                span.end_time = datetime.utcnow()
                span.latency_ms = (time.time() - start_time) * 1000
                active_trace.spans.append(span)



        return wrapper
    return decorator                
                     






             
