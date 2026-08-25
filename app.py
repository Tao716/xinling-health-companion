#!/usr/bin/env python
# encoding: utf-8
"""
@author: Datawhale
@file: main_mind.py
@time: 2025/7/21 13:57
@project: resonant-soul
@desc: 
"""

import os
from pathlib import Path

import gradio as gr

from api import initialize_app
from api.apps.admin_app import get_all_users, update_user_status, delete_user
from api.apps.conversation_app import process_user_input
from api.apps.emotion_app import get_all_emotion_records
from api.apps.sas_app import process_sas_scores
from api.apps.statistics_app import generate_stats_charts, get_stats_text
from api.apps.user_app import user_login, user_register, get_user_info_by_username, update_password, get_user_info_by_id

# 五项情绪状态自评（产品演示，不是标准化临床量表）
sas_questions = [
    "我感到比平常更加紧张和焦虑",
    "我无缘无故地感到害怕",
    "我容易心烦意乱或感到恐慌",
    "我感到我的身体好像被分成几块",
    "我感到一切都很好，不会发生什么不幸"
]

# 放松训练指导内容
relaxation_guides = {
    "呼吸放松": """
    1. 找一个安静、舒适的地方坐下
    2. 缓慢吸气，数4秒
    3. 屏住呼吸，数4秒
    4. 缓慢呼气，数6秒
    5. 重复以上步骤5-10次
    """,
    "渐进性肌肉放松": """
    1. 从脚趾开始，绷紧肌肉5秒
    2. 完全放松10秒
    3. 逐渐向上移动到小腿、大腿
    4. 继续到腹部、胸部、手臂
    5. 最后是面部肌肉
    """,
    "正念冥想": """
    1. 选择一个安静的环境
    2. 采用舒适的坐姿
    3. 闭上眼睛，关注呼吸
    4. 让思绪自然流动
    5. 温和地将注意力带回呼吸
    """
}

is_logged_in = False

initialize_app()

CUSTOM_CSS = (Path(__file__).parent / "assets" / "styles.css").read_text(encoding="utf-8")

BRAND_MARK = """
<div class="brand-lockup">
  <span class="brand-mark" aria-hidden="true"><span></span></span>
  <div><strong>心灵伙伴</strong><small>Resonant Soul</small></div>
</div>
"""


