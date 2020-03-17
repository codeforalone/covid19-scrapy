import glob
import os
import re

from datetime import datetime
from datetime import timedelta

import tabula
import pandas as pd
import json
from distutils.util import strtobool


CODE4NAGOYA = strtobool(os.environ['CODE4NAGOYA'])
print(CODE4NAGOYA)
DATE_SUFFIX = None
if CODE4NAGOYA:
    DATE_SUFFIX = 'T08:00:00.000Z'
else:
    DATE_SUFFIX = 'T00:00:00+09:00'


def get_update_date():
    """
    最終更新日。仮で現在日時
    
    Returns
    -------
    date_range : str
        %Y/%m/%d %H:%M:%Sの日付文字列
    """
    dt_now = datetime.now()
    return dt_now.strftime("%Y/%m/%d %H:%M:%S")

def get_date_range(df, date_col_name, date_format):
    """
    Dataframeから日付範囲の配列を返す
    
    Parameters
    ----------
    df : pandas.DataFrame
        処理対象のデータフレーム
    date_col_name : str
        日付
    date_format : str
        日付フォーマット

    Returns
    -------
    date_range : str array
        Dataframeの指定列の日付範囲を連続で
        YYYY/MM/DDT00:00:00+09:00
    date_range : str array
        Dataframeの指定列の日付範囲を連続で
        YYYY/MM/DDT00:00:00+09:00
    """
    date_range = []
    start = datetime.strptime(df[date_col_name][0], date_format)
    end = datetime.strptime(df.iloc[-1][date_col_name], date_format)

    for n in range((end - start).days + 1):
        date = start + timedelta(n)
        date_range.append(date.strftime(date_format) + DATE_SUFFIX)
        last_date = date.strftime("%Y/%m/%d %H:%M")

    return date_range, last_date

def pdf_to_csv(download_path):
    """
    パス文字列で指定されたフォルダの最新のPDFファイルをDataframeで返す
    
    Parameters
    ----------
    download_path : str
        パス文字列

    Returns
    -------
    df : pandas.DataFrame
        PDFファイルから生成したDataframe
    """
    # 指定フォルダから最新ファイルを取得
    list_of_files = glob.glob(download_path)
    latest_pdf_file = max(list_of_files, key=os.path.getctime)
    # tabulaでCSVに変換
    latest_csv_file = latest_pdf_file.replace('.pdf', '.csv')
    tabula.convert_into(latest_pdf_file, latest_csv_file, pages="all", output_format="csv")
    # pandas
    df = pd.read_csv(latest_csv_file)

    return df

def patients_data_prep_c4n(df):
    """
    Dataframeを整形して欲しい形式に整形する
    
    Parameters
    ----------
    df : pandas.DataFrame
        PDFファイルから生成したDataframe

    Returns
    -------
    df_out : pandas.DataFrame
        欲しいデータ形式に整形したDataframe
    """
    df['date'] = pd.to_datetime('2020年' + df['発表日'], format='%Y年%m月%d日')
    df['発表日'] = df['date'].dt.strftime('%Y-%m-%d') + DATE_SUFFIX
    df['w'] = df['date'].dt.dayofweek
    # pythonは 0-6 月-日 1/26は日で6
    # phpは  0-6 日-土 1/26は日で0
    # 言語によって違う。使っていないみたいなのでとりあえずこのまま。
    df['short_date'] =  df['date'].dt.strftime('%m/%d')
    df['date'] =  df['date'].dt.strftime('%Y-%m-%d')
    # 備考欄から末尾の数字を除去
    df['備考'] =  df['備考'].str.extract('(.*)\d+')
    # NaNは―に置き換え
    df_out = df
    df_out.fillna('―', inplace=True)

    return df_out

