import pandas as pd
import matplotlib
matplotlib.use('Agg')  # バックエンドを明示的に設定
# 日本語フォント設定を直接行う
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'Yu Gothic', 'Hiragino Kaku Gothic ProN', 'Meiryo', 'sans-serif']
import matplotlib.pyplot as plt
import streamlit as st
import os
import urllib.request

# ページ設定
st.set_page_config(
    page_title="応用情報技術者試験 学習分析",
    page_icon="📊"
)

st.title("応用情報技術者試験 学習分析")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    try:
        # CSVファイルを読み込む
        df = pd.read_csv(uploaded_file, encoding='shift-jis')
        
        # カラム名を修正（文字化けしている場合）
        if '学習日' not in df.columns and 'wK' in df.columns:
            df = df.rename(columns={
                'wK': '学習日',
                'oT': '出題',
                '': '分野',
                '𓚎': '解答時間',
                '': '正答率',
                '': '回答'
            })
        
        # 日付を日付型に変換
        df['学習日'] = pd.to_datetime(df['学習日'])
        
        # 正答率を数値型に変換
        df['正答率'] = df['正答率'].str.rstrip('%').astype(float) / 100
        
        # 概要情報
        st.header("概要")
        overall_avg = df['正答率'].mean()
        st.metric("全体の平均正答率", f"{overall_avg*100:.1f}%")
        
        # 日付ごとの平均正答率を計算
        daily_avg = df.groupby('学習日')['正答率'].mean()
        
        # 分野ごとの平均正答率を計算
        category_avg = df.groupby('分野')['正答率'].mean().sort_values(ascending=False)
        
        # 日付ごとの平均正答率グラフ
        st.header("日付ごとの平均正答率")
        st.line_chart(daily_avg)
        
        # 分野ごとの平均正答率グラフ
        st.header("分野ごとの平均正答率")
        st.bar_chart(category_avg)
        
        # 分野ごとの問題数
        category_count = df.groupby('分野').size().sort_values(ascending=False)
        
        # データフレーム表示
        st.header("分野ごとの問題数")
        st.dataframe(category_count.reset_index().rename(
            columns={'index': '分野', 0: '問題数'}))
        
        st.header("日別の平均正答率")
        st.dataframe(daily_avg.reset_index().rename(
            columns={'学習日': '日付', '正答率': '平均正答率'}))
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("CSVファイルをアップロードしてください。") 