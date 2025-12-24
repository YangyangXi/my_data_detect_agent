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

# --- 1. 基础配置 (v6.2 交互增强版) ---
st.set_page_config(page_title="数据质量监测助手", layout="wide")
st.title("🛡️ 数据质量监测助手")
st.caption("开发者：xiyy | 方案：BYOK (Bring Your Own Key) 共享模式")

# 你的 Agent 逻辑地址（公开的，但需要 Token 激活）
API_URL = "https://85wdgqkcyx.coze.site/stream_run"
PROJECT_ID = 7586937259111350324 

# --- 2. 侧边栏：引导访问者获取资源 ---
with st.sidebar:
    st.header("🔑 访问授权")
    
    # 获取用户输入的 Token
    user_pat = st.text_input(
        "请输入您的扣子 PAT 令牌", 
        type="password", 
        placeholder="pat_xxxxxxxxxxxx"
    )
    
    if user_pat:
        AUTH_TOKEN = user_pat
        st.success("✅ 令牌已就绪，将使用您的资源点进行运算。")
    else:
        AUTH_TOKEN = None
        st.error("⚠️ 需要 Token 才能运行分析。")
        
    st.divider()
    
    # 给访问者的保姆级教程
    with st.expander("❓ 如何获取我的令牌（Token）？"):
        st.write("""
        1. 登录 [Coze.cn](https://www.coze.cn)
        2. 点击左下角头像 -> **个人设置**
        3. 进入 **API 访问令牌** 选项卡
        4. 点击 **添加新令牌**
        5. 复制生成的令牌并粘贴到左侧输入框
        """)
        st.info("提示：新账号通常有免费资源点，足够完成多次数据质量检测。")

# --- 3. 核心功能逻辑 ---
uploaded_file = st.file_uploader("📂 第一步：上传待检测数据", type=['csv', 'xlsx'])

if uploaded_file and AUTH_TOKEN:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"成功读取：{uploaded_file.name}")
        st.dataframe(df.head(5))

        if st.button("🚀 第二步：启动全量 AI 诊断"):
            st.divider()
            
            with st.spinner("正在将全量数据特征注入 AI 决策中心..."):
                all_data_csv = df.to_csv(index=False)
            
            headers = {
                "Authorization": f"Bearer {AUTH_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "content": {
                    "query": {
                        "prompt": [{
                            "type": "text", 
                            "content": { "text": f"请针对以下全量数据进行审计分析：\n\n{all_data_csv}" }
                        }]
                    }
                },
                "type": "query",
                "project_id": PROJECT_ID
            }

            try:
                # 设定较长的超时时间，应对大数据量
                response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=300)
                
                if response.status_code == 500:
                    st.error("❌ 您输入的 Token 所属账号资源点已耗尽。")
                elif response.status_code == 401:
                    st.error("❌ Token 错误或已失效。")
                elif response.status_code != 200:
                    st.error(f"❌ 服务器异常 (HTTP {response.status_code})")
                else:
                    st.info("🛰️ 诊断中，结果将实时呈现...")
                    report_area = st.empty()
                    full_report = ""
                    
                    for line in response.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith('data:'):
                                try:
                                    chunk = json.loads(decoded[5:].strip())
                                    if chunk == "[DONE]": continue
                                    
                                    # 兼容性解析
                                    content = chunk.get('content', '')
                                    if isinstance(content, dict):
                                        content = content.get('answer', '')
                                    
                                    if content:
                                        full_report += content
                                        report_area.markdown(f"### 📋 数据质量报告\n\n{full_report}")
                                except:
                                    continue
            except Exception as e:
                st.error(f"网络连接异常: {e}")

    except Exception as e:
        st.error(f"读取文件失败: {e}")
elif uploaded_file and not AUTH_TOKEN:
    st.warning("👈 请先在左侧输入您的个人 PAT 令牌，否则无法支付运算成本。")
