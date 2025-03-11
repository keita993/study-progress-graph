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

# ページ設定
st.set_page_config(
    page_title="応用情報技術者試験 学習分析",
    page_icon="📊"
)

st.title("応用情報技術者試験 学習分析")

# サンプルデータの作成
def generate_sample_data():
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    progress = np.cumsum(np.random.randint(1, 10, size=30))
    return pd.DataFrame({'日付': dates, '進捗': progress})

# グラフ作成関数
def create_progress_graph(data):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(data['日付'], data['進捗'], marker='o', linestyle='-')
    ax.set_title('学習進捗グラフ')
    ax.set_xlabel('日付')
    ax.set_ylabel('進捗（累積）')
    ax.grid(True)
    return fig

# サイドバーでデータ入力方法を選択
data_input = st.sidebar.radio(
    "データ入力方法を選択してください：",
    ("CSVファイルをアップロード", "サンプルデータを使用")
)

if data_input == "サンプルデータを使用":
    data = generate_sample_data()
    
    # データの表示
    st.subheader("サンプルデータ")
    st.dataframe(data)
    
    # グラフの表示
    st.subheader("サンプル進捗グラフ")
    fig = create_progress_graph(data)
    st.pyplot(fig)
else:
    # メインのCSVアップロード部分を使用
    st.info("以下のCSVアップロード機能を使用してください。")

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
        
        # 分析処理
        st.header("概要")
        overall_avg = df[score_col].mean()
        st.metric("全体の平均正答率", f"{overall_avg*100:.1f}%")
        
        # 日付ごとの平均正答率を計算
        daily_avg = df.groupby(date_col)[score_col].mean() * 100
        
        # 移動平均を計算（7日間）
        rolling_avg = daily_avg.rolling(window=7, min_periods=1).mean()
        
        # 分野ごとの平均正答率を計算
        category_avg = df.groupby(category_col)[score_col].mean() * 100
        
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
        
        # 日付ごとの平均正答率グラフの後に追加
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
        
        # 分野ごとの平均正答率グラフ
        st.header("分野ごとの平均正答率")
        fig, ax = plt.subplots(figsize=(10, 6))
        category_avg_sorted = category_avg.sort_values(ascending=False)
        
        # 分野名を英語に変換（文字化け対策）- 改善版
        category_mapping = {
            'セキュリティ': 'Security',
            'システムアーキテクチャ': 'System Architecture',
            'プロジェクトマネジメント': 'Project Management',
            'サービスマネジメント': 'Service Management',
            'システム戦略': 'System Strategy',
            '経営戦略': 'Management Strategy',
            'システム開発': 'System Development',
            '組込システム開発': 'Embedded Systems',
            '情報システム開発': 'Information System Development',
            'データベース': 'Database',
            'ネットワーク': 'Network',
            'システム監査': 'System Audit',
            # 追加の分野名マッピング
            '情報セキュリティ': 'Information Security',
            'マネジメント': 'Management',
            'テクノロジ': 'Technology',
            'ストラテジ': 'Strategy',
            'システム構成要素': 'System Components',
            'ソフトウェア開発': 'Software Development',
            'ハードウェア': 'Hardware',
            'ヒューマンインタフェース': 'Human Interface',
            'マルチメディア': 'Multimedia',
            'データベース': 'Database',
            'ネットワーク': 'Network',
            'セキュリティ': 'Security',
            'システム開発技術': 'System Development Technology',
            'ソフトウェア開発管理技術': 'Software Development Management',
            'プロジェクトマネジメント': 'Project Management',
            'サービスマネジメント': 'Service Management',
            'システム監査': 'System Audit',
            '組込みシステム': 'Embedded Systems',
            '経営': 'Business Management',
            '企業と法務': 'Corporate and Legal Affairs',
            '経営戦略': 'Management Strategy',
            '技術戦略': 'Technology Strategy',
            'システム戦略': 'System Strategy',
            '開発技術': 'Development Technology',
            'ソフトウェア開発': 'Software Development',
            'ハードウェア': 'Hardware',
            'データベース': 'Database',
            'ネットワーク': 'Network',
            'セキュリティ': 'Security',
            'システム構築': 'System Construction',
            'システム企画': 'System Planning',
            'システム運用': 'System Operation',
            'サービス提供': 'Service Provision',
            'プロジェクト管理': 'Project Management'
        }
        
        # 部分一致で分野名を検出する関数
        def map_category(cat):
            cat_str = str(cat)
            # 完全一致の場合
            if cat_str in category_mapping:
                return category_mapping[cat_str]
            
            # 部分一致の場合
            for jp_cat, en_cat in category_mapping.items():
                if jp_cat in cat_str or cat_str in jp_cat:
                    return en_cat
            
            # マッチしない場合はそのまま返す
            return cat_str
        
        # インデックスを英語に変換（文字化け対策）- 改善版
        category_avg_sorted_en = category_avg_sorted.copy()
        category_avg_sorted_en.index = [map_category(cat) for cat in category_avg_sorted.index]
        
        # 英語ラベルでグラフ描画
        ax.bar(range(len(category_avg_sorted_en)), category_avg_sorted_en.values)
        ax.set_ylabel('Accuracy (%)')
        ax.set_xlabel('Category')
        plt.xticks(range(len(category_avg_sorted_en)), category_avg_sorted_en.index, rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)
        
        # 元の日本語名と英語名の対応表を表示
        st.caption("分野名対応表:")
        mapping_df = pd.DataFrame({
            '日本語分野名': category_avg_sorted.index,
            '英語分野名': [map_category(cat) for cat in category_avg_sorted.index],
            '正答率': [f"{val:.1f}%" for val in category_avg_sorted.values]
        })
        st.dataframe(mapping_df)
        
        # 分野ごとの問題数
        category_count = df.groupby(category_col).size().sort_values(ascending=False)
        
        # 分野ごとの問題数と正答率表示
        st.header("分野ごとの問題数と正答率")
        category_stats = category_count.reset_index().rename(columns={category_col: '分野', 0: '問題数'})
        category_percent = category_avg_sorted.reset_index()
        category_percent['正答率'] = category_percent[score_col].map('{:.1f}%'.format)
        
        # データフレームをマージ
        category_stats_merged = pd.merge(
            category_stats, 
            category_percent[[category_col, '正答率']], 
            left_on='分野', 
            right_on=category_col,
            how='left'
        )
        
        if category_col != '分野':
            category_stats_merged = category_stats_merged.drop(columns=[category_col])
        
        st.dataframe(category_stats_merged)
        
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
                st.success("分野名の文字化けを修正しました")
        
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
                        st.success(f"解答時間カラムを検出しました: {col}")
                        break
                if time_col:
                    break
            
            # 見つからない場合は、より広い範囲で検索（ただし「分野」は除外）
            if time_col is None:
                for col in df.columns:
                    col_str = str(col).lower()
                    if ('分' in col_str or 'time' in col_str) and '分野' not in col_str:
                        time_col = col
                        st.success(f"解答時間カラムを検出しました: {col}")
                        break
            
            # 回答時間のカラムが見つからない場合は位置で推測
            if time_col is None and len(df.columns) > 4:
                time_col = df.columns[4]  # 通常5列目が回答時間
                st.info(f"解答時間カラムを位置から推測しました: {time_col}")
        else:
            time_col = st.selectbox("解答時間カラムを選択してください", df.columns.tolist())
            st.success(f"解答時間カラムを '{time_col}' に設定しました")

        if time_col is not None:
            try:
                # 解答時間を分単位で処理
                st.info("解答時間は「分」単位として処理します")
                
                # 「〜分」形式から数値を抽出
                if df[time_col].dtype == 'object':
                    # 正規表現で数値部分を抽出
                    df['回答時間（分）'] = df[time_col].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
                    st.success(f"解答時間データを正常に抽出しました。平均: {df['回答時間（分）'].mean():.2f}分")
                else:
                    # 数値型の場合はそのまま使用
                    df['回答時間（分）'] = df[time_col]
                    st.success(f"解答時間データを正常に取得しました。平均: {df['回答時間（分）'].mean():.2f}分")
                
                # NaN値を0に置き換え
                nan_count = df['回答時間（分）'].isna().sum()
                if nan_count > 0:
                    st.warning(f"{nan_count}個のNaN値を0に置き換えました")
                    df['回答時間（分）'] = df['回答時間（分）'].fillna(0)
                
                # 異常値の処理
                max_time_limit = st.slider("解答時間の上限（分）", min_value=1, max_value=120, value=60, step=1)
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
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("CSVファイルをアップロードしてください。") 