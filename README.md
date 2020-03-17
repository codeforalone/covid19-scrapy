# covid19-scrapy

## このツールについて

このツールは愛知県の新型コロナ感染対策サイト用のデータを自動生成するために作成したものです。
データソースは愛知県のホームページで以下のデータを生成することができます。

## データソース

https://www.pref.aichi.jp/soshiki/kenkotaisaku/novel-coronavirus.html

の以下のデータを元に自動生成します。

- 県内発生事例一覧表
- 愛知県内検査状況
- 愛知県内感染者内訳

https://www.pref.aichi.jp/soshiki/

のニュース記事

## 生成できるデータ

東京の新型コロナ感染対策サイトのデータに合わせてjsonデータを生成します。
現在対応しているデータは以下のデータです

- patients
- patients_summary
- inspections
- inspections_summary


## 実行

```
docker-compose run scrapy
```
で/dataフォルダにデータを生成します。

## 環境変数について

`CODE4NAGOYA=True`を設定すると Code for Nagoyaさんのhttps://stopcovid19.code4.nagoya 向けのデータを
そうでない場合は https://stopcovid19.aichi-info.net/ 向けのデータを生成します。

## 以下雑記

とここまで書いたところで愛知県が新型コロナ対策サイトを設立しサイト構成も変わりました。
inspectionsはpdfからHTMLに変わっているのでデータ取りやすくなってますね。

もはや存在意義もなくなりましたが、せっかくコメント書いたり整理したりしたので一式おいておきます。

PDFからデータをCSVに変換する tabula
データの扱いがものすごく楽になる panda
github上でdockerコンテナを使った定期実行ができる Github Actions

素晴らしいツールのおかげで、昔と比べてScraping環境もものすごく楽になりました。
以前であれば環境作るだけでも大変でしたね。



