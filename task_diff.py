from typing import List, Literal
import streamlit as st
from dotenv import load_dotenv
from tables import Tasks
from task_loads import find_task, load_all_requests
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

load_dotenv()

font_path = "SimHei.ttf"
font_prop = fm.FontProperties(fname=font_path)


plt.rcParams["font.family"] = font_prop.get_name()
plt.rcParams["font.size"] = 12
plt.rcParams["axes.unicode_minus"] = False


class DiffTask:
    def __init__(self, task: Tasks, requests: List[any]):
        self.task = task
        self.requests = requests


def get_data(task1: DiffTask, task2: DiffTask, compare_field: str):
    data1 = []
    data2 = []
    if compare_field == "first_token_latency_ms":
        data1 = [request.first_token_latency_ms for request in task1.requests]
        data2 = [request.first_token_latency_ms for request in task2.requests]
    else:
        data1 = [request.request_latency_ms for request in task1.requests]
        data2 = [request.request_latency_ms for request in task2.requests]
    return data1, data2


def diff_tasks(
    task_id1: int,
    task_id2: int,
    compare_field: Literal["first_token_latency_ms", "request_latency_ms"],
):

    task_diff1 = create_diff_task(task_id1)
    task_diff2 = create_diff_task(task_id2)

    if len(task_diff1.requests) == 0 or len(task_diff2.requests) == 0:
        st.error("No requests found for the task")
        return

    # if len(task_diff1.requests) != len(task_diff2.requests):
    #     st.error("The number of requests is not the same")
    #     return

    st.markdown(
        f"Click to view task: [`{task_diff2.task.name}`](/?task_id={task_diff2.task.id})",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        compare_latency(task_diff1, task_diff2, compare_field)
        analyze_latency_improvement(task_diff1, task_diff2, compare_field)
        plot_trend_lines(task_diff1, task_diff2, compare_field)


def analyze_latency_improvement(task1: DiffTask, task2: DiffTask, compare_field: str):

    st.write("## 均值和标准差")

    data1, data2 = get_data(task1, task2, compare_field)

    # 计算均值和标准差
    mean1, std1 = np.mean(data1), np.std(data1)
    mean2, std2 = np.mean(data2), np.std(data2)

    # 计算优化程度
    improvement_percentage = ((mean1 - mean2) / mean1) * 100

    # t 检验
    t_stat, p_value = stats.ttest_ind(data1, data2)

    # 输出结果
    st.write(f"`{task1.task.name}` 均值: `{mean1:.2f}`, 标准差: `{std1:.2f}`")
    st.write(f"`{task2.task.name}` 均值: `{mean2:.2f}`, 标准差: `{std2:.2f}`")
    st.write(f"优化程度: `{improvement_percentage:.2f}%`")
    st.write(f"t统计量: `{t_stat:.2f}`, p值: `{p_value:.4f}`")

    # 可视化
    plt.figure(figsize=(12, 6))
    plt.hist(data1, bins=30, alpha=0.5, label=task1.task.name, color="blue")
    plt.hist(data2, bins=30, alpha=0.5, label=task2.task.name, color="orange")
    plt.title(f"{compare_field}", fontproperties=font_prop)
    plt.xlabel("Latency (ms)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid()
    plt.show()
    st.pyplot(plt)

    return {
        "mean_before": mean1,
        "std_before": std1,
        "mean_after": mean2,
        "std_after": std2,
        "improvement_percentage": improvement_percentage,
        "t_stat": t_stat,
        "p_value": p_value,
    }


def compare_latency(task1: DiffTask, task2: DiffTask, compare_field: str):

    data1, data2 = get_data(task1, task2, compare_field)

    improvements = []
    for d1, d2 in zip(data1, data2):
        if d1 != 0:  # 避免除以零
            improvement = ((d1 - d2) / d1) * 100
        else:
            improvement = np.nan  # 如果 d1 为 0，则设为 NaN
        improvements.append(improvement)

    # 计算统计描述
    stats_summary = {
        "平均改进 (%)": np.nanmean(improvements),
        "最大改进 (%)": np.nanmax(improvements),
        "最小改进 (%)": np.nanmin(improvements),
        "P10 (%)": np.nanpercentile(improvements, 10),
        "P50 (%)": np.nanpercentile(improvements, 50),
        "P90 (%)": np.nanpercentile(improvements, 90),
        "P95 (%)": np.nanpercentile(improvements, 95),
        "P99 (%)": np.nanpercentile(improvements, 99),
    }

    st.write("## 逐请求比较结果")
    st.write(
        f"`{task2.task.name}` 相对于 `{task1.task.name}` 的 `{compare_field}` 的改进情况："
    )
    for key, value in stats_summary.items():
        st.write(f"{key}: `{value:.2f}`" if not np.isnan(value) else f"{key}: N/A")


def plot_trend_lines(task1: DiffTask, task2: DiffTask, compare_field: str):
    st.write("## 趋势图")

    data1, data2 = get_data(task1, task2, compare_field)

    plt.figure(figsize=(12, 6))
    plt.plot(
        data1,
        label=task1.task.name,
        color="blue",
        linestyle="-",
        marker="o",
        markersize=3,
    )
    plt.plot(
        data2,
        label=task2.task.name,
        color="orange",
        linestyle="-",
        marker="o",
        markersize=3,
    )
    plt.title(f"{compare_field} Trend", fontproperties=font_prop)
    plt.xlabel("Request Number")
    plt.ylabel(f"{compare_field} (ms)")
    plt.legend()
    plt.grid()
    st.pyplot(plt)


def create_diff_task(task_id: int):
    task = find_task(task_id)
    requests = load_all_requests(task_id)
    requests = [request for request in requests if request.success == 1]
    return DiffTask(task, requests)
