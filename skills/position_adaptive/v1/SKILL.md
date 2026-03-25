# position_adaptive

## 策略描述

根据当前搜索排名位置动态调整标题策略。不同位置的用户行为不同：靠前位置需要精准匹配意图，靠后位置需要差异化突围。

## 适用场景

- 所有类型内容
- 特别适合 Position 4-8（首页但非顶部）和 Position 9-15（首页底部或第二页）

## 核心技巧

### Position 4-6（首页中部）
- 用户已经看过前 3 个结果，需要差异化
- 强调独特角度或附加价值
- 使用"完整指南"、"深度解析"等暗示更全面

### Position 7-10（首页底部）
- 用户可能在快速扫描，需要强视觉锚点
- 使用数字、括号、年份等格式化元素
- 标题更短更直接

### Position 11-15（第二页）
- 用户主动翻页，意图更强
- 可以更大胆地使用情感触发
- 强调"别人没告诉你的"独特价值

## 示例

**Position 5 — Before**: "React State Management Guide"
**Position 5 — After**: "The Complete React State Management Guide (With Real Examples)"

**Position 9 — Before**: "How to Train a Puppy"
**Position 9 — After**: "Puppy Training: 3 Methods That Actually Work [2024]"

**Position 12 — Before**: "Best Hiking Boots Review"
**Position 12 — After**: "I Tested 15 Hiking Boots — The Winner Surprised Me"

## Prompt 模板

根据当前 position 选择策略：
- Position 4-6: 强调全面性和深度，使用"完整"、"深度"、"全面"
- Position 7-10: 使用格式化元素（数字、括号、年份），保持简短
- Position 11-15: 使用情感触发和独特角度，大胆差异化
