import pandas as pd
import matplotlib
matplotlib.use('Agg')  # バックエンドを明示的に設定

# フォント設定を強化
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
        fig, ax = create_figure(figsize=(10, 6))
        ax.plot(daily_avg.index, daily_avg.values, label='日次正答率')
        ax.plot(rolling_avg.index, rolling_avg.values, label='7日移動平均', linewidth=2)
        ax.set_ylabel('正答率 (%)')
        ax.set_xlabel('学習日')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()  # レイアウトを調整
        st.pyplot(fig)
        
        # 分野ごとの平均正答率グラフ
        st.header("分野ごとの平均正答率")
        # Streamlitのbar_chartではなく、matplotlibを使用
        fig, ax = create_figure(figsize=(10, 6))
        category_avg_sorted = category_avg.sort_values(ascending=False)
        category_avg_sorted.plot(kind='bar', ax=ax)
        ax.set_ylabel('正答率 (%)')
        ax.set_xlabel('分野')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()  # レイアウトを調整
        st.pyplot(fig)
        
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
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("CSVファイルをアップロードしてください。") 