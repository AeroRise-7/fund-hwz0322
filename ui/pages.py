import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

from src.fund_data import get_fund_data, get_fund_info
from ui.components import display_fund_analysis

# 从本地文件加载自选基金数据
# 使用绝对路径确保文件保存在根目录下
FAVORITE_FUNDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "favorite_funds.json")

# 导入缓存目录常量
from src.fund_data import CACHE_DIR

def load_favorite_funds():
    """从本地文件加载自选基金数据"""
    if os.path.exists(FAVORITE_FUNDS_FILE):
        try:
            with open(FAVORITE_FUNDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_favorite_funds():
    """保存自选基金数据到本地文件"""
    with open(FAVORITE_FUNDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.favorite_funds, f, ensure_ascii=False)

def show_fund_detail_popup(fund_code):
    """显示基金详情弹窗"""
    st.session_state.show_detail_popup = True
    st.session_state.detail_fund_code = fund_code
    st.session_state.fund_data = None
    
    # 更新基金信息（无论是否为自选基金）
    try:
        # 获取最新的基金信息
        fund_info = get_fund_info(fund_code)
        last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 如果是自选基金，更新其信息
        if fund_code in st.session_state.favorite_funds:
            st.session_state.favorite_funds[fund_code]['fund_info'] = fund_info
            st.session_state.favorite_funds[fund_code]['last_update'] = last_update_time
            save_favorite_funds()
    except Exception as e:
        print(f"更新基金信息时发生错误: {str(e)}")
    
    st.rerun()

def fund_query_page():
    """基金查询页面"""
    st.session_state.current_view = "fund_query"
    st.markdown('<h1 class="main-header">基金分析报告</h1>', unsafe_allow_html=True)
    
    # 创建固定在顶部的容器
    with st.container():
        st.markdown('<div class="fixed-top">', unsafe_allow_html=True)
        
        # 如果是从自选基金跳转来的，添加返回按钮
        if st.session_state.current_view == "fund_query_from_favorite":
            if st.button("← 返回自选基金", use_container_width=True):
                st.session_state.fund_code = st.session_state.previous_fund_code
                st.session_state.previous_fund_code = None
                st.session_state.current_view = None
                st.session_state.nav_option = "自选基金"
                st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)
        
        # 输入基金代码
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            fund_code = st.text_input("👉 请输入基金代码", 
                                    value=st.session_state.fund_code,
                                    placeholder="例如: 017811",
                                    label_visibility="collapsed")
        with col2:
            analyze_button = st.button("开始分析", use_container_width=True)
        with col3:
            # 检查基金是否已在自选中
            is_favorite = fund_code in st.session_state.favorite_funds
            if is_favorite:
                if st.button("移出自选", use_container_width=True):
                    del st.session_state.favorite_funds[fund_code]
                    save_favorite_funds()
                    st.session_state.show_toast = {"message": "已从自选中移除！", "icon": "✅"}
                    st.rerun()
            else:
                if st.button("加入自选", use_container_width=True):
                    if fund_code and st.session_state.fund_data is not None:
                        # 重新获取最新的基金信息，确保包含所有新字段
                        try:
                            fund_info = get_fund_info(fund_code)
                            last_update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 保存到自选基金
                            st.session_state.favorite_funds[fund_code] = {
                                'fund_info': fund_info,
                                'last_update': last_update_time
                            }
                            save_favorite_funds()
                            st.session_state.show_toast = {"message": f"基金 {fund_code} 已添加到自选！", "icon": "✅"}
                            st.rerun()
                        except Exception as e:
                            st.error(f"添加自选基金时发生错误: {str(e)}")
                    elif fund_code:
                        st.warning('请先点击"开始分析"按钮获取基金数据')
                    else:
                        st.warning("请先输入基金代码")
        st.markdown('</div>', unsafe_allow_html=True)

    if analyze_button and fund_code:
        st.session_state.fund_code = fund_code
        st.session_state.fund_data = None
        st.session_state.start_date = None
        st.session_state.end_date = None
        st.rerun()
    
    if st.session_state.fund_code:
        try:
            # 获取基金数据（如果还没有获取）
            if st.session_state.fund_data is None:
                with st.spinner("正在获取基金数据..."):
                    df = get_fund_data(st.session_state.fund_code)
                    fund_info = get_fund_info(st.session_state.fund_code)
                    st.session_state.fund_data = {
                        'df': df,
                        'fund_info': fund_info
                    }
            else:
                df = st.session_state.fund_data['df']
                fund_info = st.session_state.fund_data['fund_info']
            
            if not df.empty:
                # 显示基金分析内容
                display_fund_analysis(df, fund_info)
            else:
                st.error("未能获取到基金数据，请检查基金代码是否正确。")
                
        except Exception as e:
            st.error(f"发生错误: {str(e)}")
    elif not st.session_state.fund_code:
        st.info("👆 请输入基金代码并点击'开始分析'按钮开始分析")

