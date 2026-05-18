import json

with open("data/raw_comments.json", "r", encoding="utf-8") as f:
    raw = json.load(f)
likes = [c["like"] for c in raw]
print(f"raw: {len(raw)}条, like max={max(likes)} min={min(likes)} avg={sum(likes)/len(likes):.0f}")

with open("data/cleaned_comments.json", "r", encoding="utf-8") as f:
    cl = json.load(f)
print(f"cleaned: {len(cl)}条, has_like={all('like' in c for c in cl)}")

with open("data/sentiment_results.json", "r", encoding="utf-8") as f:
    s = json.load(f)
print(f"sentiment: {len(s['all'])}条, has_like={all('like' in i for i in s['all'])}")
