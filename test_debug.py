import agent
import json

text = "Wrong: [1, 2, 3]\nWrong: [4, 5, 6]\nCorrect: " + json.dumps([{"id": "TC_1"}])
print("Text:", repr(text))

result = agent.extract_json(text)
print("Result:", result)
print("Expected: [{'id': 'TC_1'}]")
print("Match:", result == [{"id": "TC_1"}])
