import urllib
import html5lib
from bs4 import BeautifulSoup
import os

def download_file(target_url, download_dir, link_title):
    """
    愛知県のぺージからコロナ関連情報を取得する
    ファイル名は元のファイル名を使用する
    
    Parameters
    ----------
    target_url : str
        ダウンロード先ページのURL
    download_dir : str
        ダウンロードしたファイルの保存先
    link_title : str
        ダウンロード対象のリンクタイトル
    """
    if not os.path.isdir(download_dir):
        os.makedirs(download_dir)

    html = urllib.request.urlopen(target_url)
    soup = BeautifulSoup(html, "html5lib")

    # <a href="/uploaded/attachment/325314.pdf">愛知県内発生事例 [PDFファイル／114KB]</a>
    for link_item in soup.find_all("a"):
        
        if link_title in link_item.text:
            file_link_path = link_item.get("href")
            print(file_link_path)
            file_name = os.path.basename(file_link_path)
            download_url = urllib.parse.urljoin(target_url, file_link_path)
            urllib.request.urlretrieve(download_url, os.path.join(download_dir, file_name))

if __name__ == '__main__':
    target_url = "https://www.pref.aichi.jp/soshiki/kenkotaisaku/novel-coronavirus.html"
    download_file(target_url, 'patients', '県内発生事例一覧表') 
    download_file(target_url, 'inspections', '愛知県内検査状況')
    download_file(target_url, 'main', '愛知県内感染者内訳')