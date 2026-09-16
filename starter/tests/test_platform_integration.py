"""平台集成测试：用修复版 Agent 跑真实回归集，必须全绿。"""
import os

from run_suite import run_suite
from customer_service_agent import run_agent_fixed


def test_fixed_agent_passes_regression():
    # test 文件位于 starter/tests/，上两级即 starter/ 根目录
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = os.path.join(root, "datasets", "regression")
    rep = run_suite(data, run_agent_fixed)
    assert rep, "回归集不应为空"
    assert all(c["passed"] for c in rep), "修复版 Agent 应使回归集全绿"
