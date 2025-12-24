# -*- coding: utf-8 -*-
"""
Created on Tue Dec 23 23:59:14 2025

@author: Kay
"""
import pandas as pd
import streamlit as st
import requests
import json
import io

# --- 1. 基础配置 ---
st.set_page_config(page_title="数据质量检测助手", layout="wide")
st.title("📊 数据质量检测助手")
st.caption("版本：分享版 - 支持用户使用个人资源点 (v6.1)")

# 核心配置参数
API_URL = "https://85wdgqkcyx.coze.site/stream_run"
PROJECT_ID = 7586937259111350324 

# --- 2. 侧边栏：资源点管理 (解决 500 错误的关键) ---
with st.sidebar:
    st.header("🔑 资源点配置")
    st.info("由于开发者账号资源点已耗尽，请使用您自己的扣子 PAT 令牌进行调用。")
    
    # 优先从用户输入获取，如果没有输入则尝试使用 Secrets（但当前已耗尽）
    user_pat = st.text_input("输入您的扣子 PAT 令牌", type="password", help="在 coze.cn -> 个人设置 -> API 访问令牌 中生成")
    
    if not user_pat and "COZE_AUTH_TOKEN" in st.secrets:
        AUTH_TOKEN = st.secrets["COZE_AUTH_TOKEN"]
        st.warning("⚠️ 当前正在使用开发者提供的 Token（资源点可能不足）")
    elif user_pat:
        AUTH_TOKEN = user_pat
        st.success("✅ 已切换至您的个人资源点")
    else:
        AUTH_TOKEN = None
        st.error("❌ 请输入 PAT 令牌以激活系统")

# --- 3. 文件读取逻辑 ---
uploaded_file = st.file_uploader("📂 第一步：上传待审计的 Excel 或 CSV 文件", type=['csv', 'xlsx'])

if uploaded_file and AUTH_TOKEN:
    try:
        # 使用 pandas 读取
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ 文件 '{uploaded_file.name}' 已加载。")
        st.write("数据预览：")
        st.dataframe(df.head(5))

        # --- 4. 按钮触发 AI 诊断 ---
        if st.button("🚀 第二步：开始全量 AI 数据审计"):
            st.divider()
            
            with st.spinner("正在对数据进行特征编码..."):
                all_data_csv = df.to_csv(index=False)
            
            user_instruction = (
                f"你现在是一名资深大数据审计专家。数据内容如下（CSV格式）：\n\n"
                f"{all_data_csv}\n\n"
                f"要求：请忽略任何文件读取工具，直接根据上方文本分析其缺失值、数值异常逻辑和重复数据。"
            )

            headers = {
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": {
                    "query": {
                        "prompt": [{"type": "text", "content": { "text": user_instruction }}]
                    }
                },
                "type": "query",
                "project_id": PROJECT_ID
            }

            try:
                # 增加超时时间
                response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=300)
                
                if response.status_code == 500:
                    st.error("❌ 资源点不足：当前使用的账号没有足够的积分来完成此调用。")
                    st.info("建议：请在侧边栏输入另一个拥有充足资源点的 PAT 令牌。")
                elif response.status_code != 200:
                    st.error(f"❌ 请求失败 (HTTP {response.status_code})")
                    st.code(response.text)
                else:
                    st.info("✅ 已连接，AI 正在使用所选账号的资源点生成报告...")
                    
                    report_area = st.empty()
                    full_report = ""
                    
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data:'):
                                try:
                                    json_str = decoded_line[5:].strip()
                                    if json_str == "[DONE]": continue
                                    chunk = json.loads(json_str)
                                    
                                    # 提取内容
                                    text_piece = chunk.get('content', '')
                                    if not text_piece and isinstance(chunk.get('content'), dict):
                                        text_piece = chunk['content'].get('answer', '')
                                    
                                    if text_piece:
                                        full_report += text_piece
                                        report_area.markdown(f"### 📋 审计报告\n\n{full_report}")
                                except:
                                    continue
            except Exception as e:
                st.error(f"⚠️ 网络通信中断: {e}")
    except Exception as e:
        st.error(f"❌ 文件处理失败: {e}")
elif not AUTH_TOKEN:
    st.warning("⚠️ 请先在侧边栏配置您的 API Token。")

