# ChatGPT Share RSC Notes

Observed `chatgpt.com/share/...` pages may include the public conversation as React Router streamed data:

```javascript
window.__reactRouterContext.streamController.enqueue("[{\"_1\":2,...}]\\n");
```

The first stream chunk is a JSON string containing a JSON array. The array is a reference table:

- Objects use keys like `_123`; the number points to the table entry containing the real key string.
- Object values may also be numeric references into the same table.
- Lists may contain numeric references.
- Negative numeric references usually represent null-like sentinel values.
- Some references may be cyclic, so decoders need memoization before descending into child values.

The useful route has this shape after resolving references:

```python
root["loaderData"]["routes/share.$shareId.($action)"]["serverResponse"]["data"]
```

Important fields:

- `title`
- `create_time`
- `update_time`
- `conversation_id`
- `mapping`
- `linear_conversation`
- `current_node`

Use `linear_conversation` for readable exports. Each node may contain `message.author.role`, `message.create_time`, and `message.content`. For normal text turns, `message.content.content_type` is `text` or `multimodal_text`, and `parts` contains the visible text.

Common artifacts to filter:

- Empty `system` messages.
- `Original custom instructions no longer available`.
- Assistant JSON event text such as `{"content_type":"thoughts",...}`.
- Tool-call JSON text such as `{"system1_search_query":[...]}` or `{"open":[...]}`.
- Redacted tool result text: `The output of this plugin was redacted.`
- ChatGPT internal citation tokens such as `citeturn123view0`; these are page-local handles, not durable Markdown citations.
- Renderer-only Markdown directive container lines such as `:::writing{variant="document" id="..."}` and matching closing lines. Remove the container markers, not the content inside.

Rendering note:

- Demote Markdown headings inside message bodies after message extraction and cleanup.
- Do not demote headings inside fenced code blocks.
- This is a presentation-layer transform; keep `messages-json` as extracted visible text, not as rendered Markdown.
- Treat `--plan-template` output as a starter file only. The final export should use an agent-curated `--plan` so the turn index contains semantic summaries instead of prompt truncations.
