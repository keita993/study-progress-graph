import pandas as pd
import matplotlib
matplotlib.use('Agg')  # バックエンドを明示的に設定
import matplotlib.pyplot as plt
import japanize_matplotlib
import streamlit as st
from datetime import datetime
import io

st.set_page_config(
    page_title="応用情報技術者試験 学習分析",
    page_icon="📊",
    layout="wide"
)

st.title("応用情報技術者試験 学習分析")

use_sample = st.checkbox("サンプルデータを使用する")

if use_sample:
    uploaded_file = "sample_data.csv"
    st.info("サンプルデータを使用しています。自分のデータを分析するには、チェックを外してCSVファイルをアップロードしてください。")
else:
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    try:
        # CSVファイルを読み込む
        if use_sample:
            df = pd.read_csv(uploaded_file, encoding='shift-jis')
        else:
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
        
        # 正答率を数値型に変換（%表記を小数点に）
        df['正答率'] = df['正答率'].str.rstrip('%').astype(float) / 100
        
        # 概要情報
        st.header("概要")
        col1, col2 = st.columns(2)
        
        # 最近の傾向（直近7日間と全体の比較）
        recent_dates = sorted(df['学習日'].unique())[-7:]
        recent_df = df[df['学習日'].isin(recent_dates)]
        recent_avg = recent_df['正答率'].mean()
        overall_avg = df['正答率'].mean()
        
        with col1:
            st.metric("全体の平均正答率", f"{overall_avg*100:.1f}%")
        with col2:
            st.metric("直近の平均正答率", f"{recent_avg*100:.1f}%", 
                     f"{(recent_avg-overall_avg)*100:.1f}%")
        
        # 日付ごとの平均正答率を計算
        daily_avg = df.groupby('学習日')['正答率'].mean()
        
        # 分野ごとの平均正答率を計算
        category_avg = df.groupby('分野')['正答率'].mean().sort_values(ascending=False)
        
        # グラフの作成（日付ごとの平均正答率）
        st.header("日付ごとの平均正答率")
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        daily_avg.plot(kind='line', marker='o', ax=ax1)
        ax1.set_title('日付ごとの平均正答率')
        ax1.set_xlabel('学習日')
        ax1.set_ylabel('平均正答率')
        ax1.grid(True)
        plt.tight_layout()
        st.pyplot(fig1)
        
        # グラフの作成（分野ごとの平均正答率）
        st.header("分野ごとの平均正答率")
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        category_avg.plot(kind='bar', ax=ax2)
        ax2.set_title('分野ごとの平均正答率')
        ax2.set_xlabel('分野')
        ax2.set_ylabel('平均正答率')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig2)
        
        # 分野ごとの問題数
        category_count = df.groupby('分野').size().sort_values(ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("分野ごとの問題数")
            st.dataframe(category_count.reset_index().rename(
                columns={'index': '分野', 0: '問題数'}), use_container_width=True)
        
        with col2:
            st.header("日別の平均正答率")
            st.dataframe(daily_avg.reset_index().rename(
                columns={'index': '日付', '正答率': '平均正答率'}), use_container_width=True)
        
        # 詳細データの表示
        st.header("詳細データ")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}") 