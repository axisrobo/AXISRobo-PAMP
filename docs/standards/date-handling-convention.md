# 日期处理规范 (Date Handling Convention)

> 完整的函数签名和行为规范见 [date-handling spec](../../openspec/specs/date-handling/spec.md)。
> 本文档聚焦**编码规则**和**检查清单**。

---

## 编码规则

### 规则 1: POST — 显式解析每个日期字段

```python
from app.utils.date_helpers import parse_date

result = await db.execute(text("""
    INSERT INTO ... (start_date, end_date, ...) VALUES (:start_date, :end_date, ...)
"""), {
    "start_date": parse_date(body.get("startDate")),   # ✅
    "end_date":   parse_date(body.get("endDate")),      # ✅
    # "start_date": body.get("startDate"),              # ❌ 字符串！
})
```

### 规则 2: PUT — 动态 SET 构建器中判断字段类型

```python
from app.utils.date_helpers import parse_date

_date_columns = {"start_date", "end_date", "due_date"}

for api_field, db_col in field_mapping.items():
    if api_field in body:
        val = body[api_field]
        if db_col in _date_columns:
            val = parse_date(val)          # ✅ 转换
        params[param_name] = val
```

### 规则 3: TIMESTAMP 列使用 `parse_datetime`

```python
from app.utils.date_helpers import parse_datetime

params["start_time"] = parse_datetime(body.get("startTime"))  # ✅ naive datetime
```

### 规则 4: 禁止本地定义重复的日期解析函数

所有日期解析逻辑必须从 `app.utils.date_helpers` 导入。

### 规则 5: 前端日期字段统一发送 `YYYY-MM-DD`

```typescript
const payload = {
  startDate: startDate?.format('YYYY-MM-DD'),  // "2025-03-17"
};
```

### 规则 6: 前端日期时间字段发送 ISO 8601

```typescript
const payload = {
  startTime: startTime?.toISOString(),  // "2025-03-17T05:00:00.000Z"
};
```

### 规则 7: 日期显示统一使用 `YYYY-MM-DD`

```typescript
new Date(dateStr).toLocaleDateString('en-CA')  // "2025-03-17"
```

---

## 新增 Router 检查清单

- [ ] 导入了 `from app.utils.date_helpers import parse_date, parse_datetime`
- [ ] 每个 DATE 列参数经过 `parse_date()` 转换
- [ ] 每个 TIMESTAMP 列参数经过 `parse_datetime()` 转换
- [ ] PUT 动态 SET 中定义了 `_date_columns` / `_dt_columns` 集合
- [ ] 没有在 router 中自定义日期解析函数
- [ ] 前端日期格式为 `YYYY-MM-DD`，日期时间为 ISO 8601