def create_gradio_interface():
    with gr.Blocks(
        title="心灵伙伴 - AI心理健康助手",
        theme=gr.themes.Base(),
        css=CUSTOM_CSS,
        fill_width=True,
    ) as _interface:
        current_user = gr.State({"id": None, "name": None, "is_admin": False})

        # 用户认证面板
        with gr.Column(visible=True, elem_id="auth-panel") as auth_panel:
            with gr.Row(elem_id="auth-shell", equal_height=True):
                gr.HTML(
                    f"""
                    <section class="auth-story">
                      {BRAND_MARK}
                      <div class="auth-copy">
                        <span class="eyebrow">一个可以慢慢说话的地方</span>
                        <h1>此刻的感受，<br><em>值得被认真听见。</em></h1>
                        <p>记录情绪、整理思绪，在需要的时候获得温和而有边界的支持。</p>
                      </div>
                      <div class="mood-orbit" aria-hidden="true">
                        <span class="orbit orbit-one">呼吸</span>
                        <span class="orbit orbit-two">觉察</span>
                        <span class="orbit orbit-three">松弛</span>
                        <span class="sun-face"><i></i><b></b></span>
                      </div>
                      <div class="trust-row"><span>私密记录</span><span>情绪陪伴</span><span>自我关怀</span></div>
                    </section>
                    """,
                    elem_id="auth-story",
                )
                with gr.Column(elem_id="auth-card", min_width=360):
                    gr.HTML("<div class='auth-heading'><span>欢迎回来</span><p>登录或创建账号，继续你的心灵旅程。</p></div>")
                    with gr.Tabs(elem_id="auth-tabs"):
                        with gr.Tab("登录", id="login"):
                            login_username = gr.Textbox(
                                label="用户名",
                                placeholder="请输入用户名",
                                elem_id="login-username",
                            )
                            login_password = gr.Textbox(
                                label="密码",
                                placeholder="请输入密码",
                                type="password",
                                elem_id="login-password",
                            )
                            login_btn = gr.Button("进入心灵空间", variant="primary")
                            login_status = gr.Textbox(
                                label="登录状态",
                                interactive=False,
                                lines=1,
                                max_lines=1,
                                elem_classes=["status-box"],
                            )

                        with gr.Tab("注册", id="register"):
                            register_username = gr.Textbox(label="用户名", placeholder="至少 3 个字符")
                            register_name_nick = gr.Textbox(label="昵称", placeholder="希望我们如何称呼你")
                            register_password = gr.Textbox(
                                label="密码", placeholder="至少 8 位", type="password"
                            )
                            register_btn = gr.Button("创建我的空间", variant="primary")
                            register_status = gr.Textbox(
                                label="注册状态",
                                interactive=False,
                                lines=1,
                                max_lines=1,
                                elem_classes=["status-box"],
                            )
                    gr.HTML("<p class='privacy-note'>你的记录只保存在本项目配置的本地数据库中。</p>")

        with gr.Column(visible=False, elem_id="main_panel") as main_panel:
            with gr.Row(elem_id="topbar"):
                gr.HTML(BRAND_MARK, elem_id="main-brand")
                with gr.Row(elem_id="user-actions"):
                    current_user_display = gr.Markdown("当前用户：未登录", elem_id="user-chip")
                    logout_btn = gr.Button("退出登录", elem_id="logout-btn")
            gr.HTML(
                """
                <section class="workspace-hero">
                  <div>
                    <span class="eyebrow">今天也请对自己温柔一点</span>
                    <h1>给情绪留一点空间。</h1>
                    <p>不用组织好语言，从你此刻最真实的感受开始就可以。</p>
                  </div>
                  <div class="hero-symbol" aria-hidden="true"><span></span></div>
                </section>
                """
            )
            gr.Markdown(
                "**安全提示**　这里提供一般性的情绪支持，不能替代心理咨询、医学诊断或治疗。"
                "如你可能伤害自己或他人，请立即联系可信任的人及当地急救服务。",
                elem_id="safety-note",
            )
            # 主对话选项卡
            with gr.Tabs(elem_id="workspace-tabs"):
              with gr.Tab("陪伴对话"):
                with gr.Row(elem_id="conversation-layout", equal_height=True):
                    with gr.Column(scale=3, elem_id="chat-card"):
                        gr.HTML("<div class='section-heading'><div><span>陪伴对话</span><p>慢慢说，我在这里听。</p></div><i class='online-dot'>在线</i></div>")
                        chatbot = gr.Chatbot(
                            height=430,
                            type='messages',
                            show_label=False,
                            elem_id="companion-chat",
                        )
                        gr.HTML("<div class='prompt-hints'><span>最近有点累</span><span>我想梳理一件事</span><span>陪我做个呼吸</span></div>")
                        input_text = gr.Textbox(
                            label="和心灵伙伴说说",
                            placeholder="从此刻最想说的一句话开始…",
                            show_label=False,
                            submit_btn=True,
                            stop_btn=True,
                            elem_id="message-box",
                        )
                    with gr.Column(scale=1, min_width=280, elem_id="emotion-card"):
                        gr.HTML("<div class='section-heading compact'><div><span>情绪天气</span><p>看见变化，不评判感受。</p></div></div>")
                        emotion_chart = gr.Plot(show_label=False, elem_id="emotion-chart")
                        gr.HTML("<div class='mini-practice'><b>60 秒回到当下</b><p>放松肩膀，吸气 4 秒，呼气 6 秒。</p><span>现在试一试 →</span></div>")

              with gr.Tab("情绪自评"):
                gr.Markdown("## 五项情绪状态自评", elem_classes=["page-title"])
                gr.Markdown("""
                回想最近一周，按照真实感受完成下面五道题。结果只用于自我观察，不能作为诊断依据。
                """, elem_classes=["page-intro"])

                sas_scores = []
                with gr.Column():
                    for i, q in enumerate(sas_questions, 1):
                        sas_scores.append(
                            gr.Slider(
                                minimum=1,
                                maximum=4,
                                step=1,
                                value=1,
                                label=f"{i}. {q}",
                                interactive=True
                            )
                        )
                    sas_submit = gr.Button("查看自评结果", variant="primary")
                    sas_result = gr.Markdown(label="评估结果")

                    def process_sas_scores_wapper(current_user, *sas_scores):
                        user_id = current_user['id']
                        return process_sas_scores(user_id, *sas_scores)

                    sas_submit.click(
                        process_sas_scores_wapper,
                        inputs=[current_user, *sas_scores],
                        outputs=sas_result
                    )

              with gr.Tab("放松练习"):
                gr.Markdown("## 给身体一个暂停键", elem_classes=["page-title"])
                gr.Markdown("选择一种练习，跟着自己的节奏慢慢来。", elem_classes=["page-intro"])
                relaxation_type = gr.Radio(
                    choices=list(relaxation_guides.keys()),
                    label="选择放松训练类型"
                )
                relaxation_guide = gr.Textbox(label="训练指导", value="请选择一种放松训练方式")

              def update_diary(current_user):
                user_id = current_user['id']
                DIARY_ENTRIES = get_all_emotion_records(user_id)
                data = [[entry['date'], entry['content'], ', '.join(entry['emotions'])]
                        for entry in DIARY_ENTRIES]
                return data

              with gr.Tab("情绪日记"):
                gr.Markdown("## 我的情绪日记", elem_classes=["page-title"])
                gr.Markdown("把说过的话留在这里，看看自己如何一步步走过来。", elem_classes=["page-intro"])
                diary_list = gr.Dataframe(
                    headers=["日期", "内容", "情绪"],
                    label="日记记录"
                )
                # 添加刷新按钮
                refresh_diary_btn = gr.Button("刷新日记")
                refresh_diary_btn.click(update_diary,
                                        inputs=current_user,
                                        outputs=diary_list)
                # 在界面加载时更新日记数据
                _interface.load(update_diary,
                                inputs=current_user,
                                outputs=diary_list)

            # 添加统计分析标签页
              with gr.Tab("成长轨迹"):
                gr.Markdown("## 成长轨迹", elem_classes=["page-title"])
                gr.Markdown("用温和的数据视角，观察最近的情绪与对话变化。", elem_classes=["page-intro"])
                stats_plot = gr.Plot()
                refresh_btn = gr.Button("刷新统计数据")

                # 统计信息文本显示
                stats_text = gr.Markdown()

                def update_stats(current_user):
                    user_id = current_user['id']
                    return generate_stats_charts(user_id), get_stats_text(user_id)

                refresh_btn.click(
                    update_stats,
                    inputs=current_user,
                    outputs=[stats_plot, stats_text]
                )
                user_id = current_user.value['id']
                # 初始加载统计数据
                stats_plot.value = generate_stats_charts(user_id)
                stats_text.value = get_stats_text(user_id)

              with gr.Tab("我的空间"):
                gr.Markdown("## 我的空间", elem_classes=["page-title"])
                gr.Markdown("管理账号资料与安全设置。", elem_classes=["page-intro"])

                # 用户信息展示
                with gr.Column():
                    user_info = gr.Textbox(label="用户名", interactive=False)
                    nick_info = gr.Textbox(label="用户昵称", interactive=False)
                    reg_date_info = gr.Textbox(label="注册时间", interactive=False)

                # 密码修改模块
                with gr.Column():
                    with gr.Row():
                        new_password = gr.Textbox(label="新密码", type="password")
                        confirm_password = gr.Textbox(label="确认新密码", type="password")
                    update_pwd_btn = gr.Button("修改密码", variant="primary")
                    pwd_status = gr.Textbox(label="操作结果", interactive=False)

                # 信息更新函数
                def update_user_info(current_user):
                    if current_user is not None:
                        user = get_user_info_by_id(current_user['id'])
                        if user:
                            return [
                                user['username'],
                                user['name'],
                                user['created_at']
                            ]
                    return ["", "", ""]

                # 密码修改处理
                def change_password(current_user, new_pwd, confirm_pwd):
                    if new_pwd != confirm_pwd:
                        return "新密码与确认密码不一致"
                    if len(new_pwd) < 8:
                        return "密码长度至少8位"

                    try:
                        update_password(current_user['id'], new_pwd)
                        return "密码修改成功"
                    except Exception as e:
                        return f"密码修改失败：{str(e)}"

                # 绑定事件
                update_pwd_btn.click(
                    change_password,
                    inputs=[current_user, new_password, confirm_password],
                    outputs=pwd_status
                )

            # 添加管理员标签页
              with gr.Tab("管理后台", visible=False) as admin_tab:
                gr.Markdown("## 用户管理")

                # 用户列表
                users_table = gr.Dataframe(
                    headers=["用户ID", "用户名", "昵称", "状态", "注册时间"],  # 新增操作列
                    label="用户列表",
                    interactive=False,
                    value=[]
                )

                with gr.Row():
                    refresh_users_btn = gr.Button("刷新用户列表", variant="primary")

                with gr.Row():
                    with gr.Column(scale=1):
                        selected_user_id = gr.Number(label="选择用户ID", precision=0, minimum=1, value=2)
                    with gr.Column(scale=1):
                        # 将单选按钮改为操作选择下拉菜单
                        user_actions = gr.Radio(
                            choices=[
                                ("🛑启用用户", "enable"),
                                ("✅禁用用户", "disable"),
                                ("❌删除用户", "delete")
                            ],
                            label="选择操作",
                            type="value"
                        )
                    with gr.Column(scale=1):
                        execute_action_btn = gr.Button("执行操作", variant="secondary")

                operation_status = gr.Textbox(label="操作结果", interactive=False)

                # 更新用户列表函数
                def update_users_list(current_admin):
                    if not current_admin or not current_admin.get('id'):
                        return []
                    admin = get_user_info_by_id(current_admin['id'])
                    if not admin or not admin.get('is_admin'):
                        return []
                    users = get_all_users()
                    if users:
                        return [[
                            user['id'],
                            user['username'],
                            user['name'],
                            user['status'],
                            user['created_at'],
                        ] for user in users]
                    return []

                # 绑定事件
                refresh_users_btn.click(
                    update_users_list,
                    inputs=current_user,
                    outputs=users_table
                )

                # 新增统一操作处理函数
                def handle_user_action(current_admin, user_id, action):
                    admin = get_user_info_by_id(current_admin.get('id')) if current_admin else None
                    if not admin or not admin.get('is_admin'):
                        return "无管理员权限", []
                    if not user_id:
                        return "请选择用户ID", update_users_list(current_admin)
                    try:
                        if action == "disable":
                            result = update_user_status(user_id, False)
                        elif action == "enable":
                            result = update_user_status(user_id, True)
                        elif action == "delete":
                            result = delete_user(user_id)
                        else:
                            return "无效的操作类型", update_users_list(current_admin)

                        if result:
                            return f"操作成功：{action}", update_users_list(current_admin)
                        return "操作失败", update_users_list(current_admin)
                    except Exception as e:
                        return f"操作出错：{str(e)}", update_users_list(current_admin)

                # 绑定新的事件
                execute_action_btn.click(
                    handle_user_action,
                    inputs=[current_user, selected_user_id, user_actions],
                    outputs=[operation_status, users_table]
                )

        # 事件处理
        def login(username, password):
            user_data = user_login(username, password)
            if not user_data:
                return "用户名或密码错误", None
            if user_data.get("error"):
                return user_data["error"], None

            # 获取完整的用户信息
            user = get_user_info_by_username(username)
            return "登录成功", user

        login_event = lambda method: method(
            login,
            inputs=[login_username, login_password],
            outputs=[login_status, current_user]
        ).success(
            # 根据登录结果决定面板显示状态
            lambda status, user: (
                gr.Column(visible=user is None),
                gr.Column(visible=user is not None),
                gr.Tab(visible=user and user.get('is_admin', False))
            ),
            inputs=[login_status, current_user],
            outputs=[auth_panel, main_panel, admin_tab]
        ).success(
            # 更新用户显示
            fn=lambda user: gr.Markdown(
                f"### 当前用户：{user['name']} {'(管理员)' if user.get('is_admin') else ''}"
                if user else "### 当前用户：未登录"
            ),
            inputs=[current_user],
            outputs=current_user_display
        ).success(
            # 更新用户信息
            fn=update_user_info,
            inputs=current_user,
            outputs=[user_info, nick_info, reg_date_info]
        ).success(
            fn=update_diary,
            inputs=current_user,
            outputs=diary_list
        ).success(
            # 如果是管理员，刷新用户列表
            fn=lambda user: update_users_list(user) if user and user.get('is_admin') else [],
            inputs=[current_user],
            outputs=users_table
        )

        # 应用统一处理到两个登录入口
        login_event(login_btn.click)
        login_event(login_password.submit)

        def logout():
            return (
                {"id": None, "name": None, "is_admin": False},
                gr.Column(visible=True),
                gr.Column(visible=False),
            )

        logout_btn.click(
            fn=logout,
            inputs=None,
            outputs=[current_user, auth_panel, main_panel],
        )

        # 注册功能事件绑定
        def register(username, name_nick, password):
            if len((username or "").strip()) < 3:
                return "注册失败：用户名至少 3 个字符", None
            if len(password or "") < 8:
                return "注册失败：密码至少 8 位", None
            if not (name_nick or "").strip():
                return "注册失败：请填写昵称", None
            result = user_register(username, name_nick, password)
            if result and 'id' in result:
                return "注册成功", result
            return "注册失败，用户名已存在", None

        register_btn.click(
            register,
            inputs=[register_username, register_name_nick, register_password],
            outputs=[register_status, current_user]
        ).success(
            # 根据注册结果动态显示面板
            lambda status, user: (gr.Column(visible=user is None), gr.Column(visible=user is not None)),
            inputs=[register_status, current_user],
            outputs=[auth_panel, main_panel]
        ).success(
            # 添加空值检查
            fn=lambda user: gr.Markdown(f"### 当前用户：{user['name']}" if user else "### 当前用户：未登录"),
            inputs=[current_user],
            outputs=current_user_display
        ).success(
            # 更新用户信息
            fn=update_user_info,
            inputs=current_user,
            outputs=[user_info, nick_info, reg_date_info]
        )

        def update_relaxation_guide(choice):
            return relaxation_guides.get(choice, "请选择一种放松训练方式")

        # 绑定事件
        relaxation_type.change(update_relaxation_guide, relaxation_type, relaxation_guide)

        # 主对话功能
        welcome_message = "你好！我是你的心灵伙伴，很高兴能和你交流。请告诉我你最近的感受或者有什么想聊的？"

        def set_welcome_message():
            return [{"role": "assistant", "content": welcome_message}]

        input_text.submit(
            fn=process_user_input,
            inputs=[current_user, input_text, chatbot],
            outputs=[chatbot, emotion_chart],
            queue=False
        ).then(
            fn=lambda: "",
            inputs=None,
            outputs=input_text,
            queue=False
        ).then(
            fn=update_diary,
            inputs=current_user,
            outputs=diary_list
        )

        # 在界面加载时设置欢迎消息
        _interface.load(set_welcome_message, outputs=chatbot)

    return _interface


interface = create_gradio_interface()


if __name__ == "__main__":
    interface.queue().launch(
        server_name=os.getenv("HOST", "127.0.0.1"),
        server_port=int(os.getenv("PORT", "7860")),
        share=os.getenv("GRADIO_SHARE", "false").lower() == "true",
    )
