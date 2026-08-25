#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: conversation_app.py
@time: 2025/7/21 15:20
@project: resonant-soul
@desc: 
"""
from api.apps.emotion_app import analyze_emotion, save_emotion_record, generate_emotion_chart
from api.db.services.conversation_service import ConversationService
from api import settings


CRISIS_KEYWORDS = (
    "自杀", "不想活", "结束生命", "伤害自己", "自残", "活不下去", "想死"
)


def _offline_response(user_input, emotions):
    if any(keyword in user_input for keyword in CRISIS_KEYWORDS):
        return (
            "听起来你现在可能正处在危险或非常痛苦的时刻。请先不要独自承受："
            "立即联系身边可信任的人陪着你，并联系当地急救、报警服务或尽快前往最近的急诊。"
            "如果你手边有可能伤害自己的物品，请先把它们移远。你愿意先告诉我，你现在是否处于立即危险中吗？"
        )

    emotion_text = "、".join(emotions)
    return (
        f"我听见了，你的描述里可能有一些{emotion_text}。"
        "谢谢你愿意说出来。我们可以先把此刻最困扰你的事情拆小一点："
        "它是什么时候开始的，最近有什么事情让这种感受变得更强？"
        "（当前为离线演示回复，配置模型密钥后可启用完整 AI 对话。）"
    )


def process_user_input(current_user, user_input, history: list):
    """处理用户输入并返回响应"""
    if not current_user or not current_user.get('id'):
        raise ValueError("请先登录")
    user_input = (user_input or "").strip()
    if not user_input:
        return history, generate_emotion_chart(current_user['id'])

    user_id = current_user['id']
    emotions = analyze_emotion(user_input)
    save_emotion_record(emotions, user_input, user_id)
    print(f"检测到的情绪: {emotions}")

    if any(keyword in user_input for keyword in CRISIS_KEYWORDS) or settings.CHAT_MDL is None:
        response_content = _offline_response(user_input, emotions)
    else:
        from camel.societies import RolePlaying

        task_prompt = (
            "作为支持性倾听的AI心理健康助手，以第一人称与大学生对话。"
            "不得诊断或替代专业治疗；遇到自伤、自杀或他伤风险时优先建议立即寻求现实帮助。"
        )
        role_play_session = RolePlaying(
            assistant_role_name="心灵伙伴AI心理健康助手",
            assistant_agent_kwargs=dict(model=settings.CHAT_MDL),
            user_role_name="在校大学生",
            user_agent_kwargs=dict(model=settings.CHAT_MDL),
            task_prompt=task_prompt,
            with_task_specify=True,
            task_specify_agent_kwargs=dict(model=settings.CHAT_MDL),
            output_language='中文'
        )

        input_msg = role_play_session.init_chat()
        input_msg.content = f"""
        Instruction: 请以心灵伙伴AI心理健康助手的第一人称身份回应。根据检测到的情绪 {emotions}，提供支持性倾听和一般建议，不要做医疗诊断。
        Input: {user_input}
        """

        assistant_response, _ = role_play_session.step(input_msg)
        response_content = assistant_response.msg.content

    # 数据后处理
    if "Solution:" in response_content:
        response_content = response_content.split("Solution:")[1]
        response_content = response_content.split("Next request.")[0].strip()
        response_content = response_content.split("next request.")[0].strip()

    third_person_phrases = [
        "作为心理咨询师，",
        "作为一名心理咨询师，",
        "作为您的心理健康助手，",
        "作为一个AI助手，",
        "作为心灵伙伴，"
    ]

    for phrase in third_person_phrases:
        response_content = response_content.replace(phrase, "")

    # 保存对话记录到数据库
    ConversationService.save_conversation(user_input, response_content, user_id)

    # 返回新的对话历史和情绪图表
    new_history = history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": response_content}
    ]

    return new_history, generate_emotion_chart(user_id)
