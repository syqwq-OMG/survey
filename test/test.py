import requests
import string
import random

BASE_URL = "http://127.0.0.1:8000"

# 随机生成用户名，防止重复运行脚本时报错
username = "testuser_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
password = "password123"
token = ""
survey_id = ""

def print_step(title):
    print(f"\n{'='*20} {title} {'='*20}")

def test_auth():
    global token
    print_step("1. 测试用户认证模块")
    
    # 1.1 注册
    res = requests.post(f"{BASE_URL}/api/auth/register", json={"username": username, "password": password})
    assert res.status_code == 200, f"注册失败: {res.text}"
    print(f"✅ 注册成功: {username}")

    # 1.2 登录 (OAuth2 规范需要表单提交)
    res = requests.post(f"{BASE_URL}/api/auth/login", data={"username": username, "password": password})
    assert res.status_code == 200, f"登录失败: {res.text}"
    token = res.json()["access_token"]
    print(f"✅ 登录成功，获取 Token: {token[:15]}...")

def test_survey_creation():
    global survey_id
    print_step("2. 测试问卷创建与发布")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2.1 创建包含复杂校验和跳转逻辑的问卷
    payload = {
        "title": "API自动化测试问卷",
        "description": "用于测试后端的动态校验与跳转逻辑引擎",
        "is_anonymous": True,
        "questions": [
            {
                "q_id": "q1",
                "type": "single",
                "title": "你喜欢Python吗？",
                "is_required": True,
                "options": ["喜欢", "不喜欢"],
                # 跳转逻辑：如果选“不喜欢”，直接跳到 q3，跳过 q2
                "jump_logic": [{"condition_value": "不喜欢", "target_q_id": "q3"}]
            },
            {
                "q_id": "q2",
                "type": "text",
                "title": "为什么喜欢？（最少5个字）",
                "is_required": True, # 注意这里是必填项
                "constraints": {"min_length": 5, "max_length": 100}
            },
            {
                "q_id": "q3",
                "type": "number",
                "title": "给这门课打个分吧 (1-10)",
                "is_required": True,
                "constraints": {"min_value": 1, "max_value": 10, "is_integer": True}
            }
        ]
    }
    
    res = requests.post(f"{BASE_URL}/api/surveys", json=payload, headers=headers)
    assert res.status_code == 200, f"创建问卷失败: {res.text}"
    survey_id = res.json()["id"]
    print(f"✅ 创建问卷成功，ID: {survey_id}")

    # 2.2 发布问卷
    res = requests.put(f"{BASE_URL}/api/surveys/{survey_id}/status", json={"is_active": True}, headers=headers)
    assert res.status_code == 200, f"发布问卷失败: {res.text}"
    print("✅ 问卷发布成功")

def test_responses():
    print_step("3. 测试硬核校验与跳转豁免")
    
    # 3.1 故意提交非法数据 (测试拦截机制)
    invalid_payload = {
        "answers": [
            {"q_id": "q1", "value": "一般般"}, # 不存在的选项
            {"q_id": "q2", "value": "太短"},    # 不满足 min_length=5
            {"q_id": "q3", "value": 100}      # 超过 max_value=10
        ]
    }
    res = requests.post(f"{BASE_URL}/api/surveys/{survey_id}/responses", json=invalid_payload)
    assert res.status_code == 400, "非法数据竟然提交成功了，校验逻辑有 Bug！"
    print(f"✅ 非法数据拦截测试通过: {res.json()['detail']}")

    # 3.2 提交合法数据 (正常流程)
    valid_payload_1 = {
        "answers": [
            {"q_id": "q1", "value": "喜欢"},
            {"q_id": "q2", "value": "因为代码十分优雅"},
            {"q_id": "q3", "value": 9}
        ]
    }
    res = requests.post(f"{BASE_URL}/api/surveys/{survey_id}/responses", json=valid_payload_1)
    assert res.status_code == 200, f"合法数据提交失败: {res.text}"
    print("✅ 合法数据 (正常流程) 提交成功")

    # 3.3 提交合法数据 (触发跳转逻辑豁免)
    # 解析：选了“不喜欢”，q2被跳过。虽然 q2 是必填项，但后端状态机应该豁免它
    valid_payload_2 = {
        "answers": [
            {"q_id": "q1", "value": "不喜欢"},
            # 故意不传 q2，测试后端是否会抛出 400 必填错误
            {"q_id": "q3", "value": 5}
        ]
    }
    res = requests.post(f"{BASE_URL}/api/surveys/{survey_id}/responses", json=valid_payload_2)
    assert res.status_code == 200, f"跳转豁免逻辑失败 (后端误拦截): {res.text}"
    print("✅ 合法数据 (跳转豁免流程) 提交成功，被跳过的必答题完美豁免！")

def test_stats():
    print_step("4. 测试数据统计模块")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = requests.get(f"{BASE_URL}/api/surveys/{survey_id}/stats", headers=headers)
    assert res.status_code == 200, f"获取统计失败: {res.text}"
    
    stats = res.json()
    assert stats["total_submissions"] == 2, "统计份数错误"
    print("✅ 统计获取成功！以下为部分统计数据：")
    
    for q in stats["questions"]:
        if q["type"] == "single":
            print(f"   - 单选题选项统计: {q['option_counts']}")
        elif q["type"] == "number":
            print(f"   - 数字题平均分: {q['average']}")

if __name__ == "__main__":
    print("🚀 开始运行接口自动化测试...")
    try:
        test_auth()
        test_survey_creation()
        test_responses()
        test_stats()
        print_step("🎉 所有 API 测试用例通过！后端逻辑稳如泰山！")
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")