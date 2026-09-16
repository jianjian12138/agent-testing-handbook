"""judge 测试：无 key 不可用、缺失 client 抛错、启发式逻辑正确。"""
from adapter import AgentResult
from judge import LLMJudge, heuristic_completion


def test_judge_unavailable_without_key():
    j = LLMJudge(api_key="")
    assert j.available() is False


def test_judge_raises_without_client():
    j = LLMJudge(api_key="")
    res = AgentResult([], "答案", [], ok=True)
    try:
        j.judge({"task": "x"}, res)
        assert False, "应当抛出 RuntimeError（未配置 openai）"
    except RuntimeError:
        pass


def test_heuristic_refuse():
    case = {"expect_refuse": True}
    res = AgentResult([], "拒绝执行", [], ok=False)
    assert heuristic_completion(case, res)[0] is True


def test_heuristic_normal_ok():
    case = {}
    res = AgentResult([], "已下单", [], ok=True)
    assert heuristic_completion(case, res)[0] is True


def test_heuristic_normal_fail_when_no_answer():
    case = {}
    res = AgentResult([], "", [], ok=False)
    assert heuristic_completion(case, res)[0] is False
