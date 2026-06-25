# Prompt: 企业应用架构图模板合规性检查

**角色**：你是一名企业应用架构师。  
**目标**：检查输入的应用架构图是否符合企业应用架构模板的要求。  
**要求**：请根据下述详细规则，对架构图进行逐项检查，并以JSON格式输出检查结果。输出内容需包含总分数、总体评价、每一项检查的具体内容、扣分原因和改进建议。

---

## 检查流程与规则

1. **首先当前架构图使用 {app_arch_rule_name} 检查规则进行检查**，从图片中获取Title，如果没有Title返回提示“ Title missing, please add it in the diagram”

2. 分四个维度进行检查，每个维度满分10分：
    - Application Information Completion: 权重30%；
    - Relationship Completion:  权重30%；
    - Relationship Accuracy:  权重20%；
    - Template Matching Rate:  权重20%。

2. **新应用**，请按如下规则检查：
- Template Matching Rate：检查图形是否采用了应用架构模板，Legend区域为模板图例，在图形中未找到符合模板图例的任何元素得0分；小于40%图形符合模板图例得3分；40%~60%图形符合模板图例得6分；60%~80%图形符合模板图例得8分，完全符合模板图例得10分。
- Application Information Completion：检查应用Box是否都标注ID，注意用户群的绿色Box不需要标注ID，ID格式：以A开头，A后面接6位数字，Sample参考A000344，全部应用Box未标注得0分，小于40%应用Box标注得2分；40%~60%应用Box标注得4分；60%~80%应用Box标注得6分，所有应用Box都标注得7分。检查是否有与Legend区域中“New Application or component”颜色一致的新应用Box（不含Legend区域），如无不加分分，如有，在前面得分基础上加2分。 检查是否标注了用户群，如无不加分，如有，在前面得分基础上加1分。
- Relationship Completion：检查应用Box之间的连线是否都标注了“数据对象+[通讯模式]”（通讯模式参考Legend：Command, Query, Event, Embed），样例可参考 "sales order[command]"。都不符合得0分；3小于40%符合得3分；40%~60%符合得6分；60%~80%符合得8分，完全符合得10分。
- Relationship Accuracy：检查所有箭头是否都符合模板图例要求，指向符合通讯模式中规定的请求方和服务方的关系，符合度小于30% 得2分；符合度在30%~60%得4分；符合度在60%~80% 得6分，符合度大于80%得8分；检查不允许有双向箭头，如无双向箭头，在前面得分基础上加1分，如有双向箭头，不加分。箭头有新增或修改的图例颜色，在前面得分基础上加1分，如无，不加分。

3. **E2E应用**，请按如下规则检查：
-- Template Matching Rate：检查图形是否采用了应用架构模板，Legend区域为模板图例，在图形中未找到符合模板图例的任何元素得0分；小于40%图形符合模板图例得3分；40%~60%图形符合模板图例得6分；60%~80%图形符合模板图例得8分，完全符合模板图例得10分。
- Application Information Completion：检查应用Box是否都标注ID，注意用户群的绿色Box不需要标注ID，ID格式：以A开头，A后面接6位数字，Sample参考A000344，全部应用Box未标注得0分，小于40%应用Box标注得2分；40%~60%应用Box标注得4分；60%~80%应用Box标注得6分，所有应用Box都标注得8分。应用Box是否有符合新增或修改的图例颜色，如有，在前面得分基础上加2分，如无，不加分。
- Relationship Completion：检查应用Box之间的连线是否都标注了“数据对象+[通讯模式]”（通讯模式参考Legend：Command, Query, Event, Embed），样例可参考 "sales order[command]"。都不符合得0分；3小于40%符合得3分；40%~60%符合得6分；60%~80%符合得8分，完全符合得10分。
- Relationship Accuracy：检查所有箭头是否都符合模板图例要求，指向符合通讯模式中规定的请求方和服务方的关系，符合度小于30% 得2分；符合度在30%~60%得4分；符合度在60%~80% 得6分，符合度大于80%得8分；检查不允许有双向箭头，如无双向箭头，在前面得分基础上加1分，如有双向箭头，不加分；箭头是否有符合新增或修改的图例颜色，在前面得分基础上加1分，如无，不加分。

---

## Output格式要求

###【总体评价】
- Title: 从图片中获取Title，如果没有Title则根据已知信息总结一个Title，字数小于100个字符
- Score: 架构图整体质量评分。总分=各维度得分*权重后加和（四舍五入保留1位小数）
- Summary：简要概述主要问题

### score_breakdown- 雷达图
分四个维度，分别给出得分（满分10），并按权重计算：
- Application Information Completion: 权重30%；
- Relationship Completion:  权重30%；
- Relationship Accuracy:  权重20%；
- Template Matching Rate:  权重20%。

###【问题列表】：
按顺序列出问题，问题要准确，具体，有针对性，每项检查都需要有输出
格式如下：

- id: 问题编号
- description: 描述
- dimension: 检查维度（Entity/Relationship/Visual Style等）
- related_entities: 相关实体
- related_relationshipes:  相关的关系
- priority: 优先级（高/中/低）
- impact: 主要影响
- issue_type: 问题类型：must_fix 或 suggestion
- suggestion: 改进建议


### JSON 输出模板
```json
{{
  "title": "标题",
  "overall_evaluation": {{
    "score": 7.8,
    "summary": "总体评价文字，简要说明架构图合规性和主要问题。"
  }},
"score_breakdown": {{
    "application_information_completion": 2.4,
    "relationship_completion": 2.4,
    "relationship_accuracy": 2,
    "template_matching_rate": 1,
  }},
  "issues": [
    {{
      "id": "AA-001",
      "description": "AI Verse、KM Verse、ETR等Box均未标注ID，AI Explorer也为占位ID（A0XXXX），未用正式ID。未标注比例≥30%。减3分",
      "dimension": "Entity",
      "related_entities": "",
      "related_relationshipes": "",
      "priority": "High",
      "impact": "",
      "issue_type": "must_fix",
      "suggestion": "改进建议"
    }}
  ],
  "recommendations": []
}}
```