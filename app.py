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

# --- 1. 基础配置 (大数据质量监测系统 v5.3 - 全量数据版) ---
st.set_page_config(page_title="数据质量检测助手", layout="wide")
st.title("数据质量检测助手")
st.caption("方案：全量数据流注入 + 逻辑特征分析 + 结果实时流渲染 (v5.3)")

# 核心配置参数
API_URL = "https://85wdgqkcyx.coze.site/stream_run"
AUTH_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFkNDYwNWY5LWRjM2MtNGE0Ni04YmFhLWRiNTg3MGNmMTI4ZSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbIlZuQjBjWW1jY2ZnNXE2ZG9INVNMN1dsaXRHWU5IQ0lnIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzY2NTA4NTczLCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NTg2OTQ1ODIyNzAxMzg3ODEwIiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NTg3MDk2NTUyMDExNzI2ODU3In0.WkbXXuvL_sHN_5TbFw0Buf-if_LP3dOsFI4z2q4V-tUqhUDfVbn7cGMXnuUT2tn7EV9orUPemRqMnEjOh74dWgV79By298G6YvPaOh62nounpFA3s5aVBmVe9rq_1P4rjAig9yahbKAyf0M6RgOf8btoF1avxs3Ah6eCYlX-TLvS6zLe02PeFEavX_KsCDqW8PauIzPvhfqOM418heBJFj1C---Gk2zNE6q3poME9k-yikJq7jFhjfhyLbe1QYMqd-JcKcGg78xGF471OfwimBvNgAE1PIUN10-ssoEHPM5CbnS_VSXkivHlQ3KzA4ZXGenerH7ve-mY_29Q5tAlTA"
PROJECT_ID = 7586937259111350324 

# --- 2. 文件读取逻辑 ---
uploaded_file = st.file_uploader("📂 第一步：上传待审计的 Excel 或 CSV 文件", type=['csv', 'xlsx'])

if uploaded_file:
    try:
        # 使用 pandas 真正“读”出文件内容
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ 文件 '{uploaded_file.name}' 已加载。总计: {len(df)} 行, {len(df.columns)} 列。")
        st.write("数据内容预览：")
        st.dataframe(df.head(5))

        # --- 3. 按钮触发 AI 诊断 ---
        if st.button("🚀 第二步：开始全量 AI 数据审计"):
            st.divider()
            
            # 【重要更新】不再使用 .head(15)，而是将整个 DataFrame 转换为 CSV 字符串
            # 使用 CSV 格式是为了在传输时最节省 Token 空间
            with st.spinner("正在对全量数据进行特征编码..."):
                all_data_csv = df.to_csv(index=False)
            
            # 构造发送给 AI 的指令
            user_instruction = (
                f"你现在是一名资深大数据审计专家。我已经为你提供了文件的全量数据内容（CSV格式）如下：\n\n"
                f"### 全量数据内容：\n{all_data_csv}\n\n"
                f"### 诊断要求：\n"
                f"请直接根据上方提供的全量数据，深度分析其缺失值、数值异常逻辑、重复数据以及字段间的勾稽关系，并给出一份专业的审计报告。"
                f"注意：请不要调用任何外部文件读取工具，直接分析我发给你的这段文本。"
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

            st.write("🛰️ 正在上传全量数据流至远程节点 (此过程取决于文件大小，请稍候)...")
            
            try:
                # 增加超时时间到 300 秒，以应对超大数据量的处理
                response = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=300)
                
                if response.status_code != 200:
                    st.error(f"❌ 请求失败 (HTTP {response.status_code})")
                    st.code(response.text)
                else:
                    st.info("✅ 数据传输完成，AI 正在进行深度审计运算...")
                    
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
                                    
                                    # 针对 Vibe Agent 的多路径内容提取
                                    content_obj = chunk.get('content', {})
                                    text_piece = ""
                                    if isinstance(content_obj, dict):
                                        text_piece = content_obj.get('answer', '')
                                    
                                    if not text_piece:
                                        text_piece = chunk.get('content', '') if isinstance(chunk.get('content'), str) else ""
                                    
                                    if text_piece:
                                        full_report += text_piece
                                        report_area.markdown(f"### 📋 全量数据审计报告\n\n{full_report}")
                                except:
                                    continue
                    
                    if not full_report:
                        st.warning("⚠️ AI 响应结束但未提取到有效文本。请检查原始报文。")
                        with st.expander("查看最后接收到的报文"):
                            st.write(decoded_line if 'decoded_line' in locals() else "无数据")

            except requests.exceptions.Timeout:
                st.error("❌ 诊断超时：数据量过大，AI 处理时间超过了 5 分钟上限。")
            except Exception as e:
                st.error(f"⚠️ 网络通信中断: {e}")

    except Exception as e:
        st.error(f"❌ 读取本地文件失败: {e}")
else:
    st.info("💡 请上传文件，系统将为您执行全量数据特征注入。")