def patients_data_prep(df):
    """
    Dataframeを整形して欲しい形式に整形する
    
    Parameters
    ----------
    df : pandas.DataFrame
        PDFファイルから生成したDataframe

    Returns
    -------
    df_out : pandas.DataFrame
        欲しいデータ形式に整形したDataframe
    """
    # 年代・性別は分離して別項目にする、月日は2020年を付与して年月日にする
    df_converted = pd.concat([ df['年代・性別'].str.extract('(.*)(男性|女性)'), pd.to_datetime('2020年' + df['発表日'], format='%Y年%m月%d日') ], axis=1)
    df_converted.columns = ['年代', '性別', 'date']
    # リリース日にYYYY/MM/DDT00:00:00+09:00を設定
    df_converted['リリース日'] = df_converted['date'].dt.strftime('%Y-%m-%d') + DATE_SUFFIX
    # 存在しない項目を仮埋め
    df_empty = pd.DataFrame([['―','―']]*len(df))
    df_empty.columns = ['曜日','退院日']
    # 東京の形式に合わせて整形
    df_out = pd.concat([df_converted['リリース日'], df['住居地'], df_empty['曜日'], df_converted['年代'], df_converted['性別'], df_empty['退院日'], df_converted['date'].dt.strftime('%Y-%m-%d'), df['国籍'], df['接触状況'], df['備考'] ], axis=1)
    df_out.rename(columns={'住居地':'居住地'}, inplace=True)
    df_out.rename(columns={'退院日':'退院'}, inplace=True)
    # NaNは―に置き換え
    df_out.fillna('―', inplace=True)

    return df_out

def get_patients_summary(df_out, count_key, date_range):
    """
    Dataframeからサマリデータにする
    
    Parameters
    ----------
    df_out : pandas.DataFrame
        欲しいデータ形式に整形したDataframe
    count_key : str
        集計する列
    date_range: str array
        日付データにする日付範囲のarray

    Returns
    -------
    summary_data : array
        サマリデータをJSON形式で出力するためのデータ
    """
    # 指定のキーでgroupbyして日の件数を集計
    df_count = df_out.groupby(count_key).count()
    summary_data = []

    for date_key in date_range:
        date_summary = {}
        # 指定日に値がない場合でも0件として追加
        date_summary['日付'] = date_key
        date_summary['小計'] = 0
        if date_key in df_count.index:
            date_summary['小計'] = int(df_count['date'].loc[date_key])
            summary_data.append(date_summary)
    
    return summary_data

def inspections_data_prep(df):
    """
    Dataframeを整形して欲しい形式に整形する
    
    Parameters
    ----------
    df : pandas.DataFrame
        PDFファイルから生成したDataframe

    Returns
    -------
    df_out : pandas.DataFrame
        欲しいデータ形式に整形したDataframe
    """
    # 最初の3行はマージ
    #0    1月30日(木)     NaN     NaN
    #1         NaN     618      27
    #2   ~2月29日(土)     NaN     NaN
    df.at[1, '検査日'] = df.at[2, '検査日']
    df.drop(df.index[[0, 2]], inplace=True)
    df = df[df['検査日'].str.contains('月')]
    # 件数が0の場合に-で表示されているので0にする
    df.loc[df['陽性者数(人)'] == '-', '陽性者数(人)'] = 0
    # 〇月〇日から%Y-%m-%dの日付文字列へ、月日は年月日表記へ
    date_temp = df['検査日'].str.extract(r'(\d+月\d+日)\(\S+\)$')
    date_df = pd.concat([df, pd.to_datetime('2020年' + date_temp[0], format='%Y年%m月%d日') ], axis=1)
    date_df.rename(columns={0:'date'}, inplace=True)
    date_df['リリース日'] = date_df['date'].dt.strftime('%Y-%m-%d') + DATE_SUFFIX

    # CSVから読み込んだ内容に以下の2列を追加
    #  リリース日 %Y-%m-%dT00:00:00+09:00'
    #  date %Y-%m-%d
    df_out = pd.concat([date_df['リリース日'], date_df['date'].dt.strftime('%Y-%m-%d'), df], axis=1)
    df_out.reset_index(inplace=True)

    return df_out

