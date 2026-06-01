"""一次性验证 llm_retry（本地联调前可删）"""
from app.utils.llm_retry import parse_json_list, parse_json_object

raw = '```json\n{"x": 1}\n```'
assert parse_json_object(raw)["x"] == 1
assert len(parse_json_list('[{"a": 1}]')) == 1
print("verify ok")