def refresh_favorite_funds():
    """刷新所有自选基金的数据"""
    if not st.session_state.favorite_funds:
        return
    
    with st.spinner("正在刷新自选基金数据..."):
        updated_funds = {}
        total_funds = len(st.session_state.favorite_funds)
        progress_bar = st.progress(0)
        
        for i, fund_code in enumerate(st.session_state.favorite_funds):
            try:
                st.write(f"正在更新 ({i+1}/{total_funds}): {fund_code}")
                
                # 获取最新的基金信息
                fund_info = get_fund_info(fund_code)
                
                # 获取最新的净值数据（依赖缓存智能更新机制）
                # 这会自动检查缓存并只获取新数据
                df = get_fund_data(fund_code)
                
                # 保存更新时间
                last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 更新基金信息
                updated_funds[fund_code] = {
                    'fund_info': fund_info,
                    'last_update': last_update
                }
                
                # 更新进度
                progress_bar.progress((i + 1) / total_funds)
                
            except Exception as e:
                st.error(f"刷新基金 {fund_code} 时出错: {str(e)}")
                # 保留原有数据
                updated_funds[fund_code] = st.session_state.favorite_funds[fund_code]
                # 更新进度
                progress_bar.progress((i + 1) / total_funds)
        
        # 完成进度条
        progress_bar.progress(1.0)
        
        # 更新session_state中的数据
        st.session_state.favorite_funds = updated_funds
        # 保存到文件
        save_favorite_funds()
        st.success("自选基金数据更新完成！")

def favorite_funds_page():
    """自选基金页面"""
    st.session_state.current_view = "favorite_funds"
    st.markdown('<h1 class="main-header">自选基金</h1>', unsafe_allow_html=True)
    
    # 添加刷新按钮
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("刷新数据", use_container_width=True):
            refresh_favorite_funds()
            st.rerun()
    
    if not st.session_state.favorite_funds:
        st.info("您还没有添加任何自选基金，请在基金查询页面添加。")
    else:
        # 显示自选基金列表
        with col1:
            st.markdown("### 我的自选基金")
        
        # 创建多列布局
        cols_per_row = 3
        funds = list(st.session_state.favorite_funds.items())
        
        for i in range(0, len(funds), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(funds):
                    fund_code, fund_data = funds[i + j]
                    with cols[j]:
                        with st.container():
                            # 处理基金名称，移除代码部分
                            fund_name = fund_data['fund_info']['fund_name']
                            if '(' in fund_name:
                                fund_name = fund_name.split('(')[0]
                            elif '（' in fund_name:
                                fund_name = fund_name.split('（')[0]
                            
                            # 获取基金相关信息
                            fund_manager = fund_data['fund_info'].get('fund_manager', '未知')
                            fund_type = fund_data['fund_info'].get('fund_type', '未知')
                            
                            # 修改申购状态显示逻辑
                            is_buy_status = fund_data['fund_info'].get('is_buy')
                            if is_buy_status is True:
                                is_buy = "可申购"
                            elif is_buy_status is False:
                                is_buy = "暂停申购"
                            else:
                                is_buy = "未知"
                            
                            st.markdown(f"""
                            <div class="fund-card">
                                <h4 title="{fund_name}">{fund_name}</h4>
                                <div class="info-row">
                                    <span>代码：{fund_code}</span>
                                    <span>{fund_type}</span>
                                </div>
                                <div class="info-row">
                                    <span>基金经理：{fund_manager}</span>
                                    <span>{is_buy}</span>
                                </div>
                                <p class="update-time">更新时间：{fund_data['last_update']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("查看详情", key=f"view_{fund_code}"):
                                    # 打开详情弹窗
                                    show_fund_detail_popup(fund_code)
                            with col2:
                                if st.button("移出自选", key=f"remove_{fund_code}"):
                                    del st.session_state.favorite_funds[fund_code]
                                    save_favorite_funds()
                                    st.rerun()