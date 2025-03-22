import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, date

from src.fund_data import get_fund_data, get_fund_info

# 自定义CSS样式
def load_css():
    """加载自定义CSS样式"""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        background-color: white;
        padding: 1rem 0;
    }
    .fixed-top {
        position: sticky;
        top: 0;
        background-color: white;
        z-index: 999;
        padding: 1rem 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 2rem;
    }
    .input-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        margin: 1.5rem 0;
    }
    .sidebar-header {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        height: 42px;  /* 与输入框高度保持一致 */
    }
    /* 确保查询基金按钮和输入框的高度一致 */
    .stButton[data-testid*="query_fund_button"]>button {
        margin-top: 24px;
        height: 40px !important;
    }
    /* 确保输入框和查询按钮水平对齐 */
    div[data-testid="column"]:has(button[kind="secondaryFormSubmit"][data-testid*="query_fund_button"]) {
        margin-top: -0px !important;
        align-self: end;
    }
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
        margin-top: 0.5rem;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    /* 确保输入框和按钮在同一水平线上 */
    div.row-widget.stTextInput {
        margin-bottom: 0;
    }
    /* 自选基金卡片样式 */
    .fund-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        background-color: white;
        height: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .fund-card h4 {
        margin: 0 0 1rem 0;
        font-size: 1.1rem;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .fund-card p {
        margin: 0.5rem 0;
        color: #666;
        font-size: 0.9rem;
    }
    .fund-card .info-row {
        display: flex;
        justify-content: space-between;
        margin: 0.5rem 0;
    }
    .fund-card .update-time {
        color: #999;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    .fund-card .button-group {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    /* 持仓页面特殊样式 */
    .portfolio-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
    }
    .portfolio-summary {
        background: #f9f9f9;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .total-investment,
    .total-value,
    .total-profit {
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    .total-profit.positive {
        color: red;
    }
    .total-profit.negative {
        color: green;
    }
    .profit-percentage {
        font-size: 0.9rem;
        color: #555;
    }
    .input-group {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 1rem;
    }
    .input-group .fund-code-column {
        flex: 3;
    }
    .input-group .query-button-column {
        flex: 1;
    }
    </style>
    """, unsafe_allow_html=True)

def display_fund_analysis(df, fund_info, show_header=True):
    """显示基金分析内容"""
    if show_header:
        st.markdown('<h2 class="section-header">基金基本信息</h2>', unsafe_allow_html=True)
    
    # 显示基金基本信息
    col1, col2 = st.columns(2)
    with col1:
        # 处理基金名称，移除代码部分
        fund_name = fund_info.get('fund_name', '未获取到')
        if '(' in fund_name:
            fund_name = fund_name.split('(')[0]
        elif '（' in fund_name:
            fund_name = fund_name.split('（')[0]
        st.markdown(f"**基金名称：** {fund_name}")
        st.markdown(f"**基金公司：** {fund_info.get('fund_company', '未获取到')}")
        st.markdown(f"**基金经理：** {fund_info.get('fund_manager', '未获取到')}")
    with col2:
        st.markdown(f"**基金代码：** {fund_info.get('fund_code', '未获取到')}")
        st.markdown(f"**基金类型：** {fund_info.get('fund_type', '未获取到')}")
        
        # 修改申购状态显示逻辑
        is_buy = fund_info.get('is_buy')
        if is_buy is True:
            purchase_status = "可申购"
        elif is_buy is False:
            purchase_status = "暂停申购"
        else:
            purchase_status = "未知"
            
        st.markdown(f"**申购状态：** {purchase_status}")
        st.markdown(f"**最小申购金额：** {fund_info.get('min_purchase', 0)}元")
    
    # 添加更多信息部分
    with st.expander("更多基金信息", expanded=False):
        # 显示投资主题信息（如果有）
        themes = fund_info.get('investment_themes', [])
        if themes:
            st.markdown("**投资主题：**")
            theme_str = ", ".join([theme.get('name', '') for theme in themes])
            st.markdown(f"{theme_str}")
        
        # 显示其他名称（如果有）
        other_name = fund_info.get('other_name', '')
        if other_name:
            st.markdown(f"**别名/其他名称：** {other_name}")
        
        # 显示最近更新日期（如果有）
        update_date = fund_info.get('update_date', '')
        if update_date:
            st.markdown(f"**数据更新日期：** {update_date}")
        
        # 显示基金公司ID（如果有）
        fund_company_id = fund_info.get('fund_company_id', '')
        if fund_company_id:
            st.markdown(f"**基金公司ID：** {fund_company_id}")
    
    # 显示基金数据分析结果
    st.markdown('<h2 class="section-header">净值走势</h2>', unsafe_allow_html=True)
    
    # 创建净值走势图
    fig = go.Figure()
    
    # 根据基金类型显示不同的数据
    is_money_fund = fund_info.get('is_money_fund', False)
    if is_money_fund:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['nav'],
            mode='lines',
            name='每万份收益',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(
            title='每万份收益走势图',
            xaxis_title='日期',
            yaxis_title='每万份收益（元）',
            hovermode='x unified',
            showlegend=True,
            height=500
        )
    else:
        # 使用累计净值替代单位净值
        if 'acc_nav' in df.columns and not df['acc_nav'].isna().all():
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['acc_nav'],
                mode='lines',
                name='累计净值',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.update_layout(
                title='基金累计净值走势图',
                xaxis_title='日期',
                yaxis_title='累计净值',
                hovermode='x unified',
                showlegend=True,
                height=500
            )
        else:
            # 如果没有累计净值数据，则使用单位净值
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['nav'],
                mode='lines',
                name='单位净值',
                line=dict(color='#1f77b4', width=2)
            ))
            fig.update_layout(
                title='基金净值走势图 (累计净值数据不可用，显示单位净值)',
                xaxis_title='日期',
                yaxis_title='单位净值',
                hovermode='x unified',
                showlegend=True,
                height=500
            )
    
    # 显示图表
    st.plotly_chart(fig, use_container_width=True)
    
    # 基本统计信息
    st.markdown('<h2 class="section-header">基金统计信息</h2>', unsafe_allow_html=True)
    
    # 计算统计指标
    latest_date = df['date'].max()
    latest_nav = df['nav'].iloc[-1]
    establishment_date = df['date'].min()
    
    if is_money_fund:
        # 计算七日年化收益率
        last_7_days = df[df['date'] > latest_date - pd.Timedelta(days=7)]['nav']
        seven_day_sum = last_7_days.sum()
        seven_day_return = (seven_day_sum / 10000) * 100  # 七日累计收益率
        seven_day_annual = (pow(1 + seven_day_return/100, 365/7) - 1) * 100  # 七日年化收益率
        
        # 计算历史七日年化收益率序列
        df['rolling_7day_sum'] = df['nav'].rolling(window=7).sum()
        df['rolling_7day_return'] = (df['rolling_7day_sum'] / 10000) * 100
        df['rolling_7day_annual'] = (pow(1 + df['rolling_7day_return']/100, 365/7) - 1) * 100
        
        max_7day_annual = df['rolling_7day_annual'].max()
        min_7day_annual = df['rolling_7day_annual'].min()
        
        # 显示统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"最新每万份收益（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}元")
        with col2:
            st.metric("七日年化收益率", f"{seven_day_annual:.2f}%")
        with col3:
            st.metric(f"历史最高七日年化（{df.loc[df['rolling_7day_annual'].idxmax(), 'date'].strftime('%Y-%m-%d')}）", f"{max_7day_annual:.2f}%")
        with col4:
            st.metric(f"历史最低七日年化（{df.loc[df['rolling_7day_annual'].idxmin(), 'date'].strftime('%Y-%m-%d')}）", f"{min_7day_annual:.2f}%")
        
        # 显示额外的统计信息
        st.markdown("---")
        st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
    else:
        # 非货币基金的原有统计逻辑
        nav_change = (df['nav'].iloc[-1] / df['nav'].iloc[0] - 1) * 100
        max_nav = df['nav'].max()
        max_nav_date = df[df['nav'] == max_nav]['date'].iloc[0]
        min_nav = df['nav'].min()
        min_nav_date = df[df['nav'] == min_nav]['date'].iloc[0]
        total_return = ((df['nav'].iloc[-1] / df['nav'].iloc[0]) - 1) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"最新净值（{latest_date.strftime('%Y-%m-%d')}）", f"{latest_nav:.4f}")
        with col2:
            st.metric("累计收益（最新净值/首日净值-1）", f"{nav_change:.2f}%")
        with col3:
            st.metric(f"历史最高（{max_nav_date.strftime('%Y-%m-%d')}）", f"{max_nav:.4f}")
        with col4:
            st.metric(f"历史最低（{min_nav_date.strftime('%Y-%m-%d')}）", f"{min_nav:.4f}")
        
        st.markdown("---")
        st.markdown(f"**基金成立日期：** {establishment_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**最新数据日期：** {latest_date.strftime('%Y-%m-%d')}")
        st.markdown(f"**成立至今累计收益：** {total_return:.2f}%")
    
    # 添加基金投资天数指标分析
    st.markdown('<h2 class="section-header">基金投资天数指标分析</h2>', unsafe_allow_html=True)
    
    # 日期选择
    col1, col2 = st.columns([2, 3])
    with col1:
        st.markdown("#### 选择投资区间")
    with col2:
        # 快速选择按钮
        period_cols = st.columns(7)
        periods = {
            "近一周": 7,
            "近一月": 30,
            "近三月": 90,
            "近半年": 180,
            "近一年": 365,
            "近两年": 730,
            "近三年": 1095
        }
        
        def update_date_range(days):
            # 使用当前选择的结束日期，而不是数据集的最大日期
            current_end_date = st.session_state.get('end_date_input', df['date'].max().date())
            # 转换为datetime以便进行日期计算
            current_end_date = pd.to_datetime(current_end_date)
            start_date = current_end_date - pd.Timedelta(days=days)
            # 确保开始日期不早于基金成立日期
            if start_date < df['date'].min():
                start_date = df['date'].min()
            st.session_state.start_date = start_date.date()
            st.session_state.end_date = current_end_date.date()
        
        for i, (period_name, days) in enumerate(periods.items()):
            with period_cols[i]:
                if st.button(period_name, key=f"period_{days}"):
                    update_date_range(days)
    
    # 日期选择器
    date_cols = st.columns(2)
    with date_cols[0]:
        start_date = st.date_input(
            "开始日期",
            min_value=establishment_date.date(),
            max_value=latest_date.date(),
            value=st.session_state.start_date or establishment_date.date(),
            key="start_date_input"
        )
    with date_cols[1]:
        end_date = st.date_input(
            "结束日期",
            min_value=establishment_date.date(),
            max_value=latest_date.date(),
            value=st.session_state.end_date or latest_date.date(),
            key="end_date_input"
        )
    
    # 转换日期为datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # 获取选定期间的数据
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    period_df = df.loc[mask].copy()
    
    # 在投资区间信息上方添加两个图表：收益率曲线图和单位净值曲线图
    if not period_df.empty and start_date <= end_date and not is_money_fund:
        # 1. 收益率曲线图（从起始日期0%开始，用累计净值计算）
        if 'acc_nav' in period_df.columns and not period_df['acc_nav'].isna().all():
            # 计算累计收益率曲线
            start_acc_nav = period_df['acc_nav'].iloc[0]
            period_df['return_rate'] = (period_df['acc_nav'] / start_acc_nav - 1) * 100
            
            # 绘制收益率曲线图
            fig_return = go.Figure()
            fig_return.add_trace(go.Scatter(
                x=period_df['date'],
                y=period_df['return_rate'],
                mode='lines',
                name='收益率曲线',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_return.update_layout(
                title='投资区间收益率曲线',
                xaxis_title='日期',
                yaxis_title='收益率(%)',
                hovermode='x unified',
                showlegend=True,
                height=400
            )
            # 添加零线以便参考
            fig_return.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_return, use_container_width=True)
        else:
            # 如果没有累计净值数据，则使用单位净值
            start_nav = period_df['nav'].iloc[0]
            period_df['return_rate'] = (period_df['nav'] / start_nav - 1) * 100
            
            # 绘制收益率曲线图
            fig_return = go.Figure()
            fig_return.add_trace(go.Scatter(
                x=period_df['date'],
                y=period_df['return_rate'],
                mode='lines',
                name='收益率曲线 (使用单位净值计算)',
                line=dict(color='#ff7f0e', width=2)
            ))
            fig_return.update_layout(
                title='投资区间收益率曲线 (使用单位净值计算)',
                xaxis_title='日期',
                yaxis_title='收益率(%)',
                hovermode='x unified',
                showlegend=True,
                height=400
            )
            # 添加零线以便参考
            fig_return.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
            st.plotly_chart(fig_return, use_container_width=True)
        
        # 2. 单位净值曲线图（显示选定区间的单位净值）
        fig_nav = go.Figure()
        fig_nav.add_trace(go.Scatter(
            x=period_df['date'],
            y=period_df['nav'],
            mode='lines',
            name='单位净值',
            line=dict(color='#2ca02c', width=2)
        ))
        fig_nav.update_layout(
            title='投资区间单位净值曲线',
            xaxis_title='日期',
            yaxis_title='单位净值',
            hovermode='x unified',
            showlegend=True,
            height=400
        )
        st.plotly_chart(fig_nav, use_container_width=True)
    
    if not period_df.empty and start_date <= end_date:
        # 计算投资天数
        trading_days = len(period_df)
        calendar_days = (end_date - start_date).days + 1
        
        if is_money_fund:
            # 计算货币基金的收益指标
            total_income = period_df['nav'].sum()  # 区间内每日万份收益之和
            cumulative_return = (total_income / 10000) * 100  # 累计收益率
            annual_return = (pow(1 + cumulative_return/100, 365/calendar_days) - 1) * 100  # 年化收益率
            
            # 显示指标分析结果
            st.markdown("### 投资区间基本信息")
            st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
            
            st.markdown("### 收益类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("年化收益率", f"{annual_return:.2f}%",
                        help="年化收益率 = (1 + 累计收益率)^(365/投资天数) - 1")
            with col2:
                st.metric("区间累计收益率", f"{cumulative_return:.2f}%",
                        help="累计收益率 = (区间内每日万份收益之和/10000) × 100%")
        else:
            # 非货币基金的原有计算逻辑
            period_return = (period_df['nav'].iloc[-1] / period_df['nav'].iloc[0] - 1) * 100
            annual_return = (pow(1 + period_return/100, 252/trading_days) - 1) * 100
            
            # 计算风险类指标
            period_df['daily_return'] = period_df['nav'].pct_change()
            # 计算区间波动率
            mean_return = period_df['daily_return'].mean()
            volatility = np.sqrt(((period_df['daily_return'] - mean_return) ** 2).sum() / (trading_days - 1)) * 100
            
            period_df['rolling_max'] = period_df['nav'].expanding().max()
            period_df['drawdown'] = (period_df['nav'] - period_df['rolling_max']) / period_df['rolling_max'] * 100
            max_drawdown = abs(period_df['drawdown'].min())
            
            # 显示指标分析结果
            st.markdown("### 投资区间基本信息")
            st.markdown(f"- **投资天数：** {calendar_days}天（其中交易日{trading_days}天）")
            st.markdown(f"- **区间起始净值：** {period_df['nav'].iloc[0]:.4f}")
            st.markdown(f"- **区间结束净值：** {period_df['nav'].iloc[-1]:.4f}")
            
            st.markdown("### 收益类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("年化收益率", f"{annual_return:.2f}%",
                        help="年化收益率 = (1 + 期间总收益率)^(252/投资天数) - 1")
            with col2:
                st.metric("区间累计收益率", f"{period_return:.2f}%",
                        help="累计收益率 = (期末净值 - 期初净值) / 期初净值")
            
            st.markdown("### 风险类指标")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("区间波动率", f"{volatility:.2f}%",
                        help="波动率 = √(Σ(日收益率 - 平均收益率)²/(交易天数-1))")
            with col2:
                st.metric("最大回撤", f"{max_drawdown:.2f}%",
                        help="最大回撤 = (期间最高点净值 - 期间最低点净值) / 期间最高点净值")
    else:
        st.error("请选择有效的投资区间")

# 基金持仓相关组件

# 持仓数据文件路径
PORTFOLIO_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "portfolio.json")

def load_portfolio():
    """从本地文件加载基金持仓数据"""
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_portfolio(portfolio_data):
    """保存基金持仓数据到本地文件"""
    with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio_data, f, ensure_ascii=False, indent=2)

def display_portfolio_summary(portfolio_data):
    """显示投资组合总体情况"""
    if not portfolio_data:
        st.info("您还没有添加任何基金持仓，请点击\"添加基金\"按钮开始构建您的投资组合。")
        return
    
    # 计算总体情况
    total_investment = sum(item.get('amount', 0) for item in portfolio_data)
    total_current_value = sum(item.get('current_value', 0) for item in portfolio_data)
    total_profit = total_current_value - total_investment
    profit_percentage = (total_profit / total_investment * 100) if total_investment > 0 else 0
    
    # 显示总体情况
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="总投资金额", 
            value=f"¥{total_investment:.2f}",
        )
    with col2:
        st.metric(
            label="当前总价值", 
            value=f"¥{total_current_value:.2f}",
        )
    with col3:
        # 修改颜色逻辑：盈利为红色，亏损为绿色
        profit_color = "inverse" if total_profit > 0 else "normal" if total_profit < 0 else "off"
        profit_sign = "+" if total_profit >= 0 else ""
        st.metric(
            label="总盈亏", 
            value=f"¥{total_profit:.2f}",
            delta=f"{profit_sign}{profit_percentage:.2f}%",
            delta_color=profit_color
        )

def display_fund_card(fund_item, index, refresh_callback):
    """显示单个基金持仓卡片"""
    with st.container():
        st.markdown(f"""
        <div class="fund-card">
            <h4>{fund_item.get('fund_name', '未知基金')} ({fund_item.get('fund_code', '')})</h4>
            <div class="info-row">
                <div>购买金额: ¥{fund_item.get('amount', 0):.2f}</div>
                <div>购买日期: {fund_item.get('purchase_date', '')}</div>
            </div>
            <div class="info-row">
                <div>持有份额: {fund_item.get('shares', 0):.2f}</div>
                <div>成本单价: {fund_item.get('cost_per_unit', 0):.4f}</div>
            </div>
            <div class="info-row">
                <div>当前净值: {fund_item.get('net_value', 0):.4f}</div>
                <div>当前价值: ¥{fund_item.get('current_value', 0):.2f}</div>
            </div>
            <div class="info-row">
                <div style="color: {'red' if fund_item.get('profit', 0) > 0 else 'green' if fund_item.get('profit', 0) < 0 else 'black'}">
                    盈亏: {'+'if fund_item.get('profit', 0) >= 0 else ''}{fund_item.get('profit', 0):.2f} 
                    ({'+'if fund_item.get('profit_percentage', 0) >= 0 else ''}{fund_item.get('profit_percentage', 0):.2f}%)
                </div>
                <div class="update-time">上次更新: {fund_item.get('update_time', '未更新')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("编辑", key=f"edit_{index}", use_container_width=True):
                st.session_state.edit_fund_index = index
                st.session_state.show_edit_form = True
                st.rerun()
        with col2:
            if st.button("删除", key=f"delete_{index}", use_container_width=True):
                if 'portfolio' in st.session_state:
                    st.session_state.portfolio.pop(index)
                    save_portfolio(st.session_state.portfolio)
                    refresh_callback()
                    st.rerun()

def add_edit_fund_form(is_edit=False, fund_index=None, fund_code=None, skip_input=False):
    """添加或编辑基金表单"""
    # 初始化表单数据和会话状态
    fund_data = {}
    if is_edit and fund_index is not None and 'portfolio' in st.session_state:
        if 0 <= fund_index < len(st.session_state.portfolio):
            fund_data = st.session_state.portfolio[fund_index]
    
    # 初始化表单的会话状态
    if 'form_fund_code' not in st.session_state:
        st.session_state.form_fund_code = fund_data.get('fund_code', '')
    if 'form_purchase_amount' not in st.session_state:
        st.session_state.form_purchase_amount = float(fund_data.get('amount', 1000.0))
    if 'form_purchase_date' not in st.session_state:
        default_date = datetime.strptime(fund_data.get('purchase_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if 'purchase_date' in fund_data else datetime.now().date()
        st.session_state.form_purchase_date = default_date
    if 'form_cost_per_unit' not in st.session_state:
        st.session_state.form_cost_per_unit = float(fund_data.get('cost_per_unit', 0))
    if 'form_date_confirmed' not in st.session_state:
        st.session_state.form_date_confirmed = False
    if 'temp_fund_info' not in st.session_state and fund_code:
        # 如果有fund_code但没有缓存的fund_info，尝试获取
        try:
            fund_info = get_fund_info(fund_code)
            if fund_info and 'fund_name' in fund_info:
                st.session_state.temp_fund_info = fund_info
        except:
            pass
    
    # 如果提供了fund_code参数，则使用它
    if fund_code:
        st.session_state.form_fund_code = fund_code
    
    # 标题已从调用者处添加，这里不再需要
    if not skip_input:
        # 表单标题
        st.markdown(f"## {'编辑' if is_edit else '添加'}基金持仓")
        
        # 定义回调函数保存表单字段状态
        def on_fund_code_change():
            st.session_state.form_fund_code = st.session_state.portfolio_fund_code
        
        # 基金代码输入和查询
        col1, col2 = st.columns([3, 1])
        with col1:
            fund_code = st.text_input(
                "基金代码", 
                value=st.session_state.form_fund_code,
                placeholder="请输入6位基金代码",
                key="portfolio_fund_code",
                on_change=on_fund_code_change
            )
        with col2:
            query_button = st.button("查询基金", key="query_fund_button", use_container_width=True)
    else:
        # 使用预先提供的fund_code或session_state中的值
        fund_code = st.session_state.form_fund_code
        query_button = False  # 不自动触发查询，因为已在portfolio_page中处理
    
    # 定义回调函数保存表单字段状态
    def on_purchase_amount_change():
        st.session_state.form_purchase_amount = st.session_state.portfolio_purchase_amount
    
    def on_purchase_date_change():
        st.session_state.form_purchase_date = st.session_state.portfolio_purchase_date
        # 日期变更时，重置确认状态
        st.session_state.form_date_confirmed = False
    
    def on_cost_per_unit_change():
        st.session_state.form_cost_per_unit = st.session_state.portfolio_cost_per_unit
        
    fund_info = None
    is_valid_fund = False
    
    # 查询基金信息
    if query_button and fund_code:
        try:
            with st.spinner("正在查询基金信息..."):
                # 保存用户已输入的值到会话状态
                st.session_state.form_fund_code = fund_code
                
                fund_info = get_fund_info(fund_code)
                if fund_info and 'fund_name' in fund_info:
                    is_valid_fund = True
                    st.session_state.temp_fund_info = fund_info
                    # 确保查询阶段被标记为完成
                    st.session_state.query_stage_completed = True
                    st.success(f"查询成功: {fund_info.get('fund_name', '未知基金')}")
                else:
                    st.error("未能查询到基金信息，请检查基金代码是否正确")
                
                # 重置日期确认状态
                st.session_state.form_date_confirmed = False
                st.rerun()
        except Exception as e:
            st.error(f"查询基金信息时出错: {str(e)}")
    
    # 如果是编辑模式或者已经查询到基金信息
    is_valid_fund = is_valid_fund or (is_edit and fund_data.get('fund_code')) or 'temp_fund_info' in st.session_state
    
    if is_valid_fund:
        # 如果是新查询的基金信息，使用查询结果；否则使用已有数据
        fund_name = ""
        if 'temp_fund_info' in st.session_state:
            fund_info = st.session_state.temp_fund_info
            fund_name = fund_info.get('fund_name', '未知基金')
        else:
            fund_name = fund_data.get('fund_name', '未知基金')
        
        # 显示基金信息卡片
        st.markdown(f"""
        <div style="background-color: #e6f7e6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <div style="font-weight: bold; font-size: 16px;">查询成功: {fund_name}</div>
            <div style="font-size: 14px; color: #666;">基金代码: {fund_code}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 输入购买金额和购买日期
        col1, col2 = st.columns(2)
        with col1:
            purchase_amount = st.number_input(
                "购买金额 (元)", 
                min_value=0.01,
                value=st.session_state.form_purchase_amount,
                step=100.0,
                format="%.2f",
                key="portfolio_purchase_amount",
                on_change=on_purchase_amount_change
            )
        with col2:
            purchase_date = st.date_input(
                "购买日期",
                value=st.session_state.form_purchase_date,
                key="portfolio_purchase_date",
                on_change=on_purchase_date_change
            )
            
        # 日期确认和持仓成本单价
        if not st.session_state.form_date_confirmed:
            # 如果日期未确认，查询对应日期的净值
            date_confirm = st.button("确认购买日期", key="confirm_date_button", use_container_width=True)
            if date_confirm:
                try:
                    with st.spinner(f"正在获取 {purchase_date.strftime('%Y-%m-%d')} 的基金净值..."):
                        # 保存当前输入的购买金额和日期
                        st.session_state.form_purchase_amount = purchase_amount
                        st.session_state.form_purchase_date = purchase_date
                        
                        df = get_fund_data(fund_code)
                        # 查找最接近选择日期的净值
                        df['date'] = pd.to_datetime(df['date'])
                        date_mask = df['date'] <= pd.to_datetime(purchase_date)
                        if date_mask.any():
                            closest_date_record = df[date_mask].iloc[-1]
                            closest_date = closest_date_record['date'].date()
                            
                            # 获取净值（优先使用DWJZ，没有则使用nav）
                            if 'DWJZ' in closest_date_record:
                                net_value = float(closest_date_record['DWJZ'])
                            elif 'nav' in closest_date_record:
                                net_value = float(closest_date_record['nav'])
                            else:
                                net_value = 0
                            
                            # 保存持仓成本单价
                            st.session_state.form_cost_per_unit = net_value
                            # 设置日期已确认
                            st.session_state.form_date_confirmed = True
                            
                            st.success(f"已获取到 {closest_date.strftime('%Y-%m-%d')} 的净值: {net_value:.4f}")
                            # 使用st.rerun刷新页面状态
                            st.rerun()
                        else:
                            st.error(f"未找到 {purchase_date.strftime('%Y-%m-%d')} 或之前的基金净值数据")
                except Exception as e:
                    st.error(f"获取基金净值时出错: {str(e)}")
        else:
            # 如果日期已确认，显示持仓成本单价输入并允许修改
            st.success(f"购买日期已确认，您可以继续完成设置")
            cost_per_unit = st.number_input(
                "持仓成本单价", 
                min_value=0.0001,
                value=st.session_state.form_cost_per_unit,
                step=0.0001,
                format="%.4f",
                key="portfolio_cost_per_unit",
                on_change=on_cost_per_unit_change,
                help="购买日期对应的基金净值，可手动修改"
            )
            
            # 重置按钮，允许用户重新选择日期
            if st.button("重新选择日期", key="reset_date_button"):
                st.session_state.form_date_confirmed = False
                st.rerun()
        
        # 保存或更新按钮，只有在日期确认后才启用
        col1, col2 = st.columns(2)
        with col1:
            if st.button("取消", key="cancel_button", use_container_width=True):
                st.session_state.show_edit_form = False
                st.session_state.edit_fund_index = None
                st.session_state.query_stage_completed = False
                
                # 清除表单状态
                if 'temp_fund_info' in st.session_state:
                    del st.session_state.temp_fund_info
                if 'form_fund_code' in st.session_state:
                    del st.session_state.form_fund_code
                if 'form_purchase_amount' in st.session_state:
                    del st.session_state.form_purchase_amount
                if 'form_purchase_date' in st.session_state:
                    del st.session_state.form_purchase_date
                if 'form_cost_per_unit' in st.session_state:
                    del st.session_state.form_cost_per_unit
                if 'form_date_confirmed' in st.session_state:
                    del st.session_state.form_date_confirmed
                st.rerun()
        
        with col2:
            save_button = st.button(
                "保存", 
                key="save_button", 
                type="primary", 
                use_container_width=True,
                disabled=not st.session_state.form_date_confirmed
            )
            
            if save_button and st.session_state.form_date_confirmed:
                if not fund_code:
                    st.error("请输入基金代码")
                    return
                
                if purchase_amount <= 0:
                    st.error("购买金额必须大于0")
                    return
                
                if st.session_state.form_cost_per_unit <= 0:
                    st.error("持仓成本单价必须大于0")
                    return
                
                # 获取最新净值
                try:
                    with st.spinner("正在获取最新净值..."):
                        if 'temp_fund_info' in st.session_state:
                            fund_info = st.session_state.temp_fund_info
                        else:
                            fund_info = get_fund_info(fund_code)
                        
                        # 获取基金净值数据
                        df = get_fund_data(fund_code)
                        latest_data = df.iloc[-1] if not df.empty else None
                        
                        if latest_data is None:
                            st.error("无法获取基金最新净值数据，请稍后再试")
                            return
                        
                        # 计算持仓信息
                        # 确保DWJZ键存在，如果不存在尝试使用'nav'
                        net_value = 0
                        if latest_data is not None:
                            if 'DWJZ' in latest_data:
                                net_value = float(latest_data['DWJZ'])
                            elif 'nav' in latest_data:
                                net_value = float(latest_data['nav'])
                        
                        # 使用持仓成本单价计算份额
                        cost_per_unit = st.session_state.form_cost_per_unit
                        shares = purchase_amount / cost_per_unit if cost_per_unit > 0 else 0
                        current_value = shares * net_value
                        profit = current_value - purchase_amount
                        profit_percentage = (profit / purchase_amount * 100) if purchase_amount > 0 else 0
                        
                        # 创建或更新基金持仓数据
                        new_fund_data = {
                            'fund_code': fund_code,
                            'fund_name': fund_info.get('fund_name', '未知基金'),
                            'amount': purchase_amount,
                            'purchase_date': purchase_date.strftime('%Y-%m-%d'),
                            'cost_per_unit': cost_per_unit,  # 新增：持仓成本单价
                            'shares': shares,
                            'net_value': net_value,
                            'current_value': current_value,
                            'profit': profit,
                            'profit_percentage': profit_percentage,
                            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 保存数据
                        if is_edit and fund_index is not None:
                            st.session_state.portfolio[fund_index] = new_fund_data
                        else:
                            if 'portfolio' not in st.session_state:
                                st.session_state.portfolio = []
                            st.session_state.portfolio.append(new_fund_data)
                        
                        save_portfolio(st.session_state.portfolio)
                        
                        # 清理临时状态
                        st.session_state.show_edit_form = False
                        st.session_state.edit_fund_index = None
                        st.session_state.query_stage_completed = False
                        
                        # 清除表单状态
                        if 'temp_fund_info' in st.session_state:
                            del st.session_state.temp_fund_info
                        if 'form_fund_code' in st.session_state:
                            del st.session_state.form_fund_code
                        if 'form_purchase_amount' in st.session_state:
                            del st.session_state.form_purchase_amount
                        if 'form_purchase_date' in st.session_state:
                            del st.session_state.form_purchase_date
                        if 'form_cost_per_unit' in st.session_state:
                            del st.session_state.form_cost_per_unit
                        if 'form_date_confirmed' in st.session_state:
                            del st.session_state.form_date_confirmed
                        
                        st.success(f"{'更新' if is_edit else '添加'}基金持仓成功！")
                        st.rerun()
                except Exception as e:
                    st.error(f"保存基金持仓时出错: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

def refresh_portfolio_data():
    """刷新所有基金持仓的最新数据"""
    if 'portfolio' not in st.session_state or not st.session_state.portfolio:
        st.info("没有基金持仓数据可以刷新")
        return
    
    with st.spinner("正在刷新基金持仓数据..."):
        updated_portfolio = []
        total_funds = len(st.session_state.portfolio)
        progress_bar = st.progress(0)
        
        for i, fund_item in enumerate(st.session_state.portfolio):
            try:
                fund_code = fund_item.get('fund_code')
                st.write(f"正在更新 ({i+1}/{total_funds}): {fund_code}")
                
                # 获取最新的基金信息和净值数据
                fund_info = get_fund_info(fund_code)
                df = get_fund_data(fund_code)
                latest_data = df.iloc[-1] if not df.empty else None
                
                if latest_data is not None:
                    # 更新净值和盈亏信息
                    # 确保DWJZ键存在，如果不存在尝试使用'nav'
                    net_value = 0
                    if 'DWJZ' in latest_data:
                        net_value = float(latest_data['DWJZ'])
                    elif 'nav' in latest_data:
                        net_value = float(latest_data['nav'])
                    
                    purchase_amount = fund_item.get('amount', 0)
                    shares = fund_item.get('shares', 0)
                    cost_per_unit = fund_item.get('cost_per_unit', 0)
                    
                    # 如果有持仓成本单价，但没有份额数据，重新计算份额
                    if shares == 0 and cost_per_unit > 0:
                        shares = purchase_amount / cost_per_unit
                    # 如果没有持仓成本单价，但有份额数据，计算成本单价
                    elif shares > 0 and cost_per_unit == 0:
                        cost_per_unit = purchase_amount / shares
                    # 如果两者都没有，并且有净值数据，使用净值计算
                    elif shares == 0 and cost_per_unit == 0 and net_value > 0:
                        shares = purchase_amount / net_value
                        cost_per_unit = net_value
                    
                    current_value = shares * net_value
                    profit = current_value - purchase_amount
                    profit_percentage = (profit / purchase_amount * 100) if purchase_amount > 0 else 0
                    
                    # 更新基金数据
                    updated_fund = fund_item.copy()
                    updated_fund.update({
                        'fund_name': fund_info.get('fund_name', fund_item.get('fund_name', '未知基金')),
                        'net_value': net_value,
                        'shares': shares,
                        'cost_per_unit': cost_per_unit,  # 保留持仓成本单价
                        'current_value': current_value,
                        'profit': profit,
                        'profit_percentage': profit_percentage,
                        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    updated_portfolio.append(updated_fund)
                else:
                    # 如果获取不到最新数据，保留原数据
                    updated_portfolio.append(fund_item)
                
                # 更新进度
                progress_bar.progress((i + 1) / total_funds)
                
            except Exception as e:
                st.error(f"刷新基金 {fund_code} 时出错: {str(e)}")
                # 保留原有数据
                updated_portfolio.append(fund_item)
                # 更新进度
                progress_bar.progress((i + 1) / total_funds)
        
        # 完成进度条
        progress_bar.progress(1.0)
        
        # 更新session_state中的数据
        st.session_state.portfolio = updated_portfolio
        # 保存到文件
        save_portfolio(updated_portfolio)
        st.success("基金持仓数据更新完成！")
        st.rerun()