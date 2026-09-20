# 藤本まなと 研究者ホームページ

GitHub Pagesに配置できる、英語の静的ホームページです。
公開用HTML・CSS・画像をすべて同梱しており、初回公開にビルド作業は不要です。

## 内容

| ページ | ファイル |
| --- | --- |
| プロフィール・お知らせ・職歴・学歴 | `docs/index.html` |
| ニュース一覧・個別記事 | `docs/news.html`、`docs/news/*.html` |
| 研究内容 | `docs/research.html` |
| 研究業績 | `docs/publications.html` |
| 学会活動・受賞・所属学会 | `docs/services.html` |

英語の5つの基本ページとニュースの個別記事で構成しています。日本語ページと、言語切替リンクは削除しました。

## 手元で確認する

ZIPを解凍し、`docs/index.html` をブラウザで開いてください。
ナビゲーションと画像表示は、インターネットに接続せず確認できます。
メールや論文の外部リンクを開く場合には、対応するアプリやインターネット接続が必要です。

## GitHub Pagesで公開する

1. GitHubで新しいリポジトリを作成します。個人ホームページのURLにする場合、リポジトリ名は **自分のGitHubユーザー名.github.io** にしてください。すでにそのリポジトリがある場合は、新規作成せず既存の内容との統合を検討してください。
2. 作成したリポジトリの **Add file → Upload files** から、このZIPを解凍した中身をアップロードします。少なくとも `docs` フォルダ全体をアップロードし、`docs/index.html` という配置になっていることを確認してコミットします。ZIPファイル自体をアップロードしてもホームページにはなりません。
3. リポジトリの **Settings → Pages** を開きます。
4. **Source** を **Deploy from a branch**、**Branch** を **main**、フォルダを **/docs** に設定し、**Save** を押します。ブランチ名が異なる場合は、実際にアップロードしたブランチを選びます。
5. Pagesの画面に表示される公開URLを開きます。公開処理が完了するまで数分かかる場合があります。

公開先の例（`username` は自分のユーザー名に置き換えます）：

- 英語版：`https://username.github.io/`

以前の版をアップロード済みの場合は、リポジトリに残っている `docs/ja` も削除してください。

通常名のリポジトリでも、同じく `main /docs` を公開元に指定できます。その場合は `https://username.github.io/リポジトリ名/` 以下に表示されます。サイト内の参照は相対パスで記述しているため、どちらの形式にも対応します。

