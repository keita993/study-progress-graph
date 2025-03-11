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
import subprocess
import sys

# scipyのインポート部分を修正
try:
    from scipy import stats
except ImportError:
    st.error("scipyモジュールがインストールされていません。requirements.txtに'scipy'を追加してください。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="応用情報技術者試験 学習分析",
    page_icon="📊"
)

# カスタムCSSを修正 - ボーダーを削除
st.markdown("""
<style>
h1, h2, h3, h4, h5, h6 {
    border-bottom: none;
    width: auto;
    padding: 0;
    margin: 0;
    line-height: 1.2;
    display: block;
    position: static;
}

/* 疑似要素を削除 */
h1::after, h2::after, h3::after, h4::after, h5::after, h6::after {
    content: none;
}

/* h1のみ余白を追加 */
h1 {
    margin-bottom: 15px;
}

/* Streamlitのデフォルトスタイルを上書き */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
    margin-top: 0.5em !important;
    margin-bottom: 0.3em !important;
}

/* Streamlitのマークダウンコンテナのパディングを調整 */
.stMarkdown {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* レスポンシブデザイン用のスタイル */
@media (max-width: 768px) {
    /* スマホ表示時のフォントサイズ調整 */
    h1 {
        font-size: 1.5rem !important;
    }
    h2 {
        font-size: 1.3rem !important;
    }
    h3 {
        font-size: 1.1rem !important;
    }
    
    /* グラフのサイズ調整 */
    .stPlot {
        width: 100% !important;
        height: auto !important;
    }
    
    /* データフレームの表示調整 */
    .dataframe {
        font-size: 0.8rem !important;
        width: 100% !important;
        overflow-x: auto !important;
    }
    
    /* ボタンのサイズ調整 */
    .stButton > button {
        width: 100% !important;
        padding: 0.5rem !important;
    }
    
    /* メトリックのサイズ調整 */
    .stMetric {
        font-size: 0.9rem !important;
    }
    
    /* カラムレイアウトの調整 */
    .row-widget.stHorizontal {
        flex-direction: column !important;
    }
    
    /* 余白の調整 */
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("応用情報技術者試験 学習分析")

# ファイルアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    try:
        # バイナリモードでファイルを読み込む
        file_content = uploaded_file.read()
        
        # エンコーディングを検出
        try:
            import chardet
            result = chardet.detect(file_content)
            detected_encoding = result['encoding']
            
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
        
        # 分析処理
        st.header("概要")
        overall_avg = df[score_col].mean()
        st.metric("全体の平均正答率", f"{overall_avg*100:.1f}%")

        # 日付ごとの平均正答率を計算
        daily_avg = df.groupby(date_col)[score_col].mean() * 100

        # 移動平均を計算（7日間）
        rolling_avg = daily_avg.rolling(window=7, min_periods=1).mean()

        # 日付ごとの平均解答時間を計算（解答時間データがある場合）
        if '回答時間（分）' in df.columns:
            daily_time_avg = df.groupby(date_col)['回答時間（分）'].mean()
            # 移動平均を計算（7日間）
            time_rolling_avg = daily_time_avg.rolling(window=7, min_periods=1).mean()
        else:
            daily_time_avg = None
            time_rolling_avg = None

        # 日付ごとの平均正答率グラフ
        st.header("日付ごとの平均正答率")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(daily_avg.index, daily_avg.values, label='Daily Accuracy')
        ax.plot(rolling_avg.index, rolling_avg.values, label='7-day Moving Average', linewidth=2)
        ax.set_ylabel('Accuracy (%)')
        ax.set_xlabel('Study Date')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        
        # 日付ごとの平均正答率（表）部分もそのまま
        st.header("日付ごとの平均正答率（表）")
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

        # CSVダウンロードボタンを追加
        csv = daily_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="日付ごとのデータをCSVでダウンロード",
            data=csv,
            file_name='daily_accuracy.csv',
            mime='text/csv',
        )
        
        # 解答時間の分析部分を移動する
        # 「日付ごとの平均正答率（表）」の後に移動し、「分野ごとの平均正答率グラフ」の前に配置

        # 解答時間カラムを手動で指定するオプション
        st.header("解答時間の分析")
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
                    break
                if time_col:
                    break
            
            # 見つからない場合は、より広い範囲で検索（ただし「分野」は除外）
            if time_col is None:
                for col in df.columns:
                    col_str = str(col).lower()
                    if ('分' in col_str or 'time' in col_str) and '分野' not in col_str:
                        time_col = col
                        break
            
            # 回答時間のカラムが見つからない場合は位置で推測
            if time_col is None and len(df.columns) > 4:
                time_col = df.columns[4]  # 通常5列目が回答時間
        else:
            time_col = st.selectbox("解答時間カラムを選択してください", df.columns.tolist())

        if time_col is not None:
            try:
                # 解答時間を分単位で処理
                
                # 「〜分」形式から数値を抽出
                if df[time_col].dtype == 'object':
                    # 正規表現で数値部分を抽出
                    df['回答時間（分）'] = df[time_col].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
                else:
                    # 数値型の場合はそのまま使用
                    df['回答時間（分）'] = df[time_col]
                
                # NaN値を0に置き換え
                nan_count = df['回答時間（分）'].isna().sum()
                if nan_count > 0:
                    st.warning(f"{nan_count}個のNaN値を0に置き換えました")
                    df['回答時間（分）'] = df['回答時間（分）'].fillna(0)
                
                # 異常値の処理
                max_time_limit = st.slider("解答時間の上限（分）", min_value=1, max_value=120, value=30, step=1)
                outliers_count = (df['回答時間（分）'] > max_time_limit).sum()

                if outliers_count > 0:
                    # 異常値を含むデータフレームを保存
                    df_with_outliers = df.copy()
                    
                    # 異常値を除外
                    df_filtered = df[df['回答時間（分）'] <= max_time_limit].copy()
                    
                    st.warning(f"{outliers_count}個の異常値（{max_time_limit}分超）を除外しました")
                    
                    # 除外前後の統計情報を表示
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("除外前の統計")
                        st.metric("データ数", f"{len(df_with_outliers)}個")
                        st.metric("平均解答時間", f"{df_with_outliers['回答時間（分）'].mean():.1f}分")
                        st.metric("最大解答時間", f"{df_with_outliers['回答時間（分）'].max():.1f}分")
                    
                    with col2:
                        st.subheader("除外後の統計")
                        st.metric("データ数", f"{len(df_filtered)}個")
                        st.metric("平均解答時間", f"{df_filtered['回答時間（分）'].mean():.1f}分")
                        st.metric("最大解答時間", f"{df_filtered['回答時間（分）'].max():.1f}分")
                    
                    # 除外したデータを表示するオプション
                    if st.checkbox("除外したデータを表示"):
                        excluded_data = df_with_outliers[df_with_outliers['回答時間（分）'] > max_time_limit]
                        st.dataframe(excluded_data)
                    
                    # 以降の分析には除外後のデータを使用
                    df = df_filtered
                else:
                    st.success(f"異常値（{max_time_limit}分超）はありませんでした")
                
                # 日付ごとの平均回答時間
                daily_time_avg = df.groupby(date_col)['回答時間（分）'].mean()
                
                # 移動平均を計算（7日間）
                time_rolling_avg = daily_time_avg.rolling(window=7, min_periods=1).mean()
                
                # 日付ごとの平均回答時間グラフ
                st.subheader("日付ごとの平均解答時間")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(daily_time_avg.index, daily_time_avg.values, label='Daily Average Time')
                ax.plot(time_rolling_avg.index, time_rolling_avg.values, label='7-day Moving Average', linewidth=2)
                ax.set_ylabel('Response Time (minutes)')
                ax.set_xlabel('Study Date')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
                
                # 分野ごとの平均回答時間
                category_time_avg = df.groupby(category_col)['回答時間（分）'].mean().sort_values(ascending=False)
                
                # 分野ごとの平均回答時間を表形式で表示
                st.subheader("分野ごとの平均解答時間")
                time_stats_df = pd.DataFrame({
                    '分野': category_time_avg.index,
                    '平均解答時間（分）': [f"{val:.1f}" for val in category_time_avg.values]
                })
                st.dataframe(time_stats_df)
                
                # 回答時間の統計情報
                st.subheader("解答時間の統計情報")
                col1, col2, col3 = st.columns(3)
                
                # 実際の値を使用
                mean_time = df['回答時間（分）'].mean()
                min_time = df['回答時間（分）'].min()
                max_time = df['回答時間（分）'].max()
                
                with col1:
                    st.metric("平均解答時間", f"{mean_time:.1f}分")
                with col2:
                    st.metric("最短解答時間", f"{min_time:.1f}分")
                with col3:
                    st.metric("最長解答時間", f"{max_time:.1f}分")
                
                # 解答時間の分布
                st.subheader("解答時間の分布")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(df['回答時間（分）'], bins=20, alpha=0.7)
                ax.set_xlabel('Response Time (minutes)')
                ax.set_ylabel('Frequency')
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                st.pyplot(fig)
                
            except Exception as e:
                st.error(f"回答時間の分析中にエラーが発生しました: {str(e)}")
                st.write("エラーの詳細:", e)
        else:
            st.info("解答時間のデータが見つかりませんでした。")
        
        # 分野ごとの分析部分を修正
        st.header("分野ごとの分析")

        # 分野ごとの詳細データを表示（正答率が高い順に並び替え）
        category_count = df.groupby(category_col).size()
        category_avg_sorted = df.groupby(category_col)[score_col].mean().sort_values(ascending=False)
        category_stats = pd.DataFrame({
            '分野': category_avg_sorted.index,
            '問題数': [category_count[cat] for cat in category_avg_sorted.index],
            '正答率': [f"{val:.1f}%" for val in category_avg_sorted.values]
        })

        # 表を表示
        st.dataframe(category_stats)

        # 学習の進捗状況
        st.header("学習の進捗状況")
        total_questions = len(df)
        study_days = len(df[date_col].unique())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総問題数", f"{total_questions}問")
        with col2:
            st.metric("学習日数", f"{study_days}日")
        with col3:
            st.metric("1日平均問題数", f"{total_questions/study_days:.1f}問")
        
        # 分野の文字化けを修正する部分を追加
        if category_col in df.columns:
            # 分野名に文字化けがある場合は修正
            unique_categories = df[category_col].unique()
            category_mapping = {}
            
            for cat in unique_categories:
                cat_str = str(cat)
                # 文字化けしている可能性がある場合
                if '\\u' in repr(cat_str) or len(cat_str) <= 2:
                    # 既知の分野名と照合
                    known_categories = {
                        'セキュリティ': ['セキュリティ', 'セキュ', 'セ'],
                        'システムアーキテクチャ': ['システムアーキテクチャ', 'アーキ', 'ア'],
                        'プロジェクトマネジメント': ['プロジェクトマネジメント', 'プロマネ', 'プ'],
                        'サービスマネジメント': ['サービスマネジメント', 'サービス', 'サ'],
                        'システム戦略': ['システム戦略', '戦略', '戦'],
                        '経営戦略': ['経営戦略', '経営', '経'],
                        'システム開発': ['システム開発', '開発', '開'],
                        '組込システム開発': ['組込システム開発', '組込', '組'],
                        'データベース': ['データベース', 'DB', 'デ'],
                        'ネットワーク': ['ネットワーク', 'NW', 'ネ'],
                        'システム監査': ['システム監査', '監査', '監']
                    }
                    
                    # 文字列の類似度で最も近い分野を見つける
                    for known_cat, aliases in known_categories.items():
                        for alias in aliases:
                            if alias in cat_str or cat_str in alias:
                                category_mapping[cat] = known_cat
                                break
            
            # マッピングを適用
            if category_mapping:
                df[category_col] = df[category_col].map(lambda x: category_mapping.get(x, x))
        
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

        # AI分析コメント部分を修正
        st.header("AI分析コメント")

        # ボタンを削除し、自動的に分析を実行
        with st.spinner("分析中..."):
            ai_comments = generate_ai_analysis(df, score_col, date_col, category_col, time_col)
            
            for i, comment in enumerate(ai_comments):
                st.info(comment)
            
            # 総合アドバイス
            st.subheader("総合アドバイス")
            overall_avg = df[score_col].mean() * 100
            
            if overall_avg >= 80:
                st.success("現在の学習状況は非常に良好です。このまま模擬試験などで実践的な問題にも取り組んでみましょう。")
            elif overall_avg >= 60:
                st.warning("基礎はできていますが、まだ改善の余地があります。苦手分野を中心に学習を続けましょう。")
            else:
                st.error("基礎的な部分から見直す必要があります。テキストを再度確認し、基本概念の理解を深めましょう。")

        # 学習進捗の総合評価セクションを最後に追加
        st.header("学習進捗の総合評価")

        try:
            # トレンド分析のための準備
            # 条件チェックを修正 - 解答時間データの有無を確認
            has_time_data = '回答時間（分）' in df.columns and daily_time_avg is not None and len(daily_time_avg) > 0
            
            # データが十分にあるかチェック
            if len(daily_avg) >= 3:  # 最低3日分のデータがあれば分析可能
                # 移動平均データを使用
                recent_rolling_avg = rolling_avg.tail(min(7, len(rolling_avg)))  # 利用可能なデータを最大7日分使用
                
                # 正答率のトレンド分析
                x_acc = range(len(recent_rolling_avg))
                slope_acc, _, _, _, _ = stats.linregress(x_acc, recent_rolling_avg.values)
                
                # 評価を表示
                col1, col2 = st.columns(2)
                
                with col1:
                    if slope_acc > 0.5:
                        st.success("📈 正答率が上昇傾向にあります！")
                    elif slope_acc < -0.5:
                        st.error("📉 正答率が下降傾向にあります")
                    else:
                        st.info("📊 正答率は安定しています")
                
                # 解答時間のトレンド分析（データがある場合のみ）
                if has_time_data:
                    # 解答時間データを取得
                    recent_time_rolling_avg = time_rolling_avg.tail(min(7, len(time_rolling_avg)))
                    
                    # 解答時間のトレンド分析（十分なデータがある場合）
                    if len(recent_time_rolling_avg) >= 3:
                        with col2:
                            x_time = range(len(recent_time_rolling_avg))
                            slope_time, _, _, _, _ = stats.linregress(x_time, recent_time_rolling_avg.values)
                            
                            if slope_time < -0.2:
                                st.success("⏱️ 解答時間が短縮傾向にあります！")
                            elif slope_time > 0.2:
                                st.warning("⏱️ 解答時間が増加傾向にあります")
                            else:
                                st.info("⏱️ 解答時間は安定しています")
                        
                        # 総合評価（解答時間データがある場合）
                        if slope_acc > 0.5 and slope_time < -0.2:
                            st.success("👍 正答率が上昇し、解答時間も短縮されています！学習がとても効果的に進んでいます！")
                        elif slope_acc > 0.5:
                            st.success("👍 正答率が上昇しています。理解度が高まっています！")
                        elif slope_time < -0.2:
                            st.success("👍 解答時間が短縮されています。解答スピードが向上しています！")
                        elif slope_acc < -0.5 and slope_time > 0.2:
                            st.error("📝 正答率が下降し、解答時間も増加しています。学習方法の見直しが必要かもしれません。")
                        elif slope_acc < -0.5:
                            st.warning("📝 正答率が下降しています。基礎的な部分の復習を検討してください。")
                        elif slope_time > 0.2:
                            st.warning("⏰ 解答時間が増加しています。問題の理解に時間がかかっているかもしれません。")
                        else:
                            st.info("📚 学習は安定して進んでいます。継続的な学習を続けましょう。")
                    else:
                        # 解答時間データが少ない場合
                        with col2:
                            st.info("⏱️ 解答時間の傾向分析には少なくとも3日分のデータが必要です")
                        
                        # 正答率のみで評価
                        if slope_acc > 0.5:
                            st.success("👍 正答率が上昇しています。理解度が高まっています！")
                        elif slope_acc < -0.5:
                            st.warning("📝 正答率が下降しています。基礎的な部分の復習を検討してください。")
                        else:
                            st.info("📚 学習は安定して進んでいます。継続的な学習を続けましょう。")
                else:
                    # 解答時間データがない場合
                    with col2:
                        st.info("⏱️ 解答時間のデータがありません")
                    
                    # 正答率のみで評価
                    if slope_acc > 0.5:
                        st.success("👍 正答率が上昇しています。理解度が高まっています！")
                    elif slope_acc < -0.5:
                        st.warning("📝 正答率が下降しています。基礎的な部分の復習を検討してください。")
                    else:
                        st.info("📚 学習は安定して進んでいます。継続的な学習を続けましょう。")
                
                # 詳細な分析結果
                with st.expander("詳細な分析結果を見る"):
                    st.write(f"移動平均の正答率変化: {slope_acc:.2f}%/日")
                    
                    if has_time_data and len(recent_time_rolling_avg) >= 3:
                        st.write(f"移動平均の解答時間変化: {slope_time:.2f}分/日")
                        
                        # 解答時間のトレンド評価を追加
                        if slope_time < -0.5:
                            st.success("解答時間は大幅に短縮されています。知識の定着が進んでいる証拠です！")
                        elif slope_time < -0.2:
                            st.success("解答時間は徐々に短縮されています。学習の成果が出ています。")
                        elif slope_time > 0.5:
                            st.warning("解答時間が大幅に増加しています。問題の難易度が上がったか、集中力が低下している可能性があります。")
                        elif slope_time > 0.2:
                            st.warning("解答時間がやや増加しています。問題をじっくり考えるようになったか、難易度が上がっている可能性があります。")
                        else:
                            st.info("解答時間は安定しています。一定のペースで解答できています。")
                        
                        # 正答率と解答時間の相関
                        if len(recent_rolling_avg) == len(recent_time_rolling_avg):
                            corr = pd.Series(recent_rolling_avg.values).corr(pd.Series(recent_time_rolling_avg.values))
                            st.write(f"正答率と解答時間の相関係数: {corr:.2f}")
                            
                            if corr < -0.5:
                                st.write("👉 解答時間が短くなるほど正答率が高くなる傾向があります。知識が定着してきている証拠です！")
                            elif corr > 0.5:
                                st.write("👉 解答時間をかけるほど正答率が高くなる傾向があります。じっくり考えることで正解率が上がっています。")
        except Exception as e:
            st.error(f"トレンド分析中にエラーが発生しました: {str(e)}")
            st.error(f"エラーの詳細: {type(e).__name__}")
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("CSVファイルをアップロードしてください。") 