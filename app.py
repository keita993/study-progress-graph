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
            for col in df.columns:
                # バイト列に変換して文字化けパターンを検出
                col_bytes = str(col).encode('unicode_escape')
                
                # 学習日カラムの検出
                if b'\\u' in col_bytes and (b'w' in col_bytes or b'K' in col_bytes):
                    column_mapping[col] = '学習日'
                # 出題カラムの検出
                elif b'\\u' in col_bytes and (b'o' in col_bytes or b'T' in col_bytes):
                    column_mapping[col] = '出題'
                # 分野カラムの検出
                elif b'\\u' in col_bytes and len(col) <= 2:
                    column_mapping[col] = '分野'
                # 解答時間カラムの検出
                elif b'\\u' in col_bytes and b'\\u' in col_bytes:
                    column_mapping[col] = '解答時間'
                # 正答率カラムの検出
                elif b'\\u' in col_bytes and b'\\u' in col_bytes and any(c in str(col) for c in ['率', '％', '%']):
                    column_mapping[col] = '正答率'
                # 回答カラムの検出
                elif b'\\u' in col_bytes and any(c in str(col) for c in ['答', '解']):
                    column_mapping[col] = '回答'
            
            # カラム名を修正
            if column_mapping:
                df = df.rename(columns=column_mapping)
                st.success("文字化けしたカラム名を修正しました")
        
        # 必要なカラムを特定
        date_col = None
        category_col = None
        score_col = None
        
        # 学習日カラムを検出
        for col in df.columns:
            if '学習日' in col or '日付' in col or '日時' in col:
                date_col = col
                break
        
        # 分野カラムを検出
        for col in df.columns:
            if '分野' in col or 'カテゴリ' in col or '項目' in col:
                category_col = col
                break
        
        # 正答率カラムを検出
        for col in df.columns:
            if '正答率' in col or '正解率' in col or '得点率' in col:
                score_col = col
                break
        
        # カラムが見つからない場合は選択させる
        if date_col is None:
            # カラム名を表示用に整形
            display_columns = [f"{i}: {col}" for i, col in enumerate(df.columns)]
            selected_index = st.selectbox("学習日のカラムを選択してください", options=range(len(df.columns)), format_func=lambda x: display_columns[x])
            date_col = df.columns[selected_index]

        if category_col is None:
            display_columns = [f"{i}: {col}" for i, col in enumerate(df.columns)]
            selected_index = st.selectbox("分野のカラムを選択してください", options=range(len(df.columns)), format_func=lambda x: display_columns[x])
            category_col = df.columns[selected_index]

        if score_col is None:
            display_columns = [f"{i}: {col}" for i, col in enumerate(df.columns)]
            selected_index = st.selectbox("正答率のカラムを選択してください", options=range(len(df.columns)), format_func=lambda x: display_columns[x])
            score_col = df.columns[selected_index]
        
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
        fig, ax = plt.figure(figsize=(10, 6)), plt.gca()
        ax.plot(daily_avg.index, daily_avg.values, label='日次正答率')
        ax.plot(rolling_avg.index, rolling_avg.values, label='7日移動平均', linewidth=2)
        ax.set_ylabel('正答率 (%)')
        ax.set_xlabel('学習日')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        # 分野ごとの平均正答率グラフ
        st.header("分野ごとの平均正答率")
        category_avg_sorted = category_avg.sort_values(ascending=False)
        st.bar_chart(category_avg_sorted)
        
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
        
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("CSVファイルをアップロードしてください。") 