def get_inspections_summary(df_out, column_key, date_range):
    """
    Dataframeからサマリデータにする
    
    Parameters
    ----------
    df_out : pandas.DataFrame
        欲しいデータ形式に整形したDataframe
    column_key : str
        %Y-%m-%dの日付データの列名
    date_range: str array
        日付データにする日付範囲のarray

    Returns
    -------
    summary_data : array
        サマリデータをJSON形式で出力するためのデータ
    summary_data_labels : array
        サマリデータをJSON形式で出力するためのデータ
    """
    df_out.set_index(column_key, inplace=True)
    summary_data = {}
    summary_data_inspections = []
    summary_data_positives = []
    summary_data_labels = []

    for date_key in date_range:
        if date_key in df_out.index.values:
            date_str = df_out['date'].loc[date_key]
            pattern = r"(\d+)-(\d+)-(\d+)"
            match_obj = re.match(pattern, date_str)
            label_str = match_obj.group(2) + '/' + match_obj.group(3)

            summary_data_inspections.append(int(df_out['検査件数(件)'].loc[date_key]))
            summary_data_positives.append(int(df_out['陽性者数(人)'].loc[date_key]))
            summary_data_labels.append(label_str)

    summary_data['検査件数(件)'] = summary_data_inspections
    summary_data['陽性者数(人)'] = summary_data_positives

    return summary_data, summary_data_labels
        


if __name__ == '__main__':
    data_file_name = os.path.join('/data', 'data.json')
    output = {}

    # 患者数
    output['patients'] = {}
    output['patients']['date'] = get_update_date()
    output['patients']['data'] = []

    output['patients_summary'] = {}
    output['patients_summary']['date'] = get_update_date()
    output['patients_summary']['data'] = []

    output['contacts'] = {}
    output['contacts']['date'] = get_update_date()
    output['contacts']['data'] = []

    output['querents'] = {}
    output['querents']['date'] = get_update_date()
    output['querents']['data'] = []

    output['discharges_summary'] = {}
    output['discharges_summary']['date'] = get_update_date()
    output['discharges_summary']['data'] = []

    # 検査数
    output['inspections'] = {}
    output['inspections']['date'] = get_update_date()
    output['inspections']['data'] = []

    output['inspections_summary'] = {}
    output['inspections_summary']['date'] = get_update_date()
    output['inspections_summary']['data'] = {}

    output['better_patients_summary'] = {}
    output['better_patients_summary']['date'] = get_update_date()
    output['better_patients_summary']['data'] = {}

    # main summary
    output['lastUpdate'] = get_update_date()
    output['main_summary'] = {}


    #####################################################################
    # patients
    #####################################################################
    df_out = None
    if CODE4NAGOYA:
        df_out = patients_data_prep(pdf_to_csv('patients/*.pdf'))
    else:
        df_out = patients_data_prep_c4n(pdf_to_csv('patients/*.pdf'))

    df_out = patients_data_prep_c4n(pdf_to_csv('patients/*.pdf'))
    date_range, last_date = get_date_range(df_out, 'date', '%Y-%m-%d')

    # patients
    output['patients']['date'] = last_date
    for df_value in df_out.to_dict(orient='index').values():
        output['patients']['data'].append(df_value)

    # patients_summary
    output['patients_summary']['date'] = last_date
    if CODE4NAGOYA:
        output['patients_summary']['data'].extend(get_patients_summary(df_out, '発表日', date_range))
    else:
        output['patients_summary']['data'].extend(get_patients_summary(df_out, 'リリース日', date_range))
    

    #####################################################################
    # inspections
    #####################################################################
    df_out = inspections_data_prep(pdf_to_csv('inspections/*.pdf'))
    date_range, last_date = get_date_range(df_out, 'date', '%Y-%m-%d')

    # inspections
    output['inspections']['date'] = last_date
    for df_value in df_out.to_dict(orient='index').values():
        output['inspections']['data'].append(df_value)

    # inspections_summary
    output['inspections_summary']['date'] = last_date
    summary_data, summary_label = get_inspections_summary(df_out, 'リリース日', date_range)
    output['inspections_summary']['data'] = summary_data
    output['inspections_summary']['labels'] = summary_label

    #####################################################################
    # output data
    #####################################################################
    with open(data_file_name, 'w') as fp:
        json.dump(output, fp,indent=4, ensure_ascii=False)


