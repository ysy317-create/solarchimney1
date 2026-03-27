# -*- coding: utf-8 -*-
"""
热管换热器设计工具 - Streamlit 版本
运行命令：streamlit run this_file.py
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

# 页面配置
st.set_page_config(
    page_title="热管换热器设计工具",
    page_icon="🔥",
    layout="wide"
)

# 标题
st.title("🔥 The web based Design tool")
st.markdown("---")

# 侧边栏参数输入
with st.sidebar:
    st.header("📊 设计参数")
    
    L = st.slider("吸热段长度 L (mm)", 20, 420, 180, 1)
    theta = st.slider("倾斜角度 θ (°)", 0, 89, 55, 1)
    q = st.number_input("加热功率 q (W)", 0, 5000, 1200, 10)
    Tin = st.number_input("入口温度 T_in (°C)", 0.0, 100.0, 25.0, 0.5)
    Tamb = st.number_input("外界温度 T_amb (°C)", -20.0, 50.0, 20.0, 0.5)
    
    st.markdown("---")
    st.subheader("🧩 连接段尺寸（可自定义）")

    n_out = st.number_input("上侧段数 n_out（矩形段数量）", 1, 6, 3, 1)
    n_in = st.number_input("下侧段数 n_in（矩形段数量）", 1, 6, 3, 1)

    st.caption("单位：mm。图形按尺寸缩放显示。")

    # 上侧输入
    st.markdown("**上侧（outer，上管/冷凝段）**")
    Lo = []
    Do = []
    Dco = []  # 连接圆直径（位于矩形之间），长度为 n_out-1
    for j in range(int(n_out)):
        c1, c2 = st.columns(2)
        with c1:
            Lo.append(st.number_input(f"L_o,{j+1} (mm)", 10, 800, 90, 1, key=f"Lo{j}"))
        with c2:
            Do.append(st.number_input(f"D_o,{j+1} (mm)", 6, 80, 18, 1, key=f"Do{j}"))
        if j < int(n_out) - 1:
            Dco.append(st.number_input(f"D_co,{j+1} (mm) 连接圆", 6, 120, 16, 1, key=f"Dco{j}"))

    st.markdown("---")

    # 下侧输入
    st.markdown("**下侧（inner，下管/蒸发段）**")
    Lin = []
    Din = []
    Dci = []
    for j in range(int(n_in)):
        c1, c2 = st.columns(2)
        with c1:
            Lin.append(st.number_input(f"L_in,{j+1} (mm)", 10, 800, 95, 1, key=f"Lin{j}"))
        with c2:
            Din.append(st.number_input(f"D_in,{j+1} (mm)", 6, 80, 18, 1, key=f"Din{j}"))
        if j < int(n_in) - 1:
            Dci.append(st.number_input(f"D_ci,{j+1} (mm) 连接圆", 6, 120, 16, 1, key=f"Dci{j}"))

    # 铰点圆尺寸
    st.markdown("---")
    st.markdown("**铰点圆直径**")
    D_joint_lower = st.number_input("下铰点圆直径 D_joint_in (mm)", 10, 200, 55, 1)
    D_joint_upper = st.number_input("上铰点圆直径 D_joint_out (mm)", 10, 200, 45, 1)
    
    st.markdown("---")
    calc_btn = st.button("📈 开始计算", type="primary", use_container_width=True)
    reset_btn = st.button("🔄 重置参数", use_container_width=True)
    
    if reset_btn:
        st.rerun()

# 主页面布局
col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📋 计算结果")
    
    if calc_btn or 'last_calc' not in st.session_state:
        # 热力学计算
        area = L * 0.02  # 假设宽度20mm
        heat_flux = q / area if area > 0 else 0
        
        # 热阻计算
        R_conv = 0.045
        R_cond = L / (385 * area / 1000) if area > 0 else 0
        R_total = R_conv + R_cond
        
        deltaT = q * R_total
        Tout = Tin + deltaT
        
        # 换热效率
        efficiency = min(92, (q / (800 + q)) * 100) if q > 0 else 0
        
        # 性能系数
        cop = q / max(1, deltaT)
        
        # 保存结果
        st.session_state.last_calc = {
            'L': L, 'theta': theta, 'q': q, 'Tin': Tin, 'Tamb': Tamb,
            'area': area, 'heat_flux': heat_flux, 'deltaT': deltaT,
            'Tout': Tout, 'efficiency': efficiency, 'cop': cop
        }
    
    # 显示结果
    if 'last_calc' in st.session_state:
        res = st.session_state.last_calc
        
        st.markdown("""
        | 参数 | 数值 | 单位 |
        |------|------|------|
        | 吸热段长度 L | {:.1f} | mm |
        | 倾斜角度 θ | {:.1f} | ° |
        | 换热面积 A | {:.3f} | m² |
        | 加热功率 q | {:.0f} | W |
        | 入口温度 T_in | {:.1f} | °C |
        | 外界温度 T_amb | {:.1f} | °C |
        """.format(
            res['L'], res['theta'], res['area'],
            res['q'], res['Tin'], res['Tamb']
        ))

with col2:
    st.subheader("🎨 几何模型（圆-矩-圆-矩 交替）")

    fig, ax = plt.subplots(figsize=(9, 6.2))
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 560)
    ax.set_aspect('equal')
    ax.axis('off')

    # =========================
    # 1) 坐标与比例
    # =========================
    origin_x, origin_y = 210, 390  # 下铰点圆心
    rad = np.radians(theta)

    # 计算 mm->px：根据最长的"上侧/下侧总长度"自适应
    total_out_mm = sum(Lo) + sum(Dco)
    total_in_mm = sum(Lin) + sum(Dci)

    # 斜杆投影也会占空间
    L_mm = float(L)
    canvas_w_px = 860
    denom = max(1.0, max(total_out_mm, total_in_mm) + L_mm * np.cos(rad))
    mm2px = 0.70 * canvas_w_px / denom
    mm2px = np.clip(mm2px, 0.6, 2.4)

    def mm(v):  # mm->px
        return float(v) * mm2px

    # 上铰点圆心
    top_x = origin_x + mm(L_mm) * np.cos(rad)
    top_y = origin_y - mm(L_mm) * np.sin(rad)

    # 上下管所在 y 位置
    lower_line_y = origin_y + 30
    upper_line_y = top_y - 10

    # =========================
    # 2) 绘制辅助函数：圆 + 圆角矩形
    # =========================
    def draw_round_rect(x, y_center, length_px, height_px, color, lw=1.5):
        rect = FancyBboxPatch(
            (x, y_center - height_px/2),
            length_px,
            height_px,
            boxstyle=f"round,pad=0.02,rounding_size={height_px/2}",
            facecolor=color,
            edgecolor="#1f2937",
            linewidth=lw
        )
        ax.add_patch(rect)

    def draw_circle(cx, cy, d_px, color, lw=1.5):
        c = Circle((cx, cy), radius=d_px/2, facecolor=color, edgecolor="#1f2937", linewidth=lw)
        ax.add_patch(c)

    def add_callout(x0, y0, x1, y1, text, fontsize=9):
        ax.plot([x0, x1], [y0, y1], color='#374151', linewidth=1.2)
        ax.text(x1 + 6, y1 + 3, text, fontsize=fontsize, color='#111827')

    # =========================
    # 3) 绘制铰点圆
    # =========================
    draw_circle(origin_x, origin_y, mm(D_joint_lower), color="#2f63b8")
    draw_circle(top_x, top_y, mm(D_joint_upper), color="#c9a15a")

    # =========================
    # 4) 绘制斜杆（双线）
    # =========================
    off = 7
    nx = -np.sin(rad)
    ny = -np.cos(rad)
    ax.plot([origin_x + nx*off, top_x + nx*off],
            [origin_y + ny*off, top_y + ny*off],
            color='#d44b4b', linewidth=4)
    ax.plot([origin_x - nx*off, top_x - nx*off],
            [origin_y - ny*off, top_y - ny*off],
            color='#d44b4b', linewidth=4)

    # 角度弧
    arc_r = 52
    arc_theta = np.linspace(0, rad, 60)
    arc_x = origin_x + arc_r * np.cos(arc_theta)
    arc_y = origin_y - arc_r * np.sin(arc_theta)
    ax.plot(arc_x, arc_y, color='#374151', linewidth=1.5)
    ax.text(origin_x + 58, origin_y - 12, f'θ = {theta}°', fontsize=10)

    # L 标注
    mid_x = (origin_x + top_x) / 2
    mid_y = (origin_y + top_y) / 2
    ax.text(mid_x - 12, mid_y - 14, f'L = {L} mm', fontsize=10, fontweight='bold')

    # =========================
    # 5) 绘制下侧：圆-矩-圆-矩...
    # =========================
    lower_start_x = origin_x + mm(D_joint_lower)/2
    x = lower_start_x
    for j in range(int(n_in)):
        draw_round_rect(
            x=x,
            y_center=lower_line_y,
            length_px=mm(Lin[j]),
            height_px=mm(Din[j]),
            color="#2f63b8"
        )
        add_callout(x + mm(Lin[j])*0.65, lower_line_y, x + mm(Lin[j]) + 120, lower_line_y + 30 + j*18,
                    f"L_in,{j+1}, D_in,{j+1}", fontsize=8)

        x += mm(Lin[j])

        if j < int(n_in) - 1:
            draw_circle(cx=x + mm(Dci[j])/2, cy=lower_line_y, d_px=mm(Dci[j]), color="#1f4f99")
            x += mm(Dci[j])

    # =========================
    # 6) 绘制上侧：圆-矩-圆-矩...
    # =========================
    upper_start_x = top_x + mm(D_joint_upper)/2
    x = upper_start_x
    for j in range(int(n_out)):
        draw_round_rect(
            x=x,
            y_center=upper_line_y,
            length_px=mm(Lo[j]),
            height_px=mm(Do[j]),
            color="#c9a15a"
        )
        add_callout(x + mm(Lo[j])*0.65, upper_line_y, x + mm(Lo[j]) + 140, upper_line_y + 40 - j*18,
                    f"L_o,{j+1}, D_o,{j+1}", fontsize=8)

        x += mm(Lo[j])

        if j < int(n_out) - 1:
            draw_circle(cx=x + mm(Dco[j])/2, cy=upper_line_y, d_px=mm(Dco[j]), color="#b88f45")
            x += mm(Dco[j])

    # =========================
    # 7) 边框
    # =========================
    border_rect = Rectangle((8, 8), 884, 544, fill=False, edgecolor='#e5e7eb', linewidth=1.5)
    ax.add_patch(border_rect)

    st.pyplot(fig)

# 页脚说明
st.markdown("---")
st.caption("💡 提示：图形随参数实时变化，点击「开始计算」查看详细热力分析结果")
