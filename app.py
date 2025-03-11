import pandas as pd
import matplotlib
matplotlib.use('Agg')  # バックエンドを明示的に設定

# 日本語フォント設定
matplotlib.rcParams['font.family'] = 'IPAGothic'  # Streamlit Cloudで利用可能な日本語フォント

import matplotlib.font_manager as fm
import os

# フォント設定を強化する関数
def setup_japanese_font():
    # システムフォントを探す
    system_fonts = []
    
    # Windowsの場合
    if os.name == 'nt':
        font_paths = [
            r'C:\Windows\Fonts\meiryo.ttc',
            r'C:\Windows\Fonts\msgothic.ttc',
            r'C:\Windows\Fonts\YuGothM.ttc'
        ]
        for path in font_paths:
            if os.path.exists(path):
                system_fonts.append(path)
    
    # macOSの場合
    elif os.name == 'posix' and os.uname().sysname == 'Darwin':
        font_paths = [
            '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
            '/System/Library/Fonts/AppleGothic.ttf',
            '/Library/Fonts/Osaka.ttf'
        ]
        for path in font_paths:
            if os.path.exists(path):
                system_fonts.append(path)
    
    # Linuxの場合
    elif os.name == 'posix':
        font_paths = [
            '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'
        ]
        for path in font_paths:
            if os.path.exists(path):
                system_fonts.append(path)
    
    # システムフォントが見つかった場合は設定
    if system_fonts:
        for font_path in system_fonts:
            try:
                fm.fontManager.addfont(font_path)
                matplotlib.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
                return True
            except:
                continue
    
    # システムフォントが見つからない場合はデフォルト設定
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    
    return False

# フォント設定を適用
setup_japanese_font()

# グラフ描画時のフォント設定を強化
def create_figure(figsize=(10, 6)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    
    # グラフ内のフォント設定
    plt.rcParams['axes.unicode_minus'] = False  # マイナス記号を正しく表示
    plt.rcParams['font.size'] = 12  # フォントサイズ
    
    return fig, ax

import matplotlib.pyplot as plt
import streamlit as st
import os
import urllib.request
import re
import numpy as np

# ページ設定を更新 - より広いレイアウトに
st.set_page_config(
    page_title="応用情報技術者試験 学習分析",
    page_icon="📊",
    layout="wide",  # 画面幅を広く使用
    initial_sidebar_state="collapsed"  # サイドバーを初期状態で折りたたむ
)

# カスタムCSS追加
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f2f6;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0277BD;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #f0f2f6;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff8e1;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0D47A1;
    }
    .dataframe {
        font-size: 0.9rem;
    }
    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E88E5;
        color: white;
    }
    /* 分析セクションの背景色 */
    .section-overview {
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border-left: 5px solid #4CAF50;
    }
    .section-date {
        background-color: #e3f2fd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border-left: 5px solid #2196F3;
    }
    .section-category {
        background-color: #f3e5f5;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border-left: 5px solid #9C27B0;
    }
    .section-time {
        background-color: #fff8e1;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border-left: 5px solid #FFC107;
    }
    .section-ai {
        background-color: #ffebee;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 30px;
        border-left: 5px solid #F44336;
    }
    
    /* セクションタイトルのスタイル */
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
    }
    
    /* セクション内の小見出し */
    .subsection-title {
        font-size: 1.4rem;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# タイトルを装飾
st.markdown('<h1 class="main-header">📊 応用情報技術者試験 学習分析</h1>', unsafe_allow_html=True)

# ファイルアップロード部分を改善
with st.container():
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])
    st.markdown('</div>', unsafe_allow_html=True)

