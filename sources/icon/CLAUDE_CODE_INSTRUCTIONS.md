# Rescue App アイコン導入指示

このフォルダの画像を既存の rescue-app に導入してください。

1. リポジトリ構成を確認し、画像を適切な公開ディレクトリ（例: assets/icons/）に配置する。
2. index.html の head に favicon (32px) と apple-touch-icon (180px) を設定する。既存設定があれば更新し重複させない。
3. PWA manifest があれば icons に 192px と 512px の画像を登録する。なければ既存の設計に合わせて manifest を作り index.html にリンクする。start_url と scope は GitHub Pages の /rescue-app/ 配下で動くよう相対パスを優先する。
4. 既存の service worker があればキャッシュ更新を検討し、古いアイコンが残らないようにする。
5. アイコンの外観は変更せず、ファイル名やパスは実装に合わせて調整してよい。
6. 変更したファイルと動作確認方法を報告する。

注意: iOS のホーム画面アイコンは端末側キャッシュの影響で再追加が必要な場合がある。
