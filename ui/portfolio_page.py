import streamlit as st
import os
import json
from datetime import datetime

from ui.components import (
    load_portfolio, save_portfolio, 
    display_portfolio_summary, display_fund_card, 
    add_edit_fund_form, refresh_portfolio_data
)

def portfolio_page():
    """基金持仓管理页面"""
    st.session_state.current_view = "portfolio"
    st.markdown('<h1 class="main-header">基金持仓管理</h1>', unsafe_allow_html=True)
    
    # 初始化session_state
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = load_portfolio()
    
    if 'show_edit_form' not in st.session_state:
        st.session_state.show_edit_form = False
    
    if 'edit_fund_index' not in st.session_state:
        st.session_state.edit_fund_index = None
    
    if 'form_fund_code' not in st.session_state:
        st.session_state.form_fund_code = ""
    
    if 'query_stage_completed' not in st.session_state:
        st.session_state.query_stage_completed = False
    
    # 页面顶部操作按钮和刷新按钮在同一行
    col1, col2 = st.columns([6, 1])
    with col1:
        # 根据当前状态显示添加基金按钮
        if not st.session_state.show_edit_form:
            if st.button("+ 添加基金", use_container_width=True):
                st.session_state.show_edit_form = True
                st.session_state.edit_fund_index = None
                st.session_state.query_stage_completed = False
                st.rerun()
    with col2:
        if st.button("刷新数据", use_container_width=True):
            refresh_portfolio_data()
    
    # 添加一个容器用于存放表单，这样可以更好地控制布局
    form_container = st.container()
    
    # 显示添加/编辑表单
    if st.session_state.show_edit_form:
        is_edit = st.session_state.edit_fund_index is not None
        fund_index = st.session_state.edit_fund_index
        
        with form_container:
            # 表单标题
            st.markdown(f"## {'编辑' if is_edit else '添加'}基金持仓")
            
            # 只在未完成查询阶段时显示查询表单
            if not st.session_state.query_stage_completed:
                # 使用一个统一的表单布局，不分离输入框和查询按钮
                with st.form(key="fund_form"):
                    # 基金代码输入
                    fund_code = st.text_input(
                        "基金代码", 
                        value=st.session_state.form_fund_code,
                        placeholder="请输入6位基金代码",
                        key="portfolio_fund_code"
                    )
                    
                    # 提交按钮
                    query_submitted = st.form_submit_button("查询基金", use_container_width=True)
                
                # 处理表单提交
                if query_submitted and fund_code:
                    st.session_state.form_fund_code = fund_code
                    st.session_state.query_stage_completed = True
                    # 显示下一步
                    add_edit_fund_form(is_edit=is_edit, fund_index=fund_index, fund_code=fund_code, skip_input=True)
            else:
                # 查询阶段已完成，直接显示详细表单
                add_edit_fund_form(is_edit=is_edit, fund_index=fund_index, fund_code=st.session_state.form_fund_code, skip_input=True)
    
    # 显示投资组合总览
    st.markdown("---")
    st.markdown("## 投资组合总览")
    display_portfolio_summary(st.session_state.portfolio)
    
    # 显示基金列表
    st.markdown("---")
    st.markdown("## 基金持仓列表")
    
    if not st.session_state.portfolio:
        st.info("您还没有添加任何基金持仓，请点击\"添加基金\"按钮开始构建您的投资组合。")
    else:
        # 使用网格布局显示基金卡片
        cols_per_row = 3
        fund_items = st.session_state.portfolio
        
        for i in range(0, len(fund_items), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(fund_items):
                    with cols[j]:
                        display_fund_card(
                            fund_items[i + j], 
                            i + j, 
                            lambda: None  # 简单回调，实际刷新由各操作按钮触发
                        ) 