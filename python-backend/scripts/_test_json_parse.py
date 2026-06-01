from app.utils.llm_retry import parse_json_list, parse_json_object

arr = '[\n  {"mainTitle": "a", "subTitle": "b"}\n]\n\n以上供参考'
assert len(parse_json_list(arr)) == 1

wrapped = '{"titleOptions": [{"mainTitle": "x", "subTitle": "y"}]}'
assert len(parse_json_list(wrapped)) == 1

obj = '{"sections": [{"section": 1, "title": "t", "points": ["p"]}]}\n说明'
assert "sections" in parse_json_object(obj)

print("ok")
