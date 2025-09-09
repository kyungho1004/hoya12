# -*- coding: utf-8 -*-
"""Graph helpers (skeleton)."""
import matplotlib.pyplot as plt

def simple_trend_plot(values, ylabel="Value"):
    fig = plt.figure()
    plt.plot(range(1, len(values)+1), values, marker='o')
    plt.xlabel("회차")
    plt.ylabel(ylabel)
    plt.title("추이 그래프")
    return fig
