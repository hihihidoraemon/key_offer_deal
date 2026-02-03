#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
import base64
from io import BytesIO

# ==================== Streamlit页面配置（必须放在最前面） ====================
st.set_page_config(
    page_title="Offer数据分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 样式配置 ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 模板下载功能 ====================
def create_template_data():
    """创建Excel模板数据"""
    # 主数据表模板
    main_data = pd.DataFrame({})
    # 黑名单表模板
    blacklist_data = pd.DataFrame({
        'Advertiser': ['','','','','','[110008]Shareit','[110037]Shareit_xdj','[110040]Ricefruit','[110047]Jolibox_Appnext_Online_New','[110049]AutumnAds','[110028]mobpower','[110016]Imxbidding','[110045]dolphine','[110045]dolphine','[110045]dolphine','[110021]flymobi','[110021]flymobi','[110021]flymobi','[110022]imxbidding_xdj','[110022]imxbidding_xdj','[110059]Flowbox','[110054]acshare'],
        'Affiliate': ['[135]bidderdesk_xdj_1','[144]bidderdesk_xdj_2','[113]ioger','[108]Baidu (Hong Kong) Limited','[128]shareit','','','','','','','','[134]ioger_xdj','[136]Bytemobi_xdj','[142]magicbeans_xdj','[134]ioger_xdj','[142]magicbeans_xdj','[136]Bytemobi_xdj','[114]imxbidding','[157]imxbidding_xdj','[111]flowbox_xdj','[155]acshare_xdj']
    })
    
    return main_data, blacklist_data

def get_template_download_link():
    """生成Excel模板下载链接"""
    # 创建模板数据
    main_data, blacklist_data = create_template_data()
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        main_data.to_excel(writer, sheet_name='1-all data', index=False)
        blacklist_data.to_excel(writer, sheet_name='blacklist', index=False)
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    
    # 生成下载链接
    filename = "offer_analysis_template.xlsx"
    href = f'''
    <div class="template-download">
        <p>下载包含标准格式的Excel模板文件，包含数据表和黑名单表</p>
        <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" 
           download="{filename}" class="download-btn">
           🎯 下载Excel模板
        </a>
    </div>
    '''
    return href

def get_template_instructions():
    """返回模板使用说明"""
    return """
    ### 📋 Excel模板使用说明

    #### 模板结构：
    - **1-all data**工作表：主数据表，包含过去30天所有Offer数据
    - **blacklist**工作表：黑名单配置表，这个表不用修改

    #### 数据表字段说明（1-all data）：
    | 字段名 | 类型 | 说明 | 示例 |
    |--------|------|------|------|
    | Time | 日期 | 数据日期 | 2024-01-25 |
    | Offer ID | 数字 | Offer唯一标识 | 92054 |
    | Advertiser | 文本 | 广告主名称 | [110001]APPNEXT |
    | Affiliate | 文本 | 渠道名称 | [101]Melodong |
    | App ID | 文本 | 应用标识 | com.example.app1 |
    | GEO | 文本 | 地区代码 | US |
    | Total Clicks | 数字 | 总点击量 | 1000 |
    | Total Conversions | 数字 | 总转化量 | 50 |
    | Total Revenue | 数字 | 总收入（美元） | 500.50 |
    | Total Profit | 数字 | 总利润（美元） | 250.25 |
    | Total Caps | 数字 | 总预算上限 | 1000 |
    | Status | 文本 | 状态（ACTIVE/PAUSE） | ACTIVE |

    #### 黑名单表字段说明（blacklist）：
    | 字段名 | 类型 | 说明 | 示例 |
    |--------|------|------|------|
    | Advertiser | 文本 | 广告主黑名单（留空表示匹配所有） | [110008]Shareit |
    | Affiliate | 文本 | 渠道黑名单（留空表示匹配所有） | [113]ioger |

    #### 使用规则：
    - 如果Advertiser为空：匹配所有该Affiliate的记录
    - 如果Affiliate为空：匹配所有该Advertiser的记录
    - 如果两者都不为空：必须同时匹配Advertiser和Affiliate
    """
#上下游基础信息
ADVERTISER_TYPE_MAP = {
    '[110001]APPNEXT': 'xdj流量/inapp流量',
    '[110006]APPNEXT-ONLINE': 'xdj流量/inapp流量',
    '[110035]Jolibox_Appnext_Online': 'xdj流量/inapp流量',
    '[110047]Jolibox_Appnext_Online_New': 'xdj流量/inapp流量',
    '[110021]flymobi': 'xdj流量',
    '[110045]dolphine': 'xdj流量',
    '[110029]mobpower_xdj': 'xdj流量',
    '[110028]mobpower': 'xdj流量/inapp流量',
    '[110048]alto': 'xdj流量',
    '[110022]imxbidding_xdj': 'xdj流量',
    '[110016]Imxbidding': 'xdj流量/inapp流量',
    '[110031]mobvista': 'xdj流量',
    '[110010]Leapmob': 'xdj流量',
    '[110036]Viking': 'xdj流量',
    '[110020]cchange': 'xdj流量',
    '[110023]bidmatrix': 'xdj流量',
    '[110012]Smartconnect': 'xdj流量/inapp流量',
    '[110050]Joymobi_new': 'xdj流量/inapp流量',
    '[110039]Seanear': 'xdj流量',
    '[110025]melodong': 'xdj流量',
    '[110008]Shareit': 'xdj流量',
    '[110037]Shareit_xdj': 'xdj流量',
    '[110019]Bytemobi': 'xdj流量/inapp流量',   
    '[110017]Gridads': 'xdj流量',    
    '[110034]Joymobi': 'xdj流量',
    '[110051]Elementallink': 'xdj流量',
    '[110040]Ricefruit': 'xdj流量',
    '[110049]AutumnAds': 'xdj流量',
    '[110011]Versemedia': 'xdj流量',
    '[110054]acshare': 'xdj流量',
    '[110059]Flowbox': 'xdj流量'
}

AFFILIATE_TYPE_MAP = {
    '[101]Melodong': 'inapp流量',
    '[106]wldon': 'inapp流量',
    '[131]wldon_new': 'inapp流量',
    '[124]wldon_xdj': 'xdj流量',
    '[115]synjoy': 'inapp流量',
    '[158]synjoy_xdj': 'xdj流量',
    '[104]versemedia': 'inapp流量',
    '[122]melodong_xdj': 'xdj流量',
    '[111]flowbox_xdj': 'xdj流量',
    '[114]imxbidding': 'inapp流量',
    '[157]imxbidding_xdj': 'xdj流量',
    '[117]ioger_own': 'inapp流量',
    '[139]Versemedia_xdj': 'xdj流量',
    '[143]Alto_xdj': 'xdj流量',
    '[137]Seanear_xdj': 'xdj流量',
    '[107]zhizhen': 'inapp流量',
    '[120]magicbeans': 'inapp流量',
    '[142]magicbeans_xdj': 'xdj流量',
    '[113]ioger': 'inapp流量',
    '[123]bytemobi': 'inapp流量',
    '[134]ioger_xdj': 'xdj流量',
    '[126]seanear': 'inapp流量',
    '[141]Joymobi_xdj': 'xdj流量',
    '[136]Bytemobi_xdj': 'xdj流量',    
    '[132]Viking_xdj': 'xdj流量',
    '[155]acshare_xdj':'xdj流量',
    '[144]bidderdesk_xdj_2':'xdj流量',
    '[135]bidderdesk_xdj_1':'xdj流量'
    
}

#黑名单机制
BLACKLIST_CONFIG = {
    'advertiser_blacklist': ['[110008]Shareit','[110037]Shareit_xdj','[110040]Ricefruit','[110047]Jolibox_Appnext_Online_New','[110049]AutumnAds','[110028]mobpower','[110016]Imxbidding'],
    'affiliate_blacklist': ['[108]Baidu (Hong Kong) Limited', '[128]shareit','[113]ioger','[144]bidderdesk_xdj_2'
    '[135]bidderdesk_xdj_1']}



# 阈值配置
OFFER_DIFF_THRESHOLD = 10    
AFFILIATE_DIFF_THRESHOLD = 5 
RULE4_REVENUE_DIFF_ABS = 5    # 差值绝对值≤5
RULE4_REVENUE_DIFF_UP = 5     # 流水增长≥5
RULE5_REVENUE_DIFF_THRESHOLD = -5  
TARGET_OFFER_ID = 92054       # 仅调试该Offer


# 全局变量，用于存储从Excel读取的黑名单配置
BLACKLIST_RECORDS = []

def load_blacklist_from_excel(blacklist_df):
    """从Excel黑名单表加载黑名单配置"""
    try:
        if 'Advertiser' not in blacklist_df.columns or 'Affiliate' not in blacklist_df.columns:
            st.error("❌ 黑名单表格必须包含'Advertiser'和'Affiliate'两列")
            return []
        
        blacklist_records = []
        for _, row in blacklist_df.iterrows():
            advertiser = str(row['Advertiser']).strip() if pd.notna(row['Advertiser']) else ''
            affiliate = str(row['Affiliate']).strip() if pd.notna(row['Affiliate']) else ''
            if advertiser or affiliate:
                blacklist_records.append({
                    'advertiser': advertiser,
                    'affiliate': affiliate
                })
        
        return blacklist_records
    except Exception as e:
        st.warning(f"⚠️ 处理黑名单数据失败: {str(e)}")
        return []

def is_in_blacklist(advertiser, affiliate):
    """检查广告主和Affiliate组合是否在黑名单中"""
    if not BLACKLIST_RECORDS:
        return False
    
    advertiser_clean = str(advertiser).strip() if pd.notna(advertiser) else ''
    affiliate_clean = str(affiliate).strip() if pd.notna(affiliate) else ''
    
    for record in BLACKLIST_RECORDS:
        advertiser_match = (not record['advertiser'] or record['advertiser'] == advertiser_clean)
        affiliate_match = (not record['affiliate'] or record['affiliate'] == affiliate_clean)
        
        if advertiser_match and affiliate_match:
            return True
    
    return False



def parse_affiliate_rate_text(text):
    affiliate_list = []
    if pd.isna(text) or text == '':
        return affiliate_list
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if '流水' in line:
            affiliate_part = line.split('流水')[0].strip()
            if affiliate_part:
                affiliate_list.append(affiliate_part)
    return affiliate_list


def get_affiliate_type(affiliate_name):
    if pd.isna(affiliate_name):
        return ""
    clean_aff = affiliate_name.strip().lower().replace(' ', '')
    for aff_key, aff_type in AFFILIATE_TYPE_MAP.items():
        clean_key = aff_key.strip().lower().replace(' ', '')
        if clean_key in clean_aff or clean_aff in clean_key:
            return aff_type
    return ""

def get_affiliate_revenue_diff(qualified_df, offer_id, affiliate, latest_date, second_latest_date):
    offer_data = qualified_df[qualified_df['Offer ID'] == offer_id].copy()
    if len(offer_data) == 0:
        if offer_id == TARGET_OFFER_ID:
            print(f"  ❌ Offer {offer_id} 无数据")
        return np.nan
    
    def clean_aff_name(name):
        if pd.isna(name):
            return ""
        return name.strip().lower()
    target_aff_clean = clean_aff_name(affiliate)
    offer_data['Affiliate_clean'] = offer_data['Affiliate'].apply(clean_aff_name)
    aff_data = offer_data[offer_data['Affiliate_clean'] == target_aff_clean].copy()
    
    if len(aff_data) == 0:
        if offer_id == TARGET_OFFER_ID:
            print(f"  ❌ Offer {offer_id} 未匹配到Affiliate [{affiliate}]（清洗后：{target_aff_clean}）")
        return np.nan
    
    if offer_id == TARGET_OFFER_ID:
        print(f"  ✅ Offer {offer_id} 匹配到Affiliate [{affiliate}] 共 {len(aff_data)} 行数据")
    
    aff_data['date'] = aff_data['Time'].dt.date
    latest_rev = aff_data[aff_data['date'] == latest_date]['Total Revenue'].sum() if len(aff_data) > 0 else 0
    second_rev = aff_data[aff_data['date'] == second_latest_date]['Total Revenue'].sum() if len(aff_data) > 0 else 0
    
    if offer_id == TARGET_OFFER_ID:
        print(f"  📊 Offer {offer_id} | Affiliate {affiliate} 收入明细：")
        print(f"     - 最新日期 [{latest_date}] 收入：{latest_rev:.2f} 美金")
        print(f"     - 次新日期 [{second_latest_date}] 收入：{second_rev:.2f} 美金")
        print(f"     - 差值（最新-次新）：{latest_rev - second_rev:.2f} 美金")
    
    return latest_rev - second_rev

# ==================== 新增：收入排序计算逻辑 ====================
def calculate_revenue_ranking(qualified_df):
    """
    计算收入排序：
    - 如果是本月1号，计算所有日期的Total Revenue
    - 否则，只计算本月所有日期的Total Revenue
    - 按Advertiser维度汇总并降序排序
    """
    # 确保Time列是datetime类型
    qualified_df = qualified_df.copy()
    qualified_df['Time'] = pd.to_datetime(qualified_df['Time'], errors='coerce')
    
    # 获取数据中的最大日期（判断是否为当月1号的基准）
    max_date = qualified_df['Time'].max()
    is_first_day = (max_date.day == 1)
    
    # 筛选时间范围
    if is_first_day:
        # 本月1号：计算所有日期数据
        filtered_df = qualified_df
    else:
        # 非本月1号：只计算本月数据
        filtered_df = qualified_df[
            (qualified_df['Time'].dt.year == max_date.year) & 
            (qualified_df['Time'].dt.month == max_date.month)
        ]
    
    #计算每个(Time, Offer ID, Advertiser)的总收入
    time_offer_advertiser_revenue = filtered_df.groupby(['Offer ID', 'Advertiser'])['Total Revenue'].sum().reset_index()
    time_offer_advertiser_revenue.rename(columns={'Total Revenue': 'Time_Offer_Advertiser_Revenue'}, inplace=True)

    time_offer_advertiser_revenue = time_offer_advertiser_revenue.sort_values(
    by=['Advertiser', 'Time_Offer_Advertiser_Revenue'],  # 优先按广告主排序，同广告主内按收入排序
    ascending=[True, False],  # Advertiser升序（字母/数字顺序），Revenue降序
    ignore_index=True)
    
    time_offer_advertiser_revenue['Advertiser_Rank'] = time_offer_advertiser_revenue.groupby('Advertiser')['Time_Offer_Advertiser_Revenue'].rank(
    method='min', ascending=False).astype(int)

   
    
    return time_offer_advertiser_revenue

# ==================== 核心处理函数（适配Streamlit） ====================
def process_offer_data_web(uploaded_file, progress_bar=None, status_text=None):
    """
    网页版处理函数，基于原脚本逻辑
    """
    global BLACKLIST_RECORDS
    # 更新进度
    if progress_bar and status_text:
        progress_bar.progress(10)
        status_text.text("📁 正在读取Excel文件...")
    
    try:
        # 读取上传的文件
        excel_file = pd.ExcelFile(uploaded_file)
        df = pd.read_excel(uploaded_file, sheet_name='1-all data')
        blacklist_df = pd.read_excel(uploaded_file, sheet_name='blacklist')
        BLACKLIST_RECORDS = load_blacklist_from_excel(blacklist_df)

        print(BLACKLIST_RECORDS)
   
        
        # 数据预处理
        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.dropna(subset=['Time'])
        df['Offer ID'] = pd.to_numeric(df['Offer ID'], errors='coerce')
        df['Total Caps'] = pd.to_numeric(df['Total Caps'], errors='coerce')
        
        # 提取最新两天日期
        all_dates = sorted(df['Time'].dt.date.unique())
        print(f"数据包含的唯一日期列表：{all_dates}")
        print(f"数据时间范围：{all_dates[0]} 至 {all_dates[-1]}")
        
        if len(all_dates) >= 2:
            latest_date = all_dates[-1]          
            second_latest_date = all_dates[-2]   
            print(f"提取到最新两天日期：{second_latest_date}（次新）、{latest_date}（最新）")
        else:
            latest_date = all_dates[0]
            second_latest_date = all_dates[0]
            print(f"⚠️ 数据仅包含1个日期：{latest_date}，次新日期默认同最新日期")
        
        latest_date_str = latest_date.strftime("%Y/%m/%d")
        second_latest_date_str = second_latest_date.strftime("%Y/%m/%d")
        output_file = f"processed_offer_{latest_date.strftime('%Y%m%d')}.xlsx"
            
    except Exception as e:
        print(f"读取数据失败：{str(e)}")
        return None

    # 2. 筛选符合条件的Offer ID
    print("\n=== 2. 筛选符合条件的Offer ID ===")
    daily_offer_revenue = df.groupby(['Time', 'Offer ID'])['Total Revenue'].sum().reset_index()
    daily_offer_revenue.columns = ['Time', 'Offer ID', 'Daily_Revenue']
    qualified_offer_ids = daily_offer_revenue[daily_offer_revenue['Daily_Revenue'] >= 10]['Offer ID'].unique()
    qualified_df = df[df['Offer ID'].isin(qualified_offer_ids)].copy()
    print(f"符合条件的Offer ID数量：{len(qualified_offer_ids)}")

    # 3. 计算Offer核心汇总指标
    print("\n=== 3. 计算Offer汇总指标 ===")
    offer_summary = qualified_df.groupby('Offer ID').agg({
        'Total Clicks': 'sum',
        'Total Conversions': 'sum', 
        'Total Revenue': 'sum',
        'Total Profit': lambda x: x.sum() if 'Total Profit' in df.columns else 0,
        'Advertiser': 'first',
        'App ID': lambda x: x.iloc[0] if 'App ID' in df.columns else '',
        'GEO': lambda x: x.iloc[0] if 'GEO' in df.columns else '',
        'Total Caps': 'first',
        'Status': 'first'
    }).reset_index()

    offer_summary.columns = [
        'Offer ID', 'total_clicks', 'total_conversions', 
        'total_revenue', 'total_profit', 'Advertiser', 
        'App ID', 'GEO', 'Total caps', 'Status'
    ]

    # 4. 按Affiliate计算收入占比
    print("\n=== 4. 计算Affiliate收入占比 ===")
    affiliate_revenue = qualified_df.groupby(['Offer ID', 'Affiliate'])['Total Revenue'].sum().reset_index()
    affiliate_revenue.columns = ['Offer ID', 'Affiliate', 'affilate_revenue']
    
    affiliate_revenue = affiliate_revenue.merge(
        offer_summary[['Offer ID', 'total_revenue']], 
        on='Offer ID', 
        how='left'
    )

    affiliate_revenue['affilate_revenue_rate'] = np.where(
        affiliate_revenue['affilate_revenue'] > 0,
        (affiliate_revenue['affilate_revenue'] / affiliate_revenue['total_revenue']).round(4),
        0
    )

    affiliate_revenue['affilate_revenue_rate_str'] = affiliate_revenue['affilate_revenue_rate'].apply(
        lambda x: f"{x:.2%}" if x > 0 else "0.00%"
    )

    affiliate_revenue['affilate_revenue_text'] = (
        affiliate_revenue['Affiliate'] + "流水占比：" + 
        affiliate_revenue['affilate_revenue'].round(2).astype(str) + "美金" + 
        affiliate_revenue['affilate_revenue_rate_str']
    )

    affiliate_summary = affiliate_revenue.sort_values(
        by=['Offer ID', 'affilate_revenue_rate'], 
        ascending=[True, False]
    ).groupby('Offer ID')['affilate_revenue_text'].agg(
        lambda x: '\n'.join(x)
    ).reset_index()
    affiliate_summary.columns = ['Offer ID', 'affilate_revenue_rate_all']

    # 5. 计算最新两天分别的数据
    print("\n=== 5. 计算最新两天数据 ===")
    latest_mask = qualified_df['Time'].dt.date == latest_date
    latest_date_data = qualified_df[latest_mask].copy()
    latest_summary = latest_date_data.groupby('Offer ID').agg({
        'Total Clicks': 'sum',
        'Total Conversions': 'sum',
        'Total Revenue': 'sum',
        'Total Profit': lambda x: x.sum() if 'Total Profit' in df.columns else 0
    }).reset_index()
    
    latest_fields = [
        f'{latest_date_str}_total_clicks', 
        f'{latest_date_str}_total_conversions', 
        f'{latest_date_str}_total_revenue', 
        f'{latest_date_str}_total_profit'
    ]
    latest_summary.columns = ['Offer ID'] + latest_fields
    
    second_mask = qualified_df['Time'].dt.date == second_latest_date
    second_latest_date_data = qualified_df[second_mask].copy()
    second_summary = second_latest_date_data.groupby('Offer ID').agg({
        'Total Clicks': 'sum',
        'Total Conversions': 'sum',
        'Total Revenue': 'sum',
        'Total Profit': lambda x: x.sum() if 'Total Profit' in df.columns else 0
    }).reset_index()
    
    second_fields = [
        f'{second_latest_date_str}_total_clicks', 
        f'{second_latest_date_str}_total_conversions', 
        f'{second_latest_date_str}_total_revenue', 
        f'{second_latest_date_str}_total_profit'
    ]
    second_summary.columns = ['Offer ID'] + second_fields

    # 6. 最新一天Affiliate分析
    print("\n=== 6. 最新一天Affiliate分析 ===")
    latest_affiliate_summary = pd.DataFrame({'Offer ID': offer_summary['Offer ID'], 'latest_affilate_revenue_rate_all': ''})
    latest_day_df = qualified_df[qualified_df['Time'].dt.date == latest_date].copy()
    
    if len(latest_day_df) > 0:
        latest_affiliate_revenue = latest_day_df.groupby(['Offer ID', 'Affiliate'])['Total Revenue'].sum().reset_index()
        latest_affiliate_revenue.columns = ['Offer ID', 'Affiliate', 'latest_affilate_revenue']
        
        latest_offer_total = latest_day_df.groupby('Offer ID')['Total Revenue'].sum().reset_index()
        latest_offer_total.columns = ['Offer ID', 'latest_total_revenue']
        
        latest_affiliate_revenue = latest_affiliate_revenue.merge(latest_offer_total, on='Offer ID', how='left')
        latest_affiliate_revenue['latest_affilate_revenue_rate'] = np.where(
            (latest_affiliate_revenue['latest_affilate_revenue'] > 0) & 
            (latest_affiliate_revenue['latest_total_revenue'] > 0),
            (latest_affiliate_revenue['latest_affilate_revenue'] / latest_affiliate_revenue['latest_total_revenue']).round(4),
            0
        )

        latest_affiliate_revenue['latest_affilate_revenue_rate_str'] = latest_affiliate_revenue['latest_affilate_revenue_rate'].apply(
            lambda x: f"{x:.2%}" if x > 0 else "0.00%"
        )

        latest_affiliate_revenue['latest_affiliate_text'] = (
            latest_affiliate_revenue['Affiliate'] + "流水占比：" + 
            latest_affiliate_revenue['latest_affilate_revenue'].round(2).astype(str) + "美金" + 
            latest_affiliate_revenue['latest_affilate_revenue_rate_str']
        )

        latest_affiliate_summary = latest_affiliate_revenue.sort_values(
            by=['Offer ID', 'latest_affilate_revenue_rate'], 
            ascending=[True, False]
        ).groupby('Offer ID')['latest_affiliate_text'].agg(lambda x: '\n'.join(x)).reset_index()
        latest_affiliate_summary.columns = ['Offer ID', 'latest_affilate_revenue_rate_all']

        # ==================== 新增：计算每个Affiliate波动的原因 ====================
        # 1. 计算Affiliate两天的流水/点击/转化数据
        # 最新日期Affiliate数据（点击+转化+流水）
        latest_aff_full = latest_day_df.groupby(['Offer ID', 'Affiliate']).agg({
            'Total Clicks': 'sum',
            'Total Conversions': 'sum',
            'Total Revenue': 'sum'
        }).reset_index()
        latest_aff_full.columns = ['Offer ID', 'Affiliate', 'clicks_latest', 'conversions_latest', 'revenue_latest']
        
        # 次新日期Affiliate数据
        second_aff_full = second_latest_date_data.groupby(['Offer ID', 'Affiliate']).agg({
            'Total Clicks': 'sum',
            'Total Conversions': 'sum',
            'Total Revenue': 'sum'
        }).reset_index()
        second_aff_full.columns = ['Offer ID', 'Affiliate', 'clicks_second', 'conversions_second', 'revenue_second_latest']
        
        # 合并两天数据
        affiliate_revenue_diff = latest_aff_full.merge(
            second_aff_full, 
            on=['Offer ID', 'Affiliate'], 
            how='outer'
        ).fillna(0)
        
        # 2. 计算差值和变化率
        # 流水差值
        affiliate_revenue_diff['diff_affiliate_revenue'] = affiliate_revenue_diff['revenue_latest'] - affiliate_revenue_diff['revenue_second_latest']
        affiliate_revenue_diff['diff_affiliate_abs'] = abs(affiliate_revenue_diff['diff_affiliate_revenue'])
        
        # 流水变化率（避免除0）
        affiliate_revenue_diff['revenue_change_rate'] = np.where(
            affiliate_revenue_diff['revenue_second_latest'] > 0,
            affiliate_revenue_diff['diff_affiliate_revenue'] / affiliate_revenue_diff['revenue_second_latest'],
            np.where(affiliate_revenue_diff['revenue_latest'] > 0, 1, 0)
        )
        
        # 点击变化率
        affiliate_revenue_diff['clicks_change_rate'] = np.where(
            affiliate_revenue_diff['clicks_second'] > 0,
            (affiliate_revenue_diff['clicks_latest'] - affiliate_revenue_diff['clicks_second']) / affiliate_revenue_diff['clicks_second'],
            np.where(affiliate_revenue_diff['clicks_latest'] > 0, 1, 0)
        )
        
        # CR（转化/点击）和CR变化
        affiliate_revenue_diff['cr_latest'] = np.where(
            affiliate_revenue_diff['clicks_latest'] > 0,
            affiliate_revenue_diff['conversions_latest'] / affiliate_revenue_diff['clicks_latest'],
            0
        )
        affiliate_revenue_diff['cr_second'] = np.where(
            affiliate_revenue_diff['clicks_second'] > 0,
            affiliate_revenue_diff['conversions_second'] / affiliate_revenue_diff['clicks_second'],
            0
        )
        affiliate_revenue_diff['cr_change'] = affiliate_revenue_diff['cr_latest'] - affiliate_revenue_diff['cr_second']
        
        # 3. 筛选显著影响的Affiliate
        significant_diff = affiliate_revenue_diff[affiliate_revenue_diff['diff_affiliate_abs'] >= AFFILIATE_DIFF_THRESHOLD].copy()
        
        if len(significant_diff) > 0:
            significant_diff.sort_values(
                by=['Offer ID', 'diff_affiliate_revenue'],
                ascending=[True, True],
                inplace=True,
                ignore_index=True
            )

            def generate_influence_text(row):
                revenue_latest = float(row['revenue_latest'])
                revenue_second = float(row['revenue_second_latest'])
                diff_revenue = float(row['diff_affiliate_revenue'])
                
                if revenue_latest > 0 and revenue_second == 0:
                    return f"{row['Affiliate']}新增流水{round(revenue_latest, 2)}美金"
                
                elif revenue_latest == 0 and revenue_second > 0:
                    return f"{row['Affiliate']}停止产生流水，减少流水{round(revenue_second, 2)}美金"
                
                else:
                    if diff_revenue < 0:
                        revenue_abs = abs(diff_revenue)
                        revenue_text = f"减少流水{round(revenue_abs, 2)}美金"
                        revenue_rate = abs(float(row['revenue_change_rate']))
                        revenue_rate_text = f"{round(revenue_rate * 100, 1)}%" if revenue_rate > 0 else "0.0%"
                        full_revenue_text = f"{row['Affiliate']}{revenue_text}/{revenue_rate_text}"
                    else:
                        revenue_text = f"增加流水{round(diff_revenue, 2)}美金"
                        revenue_rate = float(row['revenue_change_rate'])
                        revenue_rate_text = f"{round(revenue_rate * 100, 1)}%" if revenue_rate > 0 else "0.0%"
                        full_revenue_text = f"{row['Affiliate']}{revenue_text}/{revenue_rate_text}"
                    
                    clicks_rate = float(row['clicks_change_rate'])
                    clicks_abs_rate = abs(clicks_rate)
                    if clicks_rate > 0:
                        clicks_text = f"Total Clicks增加{round(clicks_abs_rate * 100, 1)}%"
                    elif clicks_rate < 0:
                        clicks_text = f"Total Clicks减少{round(clicks_abs_rate * 100, 1)}%"
                    else:
                        clicks_text = "Total Clicks无变化"
                    
                    cr_change = float(row['cr_change'])
                    cr_abs_change = abs(cr_change)
                    if cr_change > 0:
                        cr_text = f"CR增加{round(cr_abs_change * 100, 1)}%"
                    elif cr_change < 0:
                        cr_text = f"CR减少{round(cr_abs_change * 100, 1)}%"
                    else:
                        cr_text = "CR无变化"
                    
                    return f"{full_revenue_text}，对应{clicks_text}，{cr_text}"
            
            significant_diff['influence_text'] = significant_diff.apply(generate_influence_text, axis=1)

            def aggregate_affiliate_text(group):
                return '\n'.join(group['influence_text'].tolist())
            
            influence_affiliate_temp = significant_diff.groupby('Offer ID').apply(
                aggregate_affiliate_text
            ).reset_index(name='influence_affiliate')
            
            influence_affiliate_summary = offer_summary[['Offer ID']].merge(
                influence_affiliate_temp, on='Offer ID', how='left'
            ).fillna({'influence_affiliate': ''})
    
    # 无显著影响规则应用
    high_diff_offers = offer_summary[
        abs(offer_summary['total_revenue'] - offer_summary['total_revenue'].shift(1)) >= OFFER_DIFF_THRESHOLD
    ]['Offer ID'].tolist() if 'total_revenue' in offer_summary.columns else []
    affiliate_diff_data = affiliate_revenue_diff if 'affiliate_revenue_diff' in locals() else pd.DataFrame()
    
    no_significant_impact_offers = []
    for offer_id in high_diff_offers:
        offer_aff_diff = affiliate_diff_data[affiliate_diff_data['Offer ID'] == offer_id] if len(affiliate_diff_data) > 0 else pd.DataFrame()
        if len(offer_aff_diff) > 0:
            max_aff_diff = offer_aff_diff['diff_affiliate_abs'].max() if 'diff_affiliate_abs' in offer_aff_diff.columns else 0
            if max_aff_diff < AFFILIATE_DIFF_THRESHOLD:
                no_significant_impact_offers.append(offer_id)
    
    # 填充无显著影响文本
    if 'influence_affiliate_summary' in locals():
        for idx, row in influence_affiliate_summary.iterrows():
            offer_id = row['Offer ID']
            if offer_id in no_significant_impact_offers:
                influence_affiliate_summary.at[idx, 'influence_affiliate'] = '无显著影响'
            else:
                influence_affiliate_summary.at[idx, 'influence_affiliate'] = row['influence_affiliate'] if row['influence_affiliate'] else ''
    else:
        # 初始化空的波动分析结果
        influence_affiliate_summary = pd.DataFrame({'Offer ID': offer_summary['Offer ID'], 'influence_affiliate': ''})
    # ==================== 新增结束 ====================

    # 8. 生成待办事项
    print("\n=== 8. 生成待办事项 ===")
    todo_base_data = offer_summary.merge(affiliate_summary, on='Offer ID', how='left').fillna({'affilate_revenue_rate_all': ''})
    todo_base_data = todo_base_data.merge(latest_summary, on='Offer ID', how='left').fillna(0)
    todo_base_data = todo_base_data.merge(second_summary, on='Offer ID', how='left').fillna(0)
    todo_base_data = todo_base_data.merge(latest_affiliate_summary, on='Offer ID', how='left').fillna({'latest_affilate_revenue_rate_all': ''})
    # 合并波动分析结果到待办数据
    todo_base_data = todo_base_data.merge(influence_affiliate_summary, on='Offer ID', how='left').fillna({'influence_affiliate': ''})
    
    todo_base_data['预算空间'] = np.where(
        (todo_base_data['Total caps'].notna()) & (todo_base_data[f'{latest_date_str}_total_conversions'].notna()),
        todo_base_data['Total caps'] - todo_base_data[f'{latest_date_str}_total_conversions'],
        0
    ).astype(int)
    
    todo_list = []
    triggered_123_offer_ids = set()
    triggered_45_affiliate = set()

    # 规则3
    print("  处理规则3：ACTIVE+预算空间<0...")
    rule3_data = todo_base_data[
        (todo_base_data['Status'].str.upper() == 'ACTIVE') & 
        (todo_base_data['预算空间'] < 0) & 
        (~todo_base_data['Advertiser'].isin(BLACKLIST_CONFIG['advertiser_blacklist']))
    ].copy()
    
    print(f"  规则3筛选出的Offer数量：{len(rule3_data)}")
    if 108906 in rule3_data['Offer ID'].values:
        row_108906 = rule3_data[rule3_data['Offer ID'] == 108906].iloc[0]
        print(f"  ✅ Offer ID 108906 符合规则3条件：")
        print(f"     - 状态：{row_108906['Status']}")
        print(f"     - 预算空间：{row_108906['预算空间']}")
        print(f"     - 广告主：{row_108906['Advertiser']}")
    
    for _, row in rule3_data.iterrows():
        todo_list.append({
            'Offer ID': row['Offer ID'],
            'Advertiser': row['Advertiser'],
            'App ID': row['App ID'],
            'GEO': row['GEO'],
            'Total caps': row['Total caps'],
            'Status': row['Status'],
            '预算空间': row['预算空间'],
            'Affiliate': '',
            '待办事项': '请询问广告主是否有预算增加空间',
            f'{latest_date_str}_total_revenue': row[f'{latest_date_str}_total_revenue'],
            f'{second_latest_date_str}_total_revenue': row[f'{second_latest_date_str}_total_revenue'],
            'affilate_revenue_rate_all': row['affilate_revenue_rate_all'],
            'latest_affilate_revenue_rate_all': row['latest_affilate_revenue_rate_all'],
            'influence_affiliate': row['influence_affiliate']  # 新增：波动原因
        })
    triggered_123_offer_ids.update(rule3_data['Offer ID'].tolist())
    
    # 规则1
    print("  处理规则1：最新无流水+次新有流水...")
    rule1_data = todo_base_data[
        (todo_base_data[f'{latest_date_str}_total_revenue'] == 0) & 
        (todo_base_data[f'{second_latest_date_str}_total_revenue'] > 10) &
        (~todo_base_data['Advertiser'].isin(BLACKLIST_CONFIG['advertiser_blacklist']))
    ].copy()
    for _, row in rule1_data.iterrows():
        todo_list.append({
            'Offer ID': row['Offer ID'],
            'Advertiser': row['Advertiser'],
            'App ID': row['App ID'],
            'GEO': row['GEO'],
            'Total caps': row['Total caps'],
            'Status': row['Status'],
            '预算空间': row['预算空间'],
            'Affiliate': '',
            '待办事项': '请确认该预算暂停原因，比如是否质量不行、CPA预算波动比较大、预算换到新id',
            f'{latest_date_str}_total_revenue': row[f'{latest_date_str}_total_revenue'],
            f'{second_latest_date_str}_total_revenue': row[f'{second_latest_date_str}_total_revenue'],
            'affilate_revenue_rate_all': row['affilate_revenue_rate_all'],
            'latest_affilate_revenue_rate_all': row['latest_affilate_revenue_rate_all'],
            'influence_affiliate': row['influence_affiliate']  # 新增：波动原因
        })
    triggered_123_offer_ids.update(rule1_data['Offer ID'].tolist())
    
    # 规则2
    print("  处理规则2：Pause+收入波动显著...")
    rule2_data = todo_base_data[
        (todo_base_data['Status'].str.upper() == 'PAUSE') & 
        (todo_base_data[f'{latest_date_str}_total_revenue'] >= 10) & 
        (abs(todo_base_data[f'{latest_date_str}_total_revenue'] - todo_base_data[f'{second_latest_date_str}_total_revenue']) >= 10) &
        (~todo_base_data['Advertiser'].isin(BLACKLIST_CONFIG['advertiser_blacklist']))
    ].copy()
    for _, row in rule2_data.iterrows():
        todo_list.append({
            'Offer ID': row['Offer ID'],
            'Advertiser': row['Advertiser'],
            'App ID': row['App ID'],
            'GEO': row['GEO'],
            'Total caps': row['Total caps'],
            'Status': row['Status'],
            '预算空间': row['预算空间'],
            'Affiliate': '',
            '待办事项': '关注今日是否有流水，如果无流水或者比昨日流水少10美金以上，和广告主确认暂停原因，如是否预算不够，否则保持观察',
            f'{latest_date_str}_total_revenue': row[f'{latest_date_str}_total_revenue'],
            f'{second_latest_date_str}_total_revenue': row[f'{second_latest_date_str}_total_revenue'],
            'affilate_revenue_rate_all': row['affilate_revenue_rate_all'],
            'latest_affilate_revenue_rate_all': row['latest_affilate_revenue_rate_all'],
            'influence_affiliate': row['influence_affiliate']  # 新增：波动原因
        })
    triggered_123_offer_ids.update(rule2_data['Offer ID'].tolist())
    
    # 规则4
    print("  处理规则4：ACTIVE+预算>0+流水差值≤5或增长≥5...")
    rule4_offer_data = todo_base_data[
        (todo_base_data['Status'].str.upper() == 'ACTIVE') & 
        (todo_base_data['预算空间'] > 0) & 
        (~todo_base_data['Offer ID'].isin(triggered_123_offer_ids)) &
        (~todo_base_data.apply(lambda row: is_in_blacklist(row['Advertiser'], ''), axis=1))
    ].copy()

    print(f"  规则4初始筛选Offer数量：{len(rule4_offer_data)}")
    rule4_count = 0
    
    for _, offer_row in rule4_offer_data.iterrows():
        offer_id = offer_row['Offer ID']
        history_affs = parse_affiliate_rate_text(offer_row['affilate_revenue_rate_all'])
        latest_affs = parse_affiliate_rate_text(offer_row['latest_affilate_revenue_rate_all'])
        all_affs = list(set(history_affs + latest_affs))
        
        if offer_id == TARGET_OFFER_ID:
            print(f"\n📌 调试Offer {TARGET_OFFER_ID}：提取到Affiliate列表 {all_affs}")
        
        if not all_affs:
            continue
        
        for aff in all_affs:
            if is_in_blacklist(offer_row['Advertiser'], aff):
                continue
            
            revenue_diff = get_affiliate_revenue_diff(qualified_df, offer_id, aff, latest_date, second_latest_date)
            
            if pd.notna(revenue_diff) and (abs(revenue_diff) <= RULE4_REVENUE_DIFF_ABS or revenue_diff >= RULE4_REVENUE_DIFF_UP):
                todo_list.append({
                    'Offer ID': offer_id,
                    'Advertiser': offer_row['Advertiser'],
                    'App ID': offer_row['App ID'],
                    'GEO': offer_row['GEO'],
                    'Total caps': offer_row['Total caps'],
                    'Status': offer_row['Status'],
                    '预算空间': offer_row['预算空间'],
                    'Affiliate': aff,
                    '待办事项': '优先push该下游消耗预算，原因该下游历史或者最新一天有产生过流水且该预算仍有空间',
                    f'{latest_date_str}_total_revenue': offer_row[f'{latest_date_str}_total_revenue'],
                    f'{second_latest_date_str}_total_revenue': offer_row[f'{second_latest_date_str}_total_revenue'],
                    'affilate_revenue_rate_all': offer_row['affilate_revenue_rate_all'],
                    'latest_affilate_revenue_rate_all': offer_row['latest_affilate_revenue_rate_all'],
                    'influence_affiliate': offer_row['influence_affiliate']  # 新增：波动原因
                })
                triggered_45_affiliate.add((offer_id, aff))
                rule4_count += 1
                
                if offer_id == TARGET_OFFER_ID:
                    print(f"  ✅ Offer {offer_id} | Affiliate {aff} 触发规则4")
    
    print(f"  规则4最终触发数量：{rule4_count}")
    
    # 规则5
    print("  处理规则5：ACTIVE+预算>0+收入减少>5...")
    rule5_offer_data = todo_base_data[
    (todo_base_data['Status'].str.upper() == 'ACTIVE') & 
    (todo_base_data['预算空间'] > 0) & 
    (~todo_base_data['Offer ID'].isin(triggered_123_offer_ids)) &
    (~todo_base_data.apply(lambda row: is_in_blacklist(row['Advertiser'], ''), axis=1))
    ].copy()

    rule5_count = 0
    for _, offer_row in rule5_offer_data.iterrows():
        offer_id = offer_row['Offer ID']
        history_affs = parse_affiliate_rate_text(offer_row['affilate_revenue_rate_all'])
        latest_affs = parse_affiliate_rate_text(offer_row['latest_affilate_revenue_rate_all'])
        all_affs = list(set(history_affs + latest_affs))
        
        if not all_affs:
            continue
        
        for aff in all_affs:
            if is_in_blacklist(offer_row['Advertiser'], aff):
                continue
            
            revenue_diff = get_affiliate_revenue_diff(qualified_df, offer_id, aff, latest_date, second_latest_date)
            
            if pd.notna(revenue_diff) and revenue_diff < RULE5_REVENUE_DIFF_THRESHOLD:
                todo_list.append({
                    'Offer ID': offer_id,
                    'Advertiser': offer_row['Advertiser'],
                    'App ID': offer_row['App ID'],
                    'GEO': offer_row['GEO'],
                    'Total caps': offer_row['Total caps'],
                    'Status': offer_row['Status'],
                    '预算空间': offer_row['预算空间'],
                    'Affiliate': aff,
                    '待办事项': '和下游沟通减少原因',
                    f'{latest_date_str}_total_revenue': offer_row[f'{latest_date_str}_total_revenue'],
                    f'{second_latest_date_str}_total_revenue': offer_row[f'{second_latest_date_str}_total_revenue'],
                    'affilate_revenue_rate_all': offer_row['affilate_revenue_rate_all'],
                    'latest_affilate_revenue_rate_all': offer_row['latest_affilate_revenue_rate_all'],
                    'influence_affiliate': offer_row['influence_affiliate']  # 新增：波动原因
                })
                triggered_45_affiliate.add((offer_id, aff))
                rule5_count += 1
                
                if offer_id == TARGET_OFFER_ID:
                    print(f"  ✅ Offer {offer_id} | Affiliate {aff} 触发规则5")
    
    print(f"  规则5最终触发数量：{rule5_count}")
    
    # ========== 规则6：ACTIVE+预算充足+类型匹配 ==========
    # 步骤1：从AFFILIATE_TYPE_MAP中提取所有Affiliate名称（无视流水）
    all_affs_from_map = list(AFFILIATE_TYPE_MAP.keys())
    
    # 步骤2：筛选符合规则6的Offer
    rule6_offers = todo_base_data[
        (todo_base_data['Status'].str.upper() == 'ACTIVE') &
        (todo_base_data['预算空间'] > 0) &
        (~todo_base_data['Offer ID'].isin(triggered_123_offer_ids)) &
        (~todo_base_data.apply(lambda row: is_in_blacklist(row['Advertiser'], ''), axis=1))
    ].copy()
    
    # 计算每个offerid过去30天的total revenue
    offer_30d_revenue = qualified_df.groupby('Offer ID')['Total Revenue'].sum().reset_index()
    offer_30d_revenue.columns = ['Offer ID', 'total_revenue_30d']
    
    # 新增：构建(geo, app id, affiliate)组合的规则4/5触发记录
    triggered_45_geo_app_aff = set()
    for (offer_id, aff) in triggered_45_affiliate:
        # 获取该offer的geo和app id
        offer_data = todo_base_data[todo_base_data['Offer ID'] == offer_id]
        if not offer_data.empty:
            geo = offer_data['GEO'].iloc[0] if pd.notna(offer_data['GEO'].iloc[0]) else ''
            app_id = offer_data['App ID'].iloc[0] if pd.notna(offer_data['App ID'].iloc[0]) else ''
            triggered_45_geo_app_aff.add((geo, app_id, aff))
    
    #按(geo, app id, affiliate)组合筛选最高流水的Offer ID
    print("\n=== 规则6优化：按组合筛选高流水Offer ===")
    
    # 收集所有可能的规则6触发项（不立即添加到todo_list）
    rule6_candidates = []
    
    rule6_count = 0
    for _, offer_row in rule6_offers.iterrows():
        offer_id = offer_row['Offer ID']
        advertiser = offer_row['Advertiser']
        geo = offer_row['GEO'] if pd.notna(offer_row['GEO']) else ''
        app_id = offer_row['App ID'] if pd.notna(offer_row['App ID']) else ''
        
        # 获取该offer的30天总流水
        offer_revenue_data = offer_30d_revenue[offer_30d_revenue['Offer ID'] == offer_id]
        total_revenue_30d = offer_revenue_data['total_revenue_30d'].iloc[0] if not offer_revenue_data.empty else 0
        
        # 获取广告主类型
        advertiser_type = ''
        for adv_key, adv_type in ADVERTISER_TYPE_MAP.items():
            if adv_key in advertiser:
                advertiser_type = adv_type
                break
        if not advertiser_type:
            continue  # 广告主无类型，跳过

        
        # 遍历AFFILIATE_TYPE_MAP中的所有Affiliate（无视流水）
        for aff in all_affs_from_map:
            # 过滤黑名单
            if is_in_blacklist(advertiser, aff):
                continue
            # 过滤已触发4/5的Affiliate（原有逻辑保留）
            if (offer_id, aff) in triggered_45_affiliate:
                continue
            
            # 新增：过滤已触发4/5的(geo, app id, affiliate)组合
            if (geo, app_id, aff) in triggered_45_geo_app_aff:
                continue
            
            # 获取Affiliate类型
            aff_type = AFFILIATE_TYPE_MAP[aff]
            
            # 类型匹配判断
            match_flag = False
            if advertiser_type == 'xdj流量' and aff_type in('xdj流量','inapp流量/xdj流量'):
                match_flag = True
            elif advertiser_type == 'xdj流量/inapp流量' and aff_type in('inapp流量','inapp流量/xdj流量'):
                match_flag = True
            
            # 触发规则6候选
            if match_flag:
                rule6_candidates.append({
                    'Offer ID': offer_id,
                    'Advertiser': advertiser,
                    'Affiliate': aff,
                    'GEO': geo,
                    'App ID': app_id,
                    'total_revenue_30d': total_revenue_30d,
                    '组合键': f"{geo}_{app_id}_{aff}",  # 用于分组
                    '原始数据': offer_row  # 保留原始数据用于后续构造
                })
                
                if offer_id == TARGET_OFFER_ID:
                    print(f"  ✅ Offer {offer_id} | Affiliate {aff} 成为规则6候选")
                    print(f"     - 组合键：{geo}_{app_id}_{aff}")
                    print(f"     - 30天流水：{total_revenue_30d:.2f}美金")
    
    # 按组合筛选最高流水Offer
    if rule6_candidates:
        # 转换为DataFrame便于处理
        candidates_df = pd.DataFrame(rule6_candidates)
        
        # 按组合键分组，选择每个组合中流水最高的Offer
        best_offers_by_combo = candidates_df.loc[candidates_df.groupby('组合键')['total_revenue_30d'].idxmax()]
        best_offers_by_combo.to_csv('输出数据.csv')
        best_offers_by_combo = best_offers_by_combo[best_offers_by_combo['total_revenue_30d'] >= 5]
        print(f"\n📊 规则6组合筛选结果：")
        print(f"   - 原始候选数：{len(candidates_df)}")
        print(f"   - 去重后数量：{len(best_offers_by_combo)}")
        print(f"   - 唯一组合数：{best_offers_by_combo['组合键'].nunique()}")
        
        # 将筛选后的结果添加到todo_list
        for _, best_offer in best_offers_by_combo.iterrows():
            original_data = best_offer['原始数据']
            todo_list.append({
                'Offer ID': best_offer['Offer ID'],
                'Advertiser': best_offer['Advertiser'],
                'Affiliate': best_offer['Affiliate'],
                'GEO': best_offer['GEO'],
                'App ID': best_offer['App ID'],
                '待办事项': '历史可能未推下游，尝试push（按组合筛选最高流水）',
                'influence_affiliate': original_data['influence_affiliate'],
                'total_revenue_30d': best_offer['total_revenue_30d'],
                f'{latest_date_str}_total_revenue': original_data[f'{latest_date_str}_total_revenue'],
                f'{second_latest_date_str}_total_revenue': original_data[f'{second_latest_date_str}_total_revenue'],
                'affilate_revenue_rate_all': original_data['affilate_revenue_rate_all'],
                'latest_affilate_revenue_rate_all': original_data['latest_affilate_revenue_rate_all']
            })
            rule6_count += 1
            
            if best_offer['Offer ID'] == TARGET_OFFER_ID:
                print(f"  🎯 Offer {best_offer['Offer ID']} 在组合 {best_offer['组合键']} 中胜出")
                print(f"     - 30天流水：{best_offer['total_revenue_30d']:.2f}美金")
    
    print(f"  规则6触发数量：{rule6_count}")     
    
    # 转换为DataFrame并去重
    todo_df = pd.DataFrame(todo_list).drop_duplicates(subset=['Offer ID', 'Affiliate', '待办事项'])
    print(f"\n✅ 待办事项总计：{len(todo_df)}条")

    

            

    # 9. 生成最终Excel

    print("\n=== 9. 生成Excel文件 ===")
    final_offer_analysis = offer_summary.merge(affiliate_summary, on='Offer ID', how='left').fillna({'affilate_revenue_rate_all': ''})
    final_offer_analysis = final_offer_analysis.merge(latest_summary, on='Offer ID', how='left').fillna(0)
    final_offer_analysis = final_offer_analysis.merge(second_summary, on='Offer ID', how='left').fillna(0)
    final_offer_analysis = final_offer_analysis.merge(latest_affiliate_summary, on='Offer ID', how='left').fillna({'latest_affilate_revenue_rate_all': ''})
    final_offer_analysis = final_offer_analysis.merge(influence_affiliate_summary, on='Offer ID', how='left').fillna({'influence_affiliate': ''})
    
    # 定义final_offer_analysis的列顺序
    final_offer_analysis_columns = [
        'Offer ID', 'Advertiser', 'App ID', 'GEO', 
        'total_clicks', 'total_conversions', 'total_revenue', 'total_profit',
        'Total caps', 'Status', 'affilate_revenue_rate_all',
        f'{latest_date_str}_total_clicks', f'{latest_date_str}_total_conversions', 
        f'{latest_date_str}_total_revenue', f'{latest_date_str}_total_profit',
        f'{second_latest_date_str}_total_clicks', f'{second_latest_date_str}_total_conversions', 
        f'{second_latest_date_str}_total_revenue', f'{second_latest_date_str}_total_profit',
        'latest_affilate_revenue_rate_all', 'influence_affiliate'
    ]
    
    # 重新排列final_offer_analysis的列顺序
    existing_columns = [col for col in final_offer_analysis_columns if col in final_offer_analysis.columns]
    extra_columns = [col for col in final_offer_analysis.columns if col not in final_offer_analysis_columns]
    final_offer_analysis = final_offer_analysis[existing_columns + extra_columns]
    
    # 创建增强的待办事项列表，包含所有列
    enhanced_todo_list = []
    
    for todo_item in todo_list:
        # 获取该Offer ID在final_offer_analysis中的所有数据
        offer_id = todo_item['Offer ID']
        offer_data = final_offer_analysis[final_offer_analysis['Offer ID'] == offer_id]
        
        if len(offer_data) > 0:
            # 获取第一行数据（每个Offer ID应该只有一行）
            offer_row = offer_data.iloc[0]
            
            # 创建增强的待办事项项，包含所有列
            enhanced_todo = {}
            
            # 首先添加final_offer_analysis的所有列
            for column in final_offer_analysis.columns:
                enhanced_todo[column] = offer_row[column]
            
            # 然后添加待办事项特有的列（覆盖可能存在的同名列）
            enhanced_todo.update({
                'Affiliate': todo_item.get('Affiliate', ''),
                '待办事项': todo_item.get('待办事项', ''),
                # 确保预算空间列使用待办事项中的值（因为可能重新计算过）
                '预算空间': todo_item.get('预算空间', offer_row.get('预算空间', 0))
            })
            
            enhanced_todo_list.append(enhanced_todo)
        else:
            # 如果找不到对应的Offer数据，使用原始待办事项
            print(f"⚠️ 警告：Offer ID {offer_id} 在final_offer_analysis中未找到，使用原始待办事项数据")
            enhanced_todo_list.append(todo_item)
    
    # 转换为DataFrame
    if enhanced_todo_list:
        # 定义enhanced_todo_df的列顺序
        enhanced_todo_columns = existing_columns + ['Affiliate', '待办事项', '预算空间'] + extra_columns
        
        enhanced_todo_df = pd.DataFrame(enhanced_todo_list)
        
        # 确保列顺序
        existing_enhanced_columns = [col for col in enhanced_todo_columns if col in enhanced_todo_df.columns]
        enhanced_todo_df = enhanced_todo_df[existing_enhanced_columns]
    else:
        enhanced_todo_df = pd.DataFrame(todo_list)
    
    # 去重
    enhanced_todo_df = enhanced_todo_df.drop_duplicates(subset=['Offer ID', 'Affiliate', '待办事项'])

    revenue_ranking_df = calculate_revenue_ranking(qualified_df)

    
    final_offer_analysis = final_offer_analysis.merge(
        revenue_ranking_df[['Offer ID','Advertiser','Advertiser_Rank']],
        on=['Offer ID','Advertiser'],
        how='left'
    )

    enhanced_todo_df = enhanced_todo_df.merge(
        revenue_ranking_df[['Offer ID','Advertiser','Advertiser_Rank']],
        on=['Offer ID','Advertiser'],
        how='left'
    )
    
    if progress_bar and status_text:
        progress_bar.progress(100)
        status_text.text("🎉 处理完成！")
    
    return final_offer_analysis, enhanced_todo_df, latest_date

# ==================== 文件下载功能 ====================
def get_excel_download_link(final_df, todo_df, latest_date):
    """生成Excel文件下载链接"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df.to_excel(writer, sheet_name='Offer Analysis', index=False)
        todo_df.to_excel(writer, sheet_name='预算待办事项', index=False)
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    filename = f"offer_analysis_{latest_date.strftime('%Y%m%d')}.xlsx"
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 下载完整分析报告</a>'
    return href

# ==================== Streamlit主界面 ====================
def main():
    st.markdown('<div class="main-header">📊 重点预算分析，每天下午5点前必须更新完今日待办事项进度</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("📋 使用说明")
        st.markdown("""
        **无需安装任何软件，直接在网页中使用！**
        
        ### 使用步骤：
        1. 下载Excel模板文件
        2. 按照模板格式填写数据
        3. 上传填写好的Excel文件
        4. 系统自动分析并生成报告
        
        
        ### 支持功能：
        - ✅ 根据最近30天流水数据对高差异Offer智能分析
        - ✅ Affiliate维度精准分析
        - ✅ 一键下载完整报告
        """)
        st.header("⚙️ 分析规则")
        
        st.info("""
        - 规则1：状态为"PAUSE"，最新一天无流水，次新一天流水>=10美金，排查突然停止流水的Offer
        - 规则2：状态为"PAUSE"，且最新一天流水≥10美金，且与次新一天流水差绝对值≥10美金，监控暂停状态的异常收入波动，防止误暂停。 
        - 规则3：状态为"ACTIVE"，且预算空间<0，状态为"ACTIVE"，且预算空间<0请询问广告主是否有预算增加空间
        - 规则4：状态为"ACTIVE"，预算空间>0，且Affiliate流水变化：差值绝对值≤5美金或流水增长≥5美金，激励高潜力Affiliate加大投放，提升预算消耗。
        - 规则5：​状态为"ACTIVE"，预算空间>0，且Affiliate流水减少>5美金，排查收入下降根源，及时修复流量下滑
        - 规则6：​状态为"ACTIVE"，预算空间>0，且广告主类型与Affiliate类型匹配，开拓新流量来源
        """)
        

    # 主内容区
    st.markdown("### 📥 第一步：下载Excel模板")
    # 模板下载区域
    st.markdown(get_template_download_link(), unsafe_allow_html=True)

    # col2 的内容（占满整行宽度）
    with st.expander("📖 模板说明", expanded=True):
        st.markdown("""
        **模板包含：**
        - 📊 主数据表（1-all data）
        - ⚠️ 黑名单表（blacklist）
        - 📝 完整字段说明
        - 🎯 示例数据
        """)
    
    # 模板使用说明
    with st.expander("📋 模板详细使用说明", expanded=False):
        st.markdown(get_template_instructions())

    # 文件上传区域
    st.markdown("### 📤 第二步：上传Excel文件")
    
    uploaded_file = st.file_uploader(
        "选择Excel文件（支持.xlsx格式）",
        type=['xlsx'],
        help="请上传包含Offer数据的Excel文件，包含Time、Offer ID、Total Revenue等字段"
    )
    
    if uploaded_file is not None:
        try:
            # 显示文件信息
            file_details = {
                "文件名": uploaded_file.name,
                "文件类型": uploaded_file.type,
                "文件大小": f"{uploaded_file.size / 1024:.2f} KB"
            }
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.json(file_details)
            
            # 数据预览
            with st.expander("📖 数据预览（前5行）", expanded=True):
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(), use_container_width=True)
            
            # 开始分析按钮
            if st.button("🚀 开始分析数据", type="primary", use_container_width=True):
                # 创建进度条
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 处理数据
                with st.spinner("数据分析中，请稍候..."):
                    try:
                        final_offer_analysis, todo_df, latest_date = process_offer_data_web(
                            uploaded_file, progress_bar, status_text
                        )
                        
                        # 显示分析结果
                        st.markdown("### 📈 分析结果")
                        
                        # 关键指标
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Offer分析记录数", len(final_offer_analysis))
                        with col2:
                            st.metric("待办事项数", len(todo_df))
                        with col3:
                            st.metric("分析日期", latest_date.strftime("%Y/%m/%d"))
                        
                        # 结果显示标签页
                        result_tab1, result_tab2, result_tab3 = st.tabs(["📊 Offer分析结果", "✅ 待办事项", "📥 下载报告"])
                        
                        with result_tab1:
                            st.dataframe(final_offer_analysis, use_container_width=True)
                        
                        with result_tab2:
                            st.dataframe(todo_df, use_container_width=True)
                        
                        with result_tab3:
                            st.markdown("### 📥 下载分析报告")
                            
                            # Offer分析报告下载
                            st.markdown(get_excel_download_link(final_offer_analysis, todo_df, latest_date), 
                                      unsafe_allow_html=True)
                            
                            st.success("✅ 分析完成！点击上方链接下载报告")
                        
                    except Exception as e:
                        st.error(f"❌ 分析过程中出现错误：{str(e)}")
                        st.code(str(e))
            
        except Exception as e:
            st.error(f"❌ 文件读取失败：{str(e)}")
    else:
        st.info("👆 请先上传Excel文件开始分析")

if __name__ == "__main__":
    main()
