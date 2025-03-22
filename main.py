import streamlit as st
import sys
import os
import json
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="基金分析工具",
    page_icon="📊",
    layout="wide"
)

# 导入UI模块
from ui.components import load_css
from ui.pages import fund_query_page, favorite_funds_page, load_favorite_funds, show_fund_detail_popup
from ui.portfolio_page import portfolio_page
from ui.other_pages import fund_compare_page, fund_investment_plan_page, more_features_page

# 加载CSS样式
load_css()

# 初始化session state
if 'fund_code' not in st.session_state:
    st.session_state.fund_code = ''
if 'fund_data' not in st.session_state:
    st.session_state.fund_data = None
if 'start_date' not in st.session_state:
    st.session_state.start_date = None
if 'end_date' not in st.session_state:
    st.session_state.end_date = None
if 'favorite_funds' not in st.session_state:
    st.session_state.favorite_funds = {}
if 'current_view' not in st.session_state:
    st.session_state.current_view = None
if 'previous_fund_code' not in st.session_state:
    st.session_state.previous_fund_code = None
if 'show_toast' not in st.session_state:
    st.session_state.show_toast = None
if 'show_detail_popup' not in st.session_state:
    st.session_state.show_detail_popup = False
if 'detail_fund_code' not in st.session_state:
    st.session_state.detail_fund_code = None

# 加载自选基金数据
if len(st.session_state.favorite_funds) == 0:
    st.session_state.favorite_funds = load_favorite_funds()

# 侧边栏导航
st.sidebar.markdown("# 📊 基金分析工具")
st.sidebar.markdown("---")

# 导航选项
selected_nav = st.sidebar.radio(
    "功能导航",
    ["基金查询", "自选基金", "基金持仓", "基金比较", "基金投资计划", "待开发"]
)

# 处理导航逻辑
if selected_nav != "基金查询" and st.session_state.current_view == "fund_query_from_favorite":
    # 如果从自选基金跳转来的，且用户点击了其他导航，恢复之前的基金代码
    if st.session_state.previous_fund_code:
        st.session_state.fund_code = st.session_state.previous_fund_code
        st.session_state.previous_fund_code = None
    st.session_state.current_view = None

# 如果切换到基金查询功能，自动关闭自选基金卡片
if selected_nav == "基金查询":
    st.session_state.show_detail_popup = False
    st.session_state.detail_fund_code = None

nav_option = selected_nav

# 显示提示信息
if st.session_state.show_toast:
    st.toast(st.session_state.show_toast["message"], icon=st.session_state.show_toast["icon"])
    st.session_state.show_toast = None

# 检查是否需要显示基金详情弹窗
if st.session_state.show_detail_popup and st.session_state.detail_fund_code:
    # 创建详情容器
    detail_container = st.container()
    with detail_container:
        st.subheader("基金详情")
        # 获取基金数据
        try:
            from src.fund_data import get_fund_data, get_fund_info
            with st.spinner("正在获取基金数据..."):
                df = get_fund_data(st.session_state.detail_fund_code)
                fund_info = get_fund_info(st.session_state.detail_fund_code)
                
            if not df.empty:
                # 显示基金分析内容
                from ui.components import display_fund_analysis
                display_fund_analysis(df, fund_info)
            else:
                st.error("未能获取到基金数据，请检查基金代码是否正确。")
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            
        # 添加关闭按钮
        if st.button("关闭", key="close_detail_popup"):
            st.session_state.show_detail_popup = False
            st.session_state.detail_fund_code = None
            st.rerun()

# 主界面内容
if nav_option == "基金查询":
    fund_query_page()
elif nav_option == "自选基金":
    favorite_funds_page()
elif nav_option == "基金持仓":
    portfolio_page()
elif nav_option == "基金比较":
    fund_compare_page()
elif nav_option == "基金投资计划":
    fund_investment_plan_page()
else:  # 待开发
    more_features_page()