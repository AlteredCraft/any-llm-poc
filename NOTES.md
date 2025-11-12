
I want to show the utility of using any-llm (https://github.com/mozilla-ai/any-llm). You can choose between configured model providers and their available models
I am using the Gateway for an access proxy: https://mozilla-ai.github.io/any-llm/gateway/overview/



## The API

I'm running locally as a docker instance: https://mozilla-ai.github.io/any-llm/gateway/quickstart/


API Refernce: https://mozilla-ai.github.io/any-llm/gateway/api-reference/


Getting the total usage for a User
```bash
curl -s http://localhost:8000/v1/users/user-123/usage \
  -H "X-AnyLLM-Key: Bearer ${GATEWAY_MASTER_KEY}" \
  -H "Content-Type: application/json"
[{"id":"2ff1048a-df8d-489e-8b7a-905dff216f57","user_id":"user-123","api_key_id":null,"timestamp":"2025-11-12T18:17:51.581203+00:00","model":"gemini-2.5-flash-lite","provider":"gemini","endpoint":"/v1/chat/completions","prompt_tokens":8,"completion_tokens":22,"total_tokens":30,"cost":null,"status":"success","error_message":null},{"id":"22976b28-2dcd-492b-85ab-b0b8937c8c53","user_id":"user-123","api_key_id":null,"timestamp":"2025-11-12T18:13:47.842203+00:00","model":"gemini-2.5-flash-lite","provider":"gemini","endpoint":"/v1/chat/completions","prompt_tokens":8,"completion_tokens":19,"total_tokens":27,"cost":null,"status":"success","error_message":null}]
```

# What to build

I want to build a simple web app with a simple chat interface. 
The user will have the option to choose between configured providers and there models.
After each chat completions, a tally of usage metrics will update.
when the user switches the model it resets the "session" (clear chat window and metrics)

see usage example in test.py

## Notes
- use uv only for python virt env and dependencies