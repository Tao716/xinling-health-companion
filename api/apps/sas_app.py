#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: sas_app.py
@time: 2025/7/21 15:16
@project: resonant-soul
@desc: 
"""
from api.db.services.assessment_service import AssessmentService


def calculate_sas_score(answers):
    """计算五项演示自评得分（第 5 题反向计分）。"""
    if len(answers) != 5 or any(score not in (1, 2, 3, 4) for score in answers):
        raise ValueError("需要提交 5 个 1-4 分的答案")
    normalized = list(answers)
    normalized[4] = 5 - normalized[4]
    return sum(normalized)


def get_sas_result(score):
    """给出演示自评的非诊断性反馈。"""
    if score <= 8:
        return "最近的紧张与不安感较少"
    elif score <= 12:
        return "最近有一些紧张或不安"
    elif score <= 16:
        return "最近较频繁地感到紧张或不安"
    else:
        return "最近的紧张或不安感比较强烈"


def process_sas_scores(user_id, *scores):
    """处理SAS评估分数"""
    normalized_scores = tuple(int(score) for score in scores)
    total_score = calculate_sas_score(normalized_scores)
    result = get_sas_result(total_score)

    if user_id is not None:
        # 保存评估结果到数据库
        AssessmentService.save_assessment(user_id, list(normalized_scores), total_score, result)

        detailed_result = f"""
    评估完成！</br>
    
    您的五项自评得分为: {total_score} / 20</br>
    
    自评反馈: {result}</br>
    
    该功能是产品演示，并非标准 SAS 或其他临床量表，不能用于诊断。</br>
    如果这些感受持续、明显影响生活，建议联系学校心理中心或专业心理/医疗服务。
        """
        return detailed_result
    return None
