import urllib
import html5lib
from bs4 import BeautifulSoup
import os
import datetime
import re
import json
from googletrans import Translator




def get_news(target_url, search_keyword):
    """
    愛知県のページからニュース一覧を取得する
    https://www.pref.aichi.jp/soshiki/
    
    Parameters
    ----------
    target_url : str
        取得する愛知県のページのURL
    search_keyword : str
        検索キーワード(タイトルにこのキーワードがあるものを収集)

    Returns
    -------
    news_items_dict : dict
        ニュースのURLをキーにしたニュースアイテム一覧
    """
    news_items_dict = {}
    html = urllib.request.urlopen(target_url)
    soup = BeautifulSoup(html, "html5lib")

    # <li><span class="span_a">2020年3月11日更新</span><span class="span_b lineclamp"><a href="/soshiki/san-kagi/waka-followup.html">【わかしゃち奨励賞】これまでの受賞者について、現在の研究内容を紹介するWebページを新たに開設しました！</a></span></li>
    for list_item in soup.find_all("li"):
        link_item = list_item.find('a')

        if search_keyword in link_item.text:
            news_item = {}

            update_text = list_item.find('span').text
            pattern = r"(\d+)年(\d+)月(\d+)日"
            match_obj = re.match(pattern, update_text)
            update_date = datetime.date(int(match_obj.group(1)), int(match_obj.group(2)), int(match_obj.group(3)))

            # ニュースアイテム
            news_item['date'] = update_date.strftime('%Y/%m/%d')
            news_item['dt'] = update_date
            news_item['url'] = urllib.parse.urljoin(target_url, link_item.get("href"))
            news_item['text'] = link_item.text
            news_items_dict[news_item['url']] = news_item

    return news_items_dict

def convert_news(news_items, max_count):
    """
    JSON出力用のニュースデータを整形する
    
    Parameters
    ----------
    news_items : array
        ニュースアイテム一覧
    max_count : int
        最大出力件数

    Returns
    -------
    output_news_items : array
        JSON形式で出力するニュースデータ
    """
    count=0
    output_news_items = []
    # 日付ソート
    for item in sorted(news_items, key=lambda x:x['dt'], reverse=True):
        del(item['dt'])
        output_news_items.append(item)
        count+=1
        if count >= max_count:
            break

    return output_news_items

def generate_i18_config(news_items):
    """
    WhatsNew.i18n.jsonをgoogletranslateで自動生成する
    
    Parameters
    ----------
    news_items : array
        ニュースアイテム一覧

    Returns
    -------
    news_i18_items : array
        WhatsNew.i18n.jsonの内容
    """
    news_i18_items = {}
    news_i18_items['ja'] = {}
    news_i18_items['en'] = {}

    whats_news_ja = "最新のお知らせ"
    whats_news_en = "What's new"
    news_i18_items['ja'][whats_news_ja] = {}
    news_i18_items['ja'][whats_news_ja] = whats_news_ja
    news_i18_items['en'][whats_news_ja] = {}
    news_i18_items['en'][whats_news_ja] = whats_news_en

    translator = Translator()
    for item in news_items:
        ja_text = item['text']
        en_text = translator.translate(ja_text, src='ja' ,dest='en')

        news_i18_items['ja'][ja_text] = {}
        news_i18_items['ja'][ja_text] = ja_text
        news_i18_items['en'][ja_text] = {}
        news_i18_items['en'][ja_text] = en_text.text

    return news_i18_items


if __name__ == '__main__':
    # 出力
    output = {}
    output['newsItems'] = []

    # 愛知県のサイトの新着とプレスリリースからニュース記事を取得
    news_items_dict = {}
    news_items_dict.update(get_news("https://www.pref.aichi.jp/soshiki/list1-1.html", 'コロナ'))
    news_items_dict.update(get_news("https://www.pref.aichi.jp/soshiki/list7-1.html", 'コロナ'))

    # 重複除いてソートしたものを指定件数ニュース記事として作成
    output['newsItems'] = convert_news(news_items_dict.values(), 5)
    news_file = os.path.join('/data', 'news.json')
    with open(news_file, 'w') as fp:
        json.dump(output, fp,indent=4, ensure_ascii=False)

    # 多言語対応のWhatsNew.i18n.json
    output_i18_file = os.path.join('/data', 'WhatsNew.i18n.json')
    news_i18_items = generate_i18_config(output['newsItems'])
    with open(output_i18_file, 'w') as fp:
        json.dump(news_i18_items, fp,indent=4, ensure_ascii=False)

