import asyncio
import json
import logging
import time
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from expense_agent.agent import root_agent
from google.adk.events import RequestInput

logging.basicConfig(level=logging.INFO)

async def main():
    dataset_path = "tests/eval/datasets/basic-dataset.json"
    out_path = "artifacts/traces/generated_traces.json"

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, session_service=session_service, app_name="expense_agent")

    traces = {"eval_cases": []}

    for case in dataset["eval_cases"]:
        case_id = case["eval_case_id"]
        prompt_text = case["prompt"]["parts"][0]["text"]
        logging.info(f"Running case: {case_id}")
        
        message = types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])
        
        session = session_service.create_session_sync(user_id=case_id, app_name="expense_agent")
        
        events = runner.run(
            new_message=message,
            user_id=case_id,
            session_id=session.id,
        )

        needs_human = False
        for ev in events:
            if isinstance(ev, RequestInput):
                needs_human = True
                break
            
        if needs_human:
            decision = "reject" if "prompt_injection" in case_id else "approve"
            logging.info(f"Human required. Providing: {decision}")
            message2 = types.Content(role="user", parts=[types.Part.from_text(text=decision)])
            events2 = runner.run(
                new_message=message2,
                user_id=case_id,
                session_id=session.id,
            )
            for ev in events2:
                pass
                
        session = session_service.get_session_sync(app_name="expense_agent", user_id=case_id, session_id=session.id)
        session_dict = json.loads(session.model_dump_json())

        # Construct strictly valid events
        valid_events = []
        for ev in session_dict["events"]:
            # ADK 'author' might be 'user' or the agent name ('expense_agent')
            author = ev.get("author", "expense_agent")
            
            content_dict = ev.get("content", {})
            if not content_dict:
                # Some events might not have content (like pure tool calls without text in some structures)
                # Ensure parts exist
                content_dict = {"role": author, "parts": []}
                
            valid_events.append({
                "author": author,
                "content": content_dict
            })

        agent_data = {
            "agents": {
                "expense_agent": {
                    "agent_id": "expense_agent"
                }
            },
            "turns": [
                {
                    "turn_index": 0,
                    "events": valid_events
                }
            ]
        }
        
        trace_case = {
            "eval_case_id": case_id,
            "agent_data": agent_data,
            "responses": [{"response": {"role": "model", "parts": [{"text": "dummy"}]}}]
        }
        traces["eval_cases"].append(trace_case)
        time.sleep(5)

    with open(out_path, "w") as f:
        json.dump(traces, f, indent=2)
        
    logging.info(f"Traces written to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