# 分析結果をタブで整理
if uploaded_file is not None:
    try:
        # バイナリモードでファイルを読み込む
        file_content = uploaded_file.read()
        
        # エンコーディングを検出
        try:
            import chardet
            result = chardet.detect(file_content)
            detected_encoding = result['encoding']
            st.info(f"検出されたエンコーディング: {detected_encoding}")
        except:
            detected_encoding = None
        
        # 様々なエンコーディングを試す
        encodings_to_try = ['utf-8-sig', 'utf-8', 'shift-jis', 'cp932', 'euc-jp']
        if detected_encoding and detected_encoding not in encodings_to_try:
            encodings_to_try.insert(0, detected_encoding)
        
        df = None
        error_messages = []
        
        for encoding in encodings_to_try:
            try:
                # StringIOを使用してメモリ上でデコード
                import io
                string_data = io.StringIO(file_content.decode(encoding))
                df = pd.read_csv(string_data)
                st.success(f"エンコーディング '{encoding}' で正常に読み込みました")
                break
            except UnicodeDecodeError as e:
                error_messages.append(f"エンコーディング '{encoding}' でのデコードに失敗: {str(e)}")
                continue
            except Exception as e:
                error_messages.append(f"エンコーディング '{encoding}' での読み込みに失敗: {str(e)}")
                continue
        
        if df is None:
            st.error("すべてのエンコーディングでファイルの読み込みに失敗しました。")
            st.write("エラーメッセージ:")
            for msg in error_messages:
                st.write(f"- {msg}")
            
            # 最後の手段: バイナリモードで直接読み込み
            try:
                import io
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin1', error_bad_lines=False)
                st.warning("ファイルを'latin1'エンコーディングで読み込みました。文字化けが発生する可能性があります。")
            except:
                st.stop()
        
        # カラム名を検出して修正する部分を改善
        if df is not None:
            # 文字化けしたカラム名を修正
            column_mapping = {}
            
            # カラムの位置に基づいて自動検出
            if len(df.columns) >= 6:
                # 典型的なCSVフォーマットの場合
                column_positions = {
                    0: 'No.',
                    1: '学習日',
                    2: '出題',
                    3: '分野',
                    4: '解答時間',
                    5: '正答率',
                    6: '回答'
                }
                
                for i, col in enumerate(df.columns):
                    if i in column_positions:
                        column_mapping[col] = column_positions[i]
            
            # 位置ベースのマッピングがない場合は内容ベースで検出
            if not column_mapping:
                for col in df.columns:
                    col_str = str(col)
                    col_bytes = col_str.encode('unicode_escape')
                    
                    # 学習日カラムの検出
                    if '学習' in col_str or '日付' in col_str or '日時' in col_str or (b'\\u' in col_bytes and (b'w' in col_bytes or b'K' in col_bytes)):
                        column_mapping[col] = '学習日'
                    # 分野カラムの検出
                    elif '分野' in col_str or 'カテゴリ' in col_str or '項目' in col_str or (len(col_str) <= 2 and b'\\u' in col_bytes):
                        column_mapping[col] = '分野'
                    # 正答率カラムの検出
                    elif '正答率' in col_str or '正解率' in col_str or '得点率' in col_str or any(c in col_str for c in ['率', '％', '%']):
                        column_mapping[col] = '正答率'
            
            # カラム名を修正
            if column_mapping:
                df = df.rename(columns=column_mapping)
                st.success("カラム名を自動検出しました")
        
        # 必要なカラムを特定
        date_col = '学習日' if '学習日' in df.columns else None
        category_col = '分野' if '分野' in df.columns else None
        score_col = '正答率' if '正答率' in df.columns else None
        
        # カラムが見つからない場合は位置で推測
        if date_col is None and len(df.columns) > 1:
            date_col = df.columns[1]  # 通常2列目が日付
        
        if category_col is None and len(df.columns) > 3:
            category_col = df.columns[3]  # 通常4列目が分野
        
        if score_col is None and len(df.columns) > 5:
            score_col = df.columns[5]  # 通常6列目が正答率
        
        # それでも見つからない場合はエラー
        if date_col is None or category_col is None or score_col is None:
            st.error("必要なカラムを自動検出できませんでした。CSVファイルの形式を確認してください。")
            st.stop()
        
        # 日付を日付型に変換
        try:
            df[date_col] = pd.to_datetime(df[date_col])
        except:
            st.error(f"日付の変換に失敗しました。カラム '{date_col}' が日付形式であることを確認してください。")
            st.stop()
        
        # 正答率を数値型に変換
        try:
            # パーセント表記（例: 80%）の場合
            if df[score_col].dtype == 'object':
                df[score_col] = df[score_col].astype(str).str.rstrip('%').astype(float) / 100
            
            # すでに小数点表記（例: 0.8）の場合
            if df[score_col].max() > 1:
                df[score_col] = df[score_col] / 100
        except:
            st.error(f"正答率の変換に失敗しました。カラム '{score_col}' が数値またはパーセント形式であることを確認してください。")
            st.stop()
        
        # 必要な変数を計算
        overall_avg = df[score_col].mean()
        daily_avg = df.groupby(date_col)[score_col].mean() * 100
        rolling_avg = daily_avg.rolling(window=7, min_periods=1).mean()
        category_avg = df.groupby(category_col)[score_col].mean() * 100
        category_count = df.groupby(category_col).size()
        total_questions = len(df)
        study_days = len(df[date_col].unique())
        
        # タブを作成
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 概要", "📅 日付分析", "🔍 分野分析", "⏱️ 時間分析", "🤖 AI分析"])
        
        with tab1:
            st.markdown('<div class="section-overview">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📊 学習概要</div>', unsafe_allow_html=True)
            
            # 概要メトリクス
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("全体の平均正答率", f"{overall_avg*100:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("総問題数", f"{total_questions}問")
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("学習日数", f"{study_days}日")
                st.markdown('</div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                st.metric("1日平均問題数", f"{total_questions/study_days:.1f}問")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 学習の進捗状況グラフ
            st.markdown('<div class="subsection-title">学習の進捗状況</div>', unsafe_allow_html=True)
            
            # 累積問題数グラフを追加
            cumulative_questions = df.groupby(date_col).size().cumsum()
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cumulative_questions.index, cumulative_questions.values, marker='o', linestyle='-', linewidth=2)
            ax.set_ylabel('累積問題数')
            ax.set_xlabel('学習日')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 日付ごとの平均正答率グラフ
        with tab2:
            st.markdown('<div class="section-date">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">📅 日付ごとの分析</div>', unsafe_allow_html=True)
            
            # 日付ごとの平均正答率グラフ
            st.markdown('<div class="subsection-title">日付ごとの平均正答率</div>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(daily_avg.index, daily_avg.values, label='日次正答率', marker='o')
            ax.plot(rolling_avg.index, rolling_avg.values, label='7日移動平均', linewidth=2)
            ax.set_ylabel('正答率 (%)')
            ax.set_xlabel('学習日')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            
            # 日付ごとのデータを表示
            st.markdown('<div class="subsection-title">日付ごとの詳細データ</div>', unsafe_allow_html=True)
            
            # 日付ごとのデータを表示用に整形
            daily_data = pd.DataFrame({
                '日付': daily_avg.index,
                '問題数': df.groupby(date_col).size().values,
                '平均正答率': [f"{val:.1f}%" for val in daily_avg.values],
                '7日移動平均': [f"{val:.1f}%" for val in rolling_avg.values]
            })

            # 日付を見やすい形式に変換
            daily_data['日付'] = daily_data['日付'].dt.strftime('%Y-%m-%d')

            # 最新の日付が上に来るように並べ替え
            daily_data = daily_data.sort_values('日付', ascending=False)

            # 表を表示
            st.dataframe(daily_data)

            # CSVダウンロードボタン
            csv = daily_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="日付ごとのデータをCSVでダウンロード",
                data=csv,
                file_name='daily_accuracy.csv',
                mime='text/csv',
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 分野ごとの平均正答率グラフ
        with tab3:
            st.markdown('<div class="section-category">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🔍 分野ごとの分析</div>', unsafe_allow_html=True)
            
            # 分野ごとの正答率と問題数を並べて表示
            col1, col2 = st.columns(2)
            
            # 分野ごとの問題数と正答率表示
            category_stats = category_count.reset_index().rename(columns={category_col: '分野', 0: '問題数'})
            category_percent = category_avg.reset_index()
            category_percent['正答率'] = category_percent[score_col].map('{:.1f}%'.format)
            
            # データフレームをマージ
            category_stats_merged = pd.merge(
                category_stats, 
                category_percent[[category_col, '正答率']], 
                left_on='分野', 
                right_on=category_col
            )
            
            if category_col != '分野':
                category_stats_merged = category_stats_merged.drop(columns=[category_col])
            
            with col1:
                st.markdown('<div class="subsection-title">分野ごとの正答率</div>', unsafe_allow_html=True)
                st.dataframe(category_percent.sort_values(score_col, ascending=False))
            
            with col2:
                st.markdown('<div class="subsection-title">分野ごとの問題数</div>', unsafe_allow_html=True)
                st.dataframe(category_stats)
            
            # 分野ごとの詳細データ
            st.markdown('<div class="subsection-title">分野ごとの詳細データ</div>', unsafe_allow_html=True)
            st.dataframe(category_stats_merged.sort_values('問題数', ascending=False))
            
            # 分野ごとの正答率グラフ
            st.markdown('<div class="subsection-title">分野ごとの正答率グラフ</div>', unsafe_allow_html=True)
            fig, ax = plt.subplots(figsize=(10, 6))
            category_avg_sorted = category_avg.sort_values(ascending=False)
            
            # 横棒グラフで表示
            bars = ax.barh(range(len(category_avg_sorted)), category_avg_sorted.values)
            ax.set_yticks(range(len(category_avg_sorted)))
            ax.set_yticklabels(category_avg_sorted.index)
            ax.set_xlabel('正答率 (%)')
            ax.set_xlim(0, 100)  # 0-100%のスケール
            
            # 棒グラフに値を表示
            for i, (bar, val) in enumerate(zip(bars, category_avg_sorted.values)):
                ax.text(val + 1, bar.get_y() + bar.get_height()/2, f'{val:.1f}%', 
                        va='center', fontsize=10)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 時間分析タブの修正
        with tab4:
            st.markdown('<div class="section-time">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">⏱️ 解答時間の分析</div>', unsafe_allow_html=True)
            
            # 解答時間カラムを手動で指定するオプション
            st.markdown('<div class="subsection-title">解答時間カラムの設定</div>', unsafe_allow_html=True)
            use_auto_detection = st.checkbox("解答時間カラムを自動検出する", value=True)

            # 回答時間のカラムを特定 - 改良版
            time_col = None
            if use_auto_detection:
                # 優先度の高いキーワードから検索
                priority_keywords = ['解答時間', '回答時間', '時間']
                for keyword in priority_keywords:
                    for col in df.columns:
                        if keyword in str(col):
                            time_col = col
                            st.markdown('<div class="success-box">解答時間カラムを検出しました: ' + col + '</div>', unsafe_allow_html=True)
                            break
                    if time_col:
                        break
            
            # 見つからない場合は、より広い範囲で検索（ただし「分野」は除外）
            if time_col is None:
                for col in df.columns:
                    col_str = str(col).lower()
                    if ('分' in col_str or 'time' in col_str) and '分野' not in col_str:
                        time_col = col
                        st.markdown('<div class="success-box">解答時間カラムを検出しました: ' + col + '</div>', unsafe_allow_html=True)
                        break
            
            # 回答時間のカラムが見つからない場合は位置で推測
            if time_col is None and len(df.columns) > 4:
                time_col = df.columns[4]  # 通常5列目が回答時間
                st.markdown('<div class="info-box">解答時間カラムを位置から推測しました: ' + time_col + '</div>', unsafe_allow_html=True)
            else:
                time_col = st.selectbox("解答時間カラムを選択してください", df.columns.tolist())
                st.markdown('<div class="success-box">解答時間カラムを \'' + time_col + '\' に設定しました</div>', unsafe_allow_html=True)

            if time_col is not None:
                try:
                    # 解答時間を分単位で処理
                    st.markdown('<div class="info-box">解答時間は「分」単位として処理します</div>', unsafe_allow_html=True)
                    
                    # 「〜分」形式から数値を抽出
                    if df[time_col].dtype == 'object':
                        # 正規表現で数値部分を抽出
                        df['回答時間（分）'] = df[time_col].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
                        st.markdown(f'<div class="success-box">解答時間データを正常に抽出しました。平均: {df["回答時間（分）"].mean():.2f}分</div>', unsafe_allow_html=True)
                    else:
                        # 数値型の場合はそのまま使用
                        df['回答時間（分）'] = df[time_col]
                        st.markdown(f'<div class="success-box">解答時間データを正常に取得しました。平均: {df["回答時間（分）"].mean():.2f}分</div>', unsafe_allow_html=True)
                    
                    # NaN値を0に置き換え
                    nan_count = df['回答時間（分）'].isna().sum()
                    if nan_count > 0:
                        st.markdown(f'<div class="warning-box">{nan_count}個のNaN値を0に置き換えました</div>', unsafe_allow_html=True)
                        df['回答時間（分）'] = df['回答時間（分）'].fillna(0)
                    
                    # 異常値の処理
                    st.markdown('<div class="subsection-title">異常値の処理</div>', unsafe_allow_html=True)
                    max_time_limit = st.slider("解答時間の上限（分）", min_value=1, max_value=120, value=60, step=1)
                    outliers_count = (df['回答時間（分）'] > max_time_limit).sum()

                    if outliers_count > 0:
                        # 異常値を含むデータフレームを保存
                        df_with_outliers = df.copy()
                        
                        # 異常値を除外
                        df_filtered = df[df['回答時間（分）'] <= max_time_limit].copy()
                        
                        st.markdown(f'<div class="warning-box">{outliers_count}個の異常値（{max_time_limit}分超）を除外しました</div>', unsafe_allow_html=True)
                        
                        # 除外前後の統計情報を表示
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown('<div class="subsection-title">除外前の統計</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("データ数", f"{len(df_with_outliers)}個")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("平均解答時間", f"{df_with_outliers['回答時間（分）'].mean():.1f}分")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("最大解答時間", f"{df_with_outliers['回答時間（分）'].max():.1f}分")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown('<div class="subsection-title">除外後の統計</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("データ数", f"{len(df_filtered)}個")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("平均解答時間", f"{df_filtered['回答時間（分）'].mean():.1f}分")
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                            st.metric("最大解答時間", f"{df_filtered['回答時間（分）'].max():.1f}分")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 除外したデータを表示するオプション
                        if st.checkbox("除外したデータを表示"):
                            excluded_data = df_with_outliers[df_with_outliers['回答時間（分）'] > max_time_limit]
                            st.dataframe(excluded_data)
                        
                        # 以降の分析には除外後のデータを使用
                        df = df_filtered
                    else:
                        st.markdown(f'<div class="success-box">異常値（{max_time_limit}分超）はありませんでした</div>', unsafe_allow_html=True)
                    
                    # 日付ごとの平均回答時間
                    daily_time_avg = df.groupby(date_col)['回答時間（分）'].mean()
                    
                    # 移動平均を計算（7日間）
                    time_rolling_avg = daily_time_avg.rolling(window=7, min_periods=1).mean()
                    
                    # 日付ごとの平均回答時間グラフ
                    st.markdown('<div class="subsection-title">日付ごとの平均解答時間</div>', unsafe_allow_html=True)

                    # 日付ごとの平均解答時間を計算
                    try:
                        # 日付ごとのグループ化が正しく行われているか確認
                        daily_time_avg = df.groupby(date_col)['回答時間（分）'].mean()
                        
                        # データが存在するか確認
                        if len(daily_time_avg) > 0:
                            # 移動平均を計算（7日間）
                            time_rolling_avg = daily_time_avg.rolling(window=7, min_periods=1).mean()
                            
                            # グラフ描画
                            fig, ax = plt.subplots(figsize=(10, 6))
                            ax.plot(daily_time_avg.index, daily_time_avg.values, label='日次平均時間', marker='o')
                            ax.plot(time_rolling_avg.index, time_rolling_avg.values, label='7日移動平均', linewidth=2)
                            ax.set_ylabel('解答時間（分）')
                            ax.set_xlabel('学習日')
                            ax.legend()
                            ax.grid(True, alpha=0.3)
                            plt.tight_layout()
                            st.pyplot(fig)
                            
                            # 日付ごとの解答時間データを表示
                            st.markdown('<div class="subsection-title">日付ごとの解答時間データ</div>', unsafe_allow_html=True)
                            time_daily_data = pd.DataFrame({
                                '日付': daily_time_avg.index,
                                '問題数': df.groupby(date_col).size().values,
                                '平均解答時間（分）': [f"{val:.1f}" for val in daily_time_avg.values],
                                '7日移動平均（分）': [f"{val:.1f}" for val in time_rolling_avg.values]
                            })
                            
                            # 日付を見やすい形式に変換
                            time_daily_data['日付'] = time_daily_data['日付'].dt.strftime('%Y-%m-%d')
                            
                            # 最新の日付が上に来るように並べ替え
                            time_daily_data = time_daily_data.sort_values('日付', ascending=False)
                            
                            # 表を表示
                            st.dataframe(time_daily_data)
                        else:
                            st.markdown('<div class="warning-box">解答時間のデータが十分ではありません。</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="error-box">解答時間グラフの生成中にエラーが発生しました: {str(e)}</div>', unsafe_allow_html=True)
                    st.write("エラーの詳細:", e)
                    
                    # 分野ごとの平均回答時間
                    category_time_avg = df.groupby(category_col)['回答時間（分）'].mean().sort_values(ascending=False)
                    
                    # 分野ごとの平均回答時間を表形式で表示
                    st.markdown('<div class="subsection-title">分野ごとの平均解答時間</div>', unsafe_allow_html=True)
                    time_stats_df = pd.DataFrame({
                        '分野': category_time_avg.index,
                        '平均解答時間（分）': [f"{val:.1f}" for val in category_time_avg.values]
                    })
                    st.dataframe(time_stats_df)
                    
                    # 回答時間の統計情報
                    st.markdown('<div class="subsection-title">解答時間の統計情報</div>', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    
                    # 実際の値を使用
                    mean_time = df['回答時間（分）'].mean()
                    min_time = df['回答時間（分）'].min()
                    max_time = df['回答時間（分）'].max()
                    
                    with col1:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric("平均解答時間", f"{mean_time:.1f}分")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col2:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric("最短解答時間", f"{min_time:.1f}分")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col3:
                        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                        st.metric("最長解答時間", f"{max_time:.1f}分")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 解答時間の分布
                    st.markdown('<div class="subsection-title">解答時間の分布</div>', unsafe_allow_html=True)
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.hist(df['回答時間（分）'], bins=20, alpha=0.7)
                    ax.set_xlabel('解答時間（分）')
                    ax.set_ylabel('頻度')
                    ax.grid(True, alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                except Exception as e:
                    st.markdown(f'<div class="error-box">回答時間の分析中にエラーが発生しました: {str(e)}</div>', unsafe_allow_html=True)
                    st.write("エラーの詳細:", e)
            else:
                st.markdown('<div class="info-box">解答時間のデータが見つかりませんでした。</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # AI分析コメント機能
        def generate_ai_analysis(df, score_col, date_col, category_col, time_col):
            """学習データに基づいたAI分析コメントを生成する関数"""
            comments = []
            
            # 全体の傾向分析
            overall_avg = df[score_col].mean() * 100
            if overall_avg >= 80:
                comments.append(f"全体の平均正答率は{overall_avg:.1f}%で非常に良好です。応用情報技術者試験に必要な知識をしっかり身につけています。")
            elif overall_avg >= 60:
                comments.append(f"全体の平均正答率は{overall_avg:.1f}%で良好です。さらに得点を伸ばすために苦手分野を重点的に学習しましょう。")
            else:
                comments.append(f"全体の平均正答率は{overall_avg:.1f}%です。基礎的な部分から復習することをお勧めします。")
            
            # 最近の傾向分析
            if len(df) >= 10:
                recent_df = df.sort_values(date_col, ascending=False).head(10)
                recent_avg = recent_df[score_col].mean() * 100
                overall_avg = df[score_col].mean() * 100
                
                if recent_avg > overall_avg + 5:
                    comments.append(f"最近10問の平均正答率は{recent_avg:.1f}%で、全体平均より{recent_avg-overall_avg:.1f}%高くなっています。学習の成果が出ています！")
                elif recent_avg < overall_avg - 5:
                    comments.append(f"最近10問の平均正答率は{recent_avg:.1f}%で、全体平均より{overall_avg-recent_avg:.1f}%低くなっています。疲れが出ているかもしれません。休息も大切にしましょう。")
            
            # 苦手分野の分析
            category_avg = df.groupby(category_col)[score_col].mean() * 100
            worst_categories = category_avg.sort_values().head(3)
            if len(worst_categories) > 0:
                worst_cat_names = ", ".join([f"{cat}({avg:.1f}%)" for cat, avg in worst_categories.items()])
                comments.append(f"苦手な分野は {worst_cat_names} です。これらの分野を重点的に学習することで全体の正答率向上が期待できます。")
            
            # 得意分野の分析
            best_categories = category_avg.sort_values(ascending=False).head(3)
            if len(best_categories) > 0:
                best_cat_names = ", ".join([f"{cat}({avg:.1f}%)" for cat, avg in best_categories.items()])
                comments.append(f"得意な分野は {best_cat_names} です。これらの分野の知識を活かして関連分野の学習も進めましょう。")
            
            # 解答時間の分析
            if 'time_col' in locals() and '回答時間（分）' in df.columns:
                avg_time = df['回答時間（分）'].mean()
                if avg_time > 30:
                    comments.append(f"平均解答時間は{avg_time:.1f}分です。解答のスピードを上げるために、基本的な知識の定着を図りましょう。")
                elif avg_time < 10:
                    comments.append(f"平均解答時間は{avg_time:.1f}分と速いです。解答の正確性も確認しながら進めましょう。")
            
            # 学習ペースの分析
            study_days = len(df[date_col].unique())
            total_questions = len(df)
            if study_days > 0:
                questions_per_day = total_questions / study_days
                if questions_per_day >= 10:
                    comments.append(f"1日平均{questions_per_day:.1f}問と良いペースで学習を続けています。このペースを維持しましょう。")
                elif questions_per_day < 5:
                    comments.append(f"1日平均{questions_per_day:.1f}問です。可能であれば学習量を増やすことを検討してみてください。")
            
            # 学習の継続性分析
            if study_days > 1:
                date_diff = (df[date_col].max() - df[date_col].min()).days
                if date_diff > 0:
                    continuity = study_days / date_diff
                    if continuity >= 0.7:
                        comments.append("学習の継続性が高く、素晴らしいです。継続は力なりです！")
                    elif continuity <= 0.3:
                        comments.append("学習の間隔が空いています。定期的な学習習慣を作ることで効果が高まります。")
            
            return comments

        # AIコメント表示部分を追加
        with tab5:
            st.markdown('<div class="section-ai">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">🤖 AI分析</div>', unsafe_allow_html=True)
            
            if st.button("AI分析を実行"):
                with st.spinner("分析中..."):
                    ai_comments = generate_ai_analysis(df, score_col, date_col, category_col, time_col)
                    
                    # コメントを表示
                    st.markdown('<div class="subsection-title">AI分析コメント</div>', unsafe_allow_html=True)
                    for i, comment in enumerate(ai_comments):
                        st.markdown(f'<div class="info-box">{comment}</div>', unsafe_allow_html=True)
                    
                    # 総合アドバイス
                    st.markdown('<div class="subsection-title">総合アドバイス</div>', unsafe_allow_html=True)
                    overall_avg = df[score_col].mean() * 100
                    
                    if overall_avg >= 80:
                        st.markdown('<div class="success-box">現在の学習状況は非常に良好です。このまま模擬試験などで実践的な問題にも取り組んでみましょう。</div>', unsafe_allow_html=True)
                    elif overall_avg >= 60:
                        st.markdown('<div class="warning-box">基礎はできていますが、まだ改善の余地があります。苦手分野を中心に学習を続けましょう。</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-box">基礎的な部分から見直す必要があります。テキストを再度確認し、基本概念の理解を深めましょう。</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="info-box">「AI分析を実行」ボタンをクリックすると、学習データに基づいた詳細な分析とアドバイスが表示されます。</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.markdown(f'<div class="error-box">エラーが発生しました: {str(e)}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info-box">CSVファイルをアップロードしてください。</div>', unsafe_allow_html=True) 