公開設定の根拠：[GitHub Pages クイックスタート](https://docs.github.com/en/pages/quickstart)、[公開元の設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

## 内容を更新する

### 少量の文章を変更する場合

`docs` 内の該当するHTMLファイルを編集してアップロードします。色・余白・文字サイズは `docs/assets/style.css` で変更できます。写真は `docs/assets/manato-fujimoto.png` です。

### 業績や共通情報をまとめて更新する場合

| 編集対象 | 内容 |
| --- | --- |
| `content/site.json` | プロフィール、研究紹介、お知らせ、職歴、学歴、学会活動など。言語別の項目は `en` を使用します |
| `content/publications.json` | 論文タイトル、著者、掲載先、年、採択状態、外部リンク |
| `content/journal-metrics.json` | 掲載誌の確認済みJournal Impact Factor、対象年、出典、確認日 |
| `scripts/build.py` | HTMLの共通構造、ページ構成 |

Python 3のある環境で、このフォルダを作業ディレクトリとして次を実行します。

```bash
python3 scripts/build.py
```

`docs` 内の英語5ページ、ニュースの個別記事、`sitemap.xml`、`robots.txt` が再生成されます。旧日本語ページが残っている場合は、生成時に削除されます。更新した `docs` をGitHubに反映すると、公開サイトが更新されます。追加のPythonパッケージは不要です。

**HTMLを直接編集した後に再生成すると、その直接編集は上書きされます。** 継続的に更新する場合は、JSONと生成スクリプトを編集元として使ってください。新しい論文を追加するときは既存の `id` を変更せず、一意の `id` と `label` を追加すると、研究紹介からの論文リンクを維持できます。

### NewsとPublicationsの論文情報を連動させる

論文情報の編集元は `content/publications.json` に一本化しています。巻・号・ページは対象論文の `venue` に入力してください。タイトル、著者、URL、採択状態、タグも同じレコードで管理します。

各Newsは `content/site.json` の `news` にある `publications` 配列で論文IDを参照します（例：`["j035"]`、`["c082", "c081"]`）。本文の `body_html` に書誌情報を複製せず、採択などの告知文章だけを保存します。`slug` は記事のURLに使います。

`python3 scripts/build.py` を実行すると、PublicationsとNewsの論文欄を同じ関数から生成します。元の論文情報を更新すれば、News側の巻・号・ページ、著者、タイトル、タグを個別に修正する必要はありません。掲載先の未確定情報をNews用に補完したり、`pp. xx-xx` を追加したりしません。存在しない論文IDを参照するとビルドを停止します。

反映されるタイミングは再生成時です。HTMLの直接編集や外部サイトの更新を監視して同期する機能ではありません。Newsの告知日と本文は、当時の告知として維持します。

## 検索エンジン・AI検索向けの設定

- `content/site.json` の `site_url` を正規の公開URLとして使用します。公開先を変更するときは、この値も更新してビルドしてください。
- Homeの説明文は `description.en`、その他のページの説明文は `page_descriptions` で管理します。
- 基本ページとNews個別記事にcanonical URL、検索結果の説明文、Open Graphメタデータ、JSON-LD構造化データを生成します。
- HomeをProfilePageとして記述し、氏名・所属・研究分野をPerson情報に整理します。本人の外部プロフィールは `profile_links` から `sameAs` として関連付けます。
- Publicationsでは、表示中の全業績のタイトル・著者・掲載情報・採択状態をItemListとScholarlyArticleで記述します。未確定の刊行日や外部評価は追加しません。
- `sitemap.xml` に基本ページとNews個別記事の正規URLを列挙し、`robots.txt` から案内します。`robots.txt` は検索・AI検索クローラーの巡回を許可する設定です。
- これらの設定は検索結果への掲載やAIによる引用を保証するものではありません。Googleの登録状況や掲載実績は、サイト所有者のSearch Consoleで確認できます。

参考：[Googleの生成AI検索向けガイド](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)、[OpenAIクローラーの仕様](https://developers.openai.com/api/docs/bots)。

## 掲載情報

2026年9月13日に確認できた公開情報をもとに初期データを作成しました。業績は学術論文38件、国際会議論文83件で、採択済み・刊行予定を含みます。国内研究会発表等は、既存の業績一覧へのリンクで案内しています。学会活動と受賞は一部を抜粋しています。

- 書誌情報の未確定ページ番号などは表示から省略しました。
- 年別見出しを設けず、学術論文・国際会議論文それぞれを新しい発行順に掲載しています。採択済み・刊行予定も同じ一覧に含め、各論文に「Accepted」を表示しています。
- 学術論文のJournal Impact Factorは、2026年に公表された2025年値に統一しています。括弧内はIFの対象年です。各論文の出版年当時の値を示すものではありません。出版社・学会の情報を優先し、必要に応じて年度が明記された外部資料を照合しています。数値から実際の確認元へ移動できます。
- Impact Factorを更新するときは、`content/journal-metrics.json` の `metric_year`（対象年）、`release_year`（公表年）、`checked_on`（確認日）と、各誌の `value`、`year`、`source_url` を更新してください。すべての `year` が `metric_year` と一致しないと再生成は停止します。`venue_name` は書誌情報冒頭の雑誌名に一致させます。対象年の値を確認できない誌は `journals` から外し、`unverified_venues` に記録します。古い値や確認日による代用はしません。未表示はIF未付与の断定ではありません。
- ISMICT 2026の役職は、公式委員会一覧の **Web Chair** を採用しています。
- 計画中の研究助成申請内容や未公開情報は掲載していません。
- 外部ページへのリンクは書誌情報の参照先です。すべての出版社サイトのアクセス可能性を保証するものではありません。

掲載元の詳細は [SOURCES.md](SOURCES.md) に記載しています。

## 動作仕様

- 公開サイトはHTML・CSSと、業績の表示切替用の短いJavaScriptで動作します。データベース、外部フォント、JavaScriptライブラリは使用していません。JavaScriptが無効でも全業績を閲覧できます。
- スマートフォン向けのレイアウトと、キーボード操作用のフォーカス表示、本文へのスキップリンクを備えています。
- 英語ページのみを公開し、言語切替は設けていません。
- この納品時点ではGitHubへのアップロード・公開は行っていません。
