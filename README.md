# 농마니 약초 백과

한국 산나물·약초 172가지의 생김새, 독초와 구별하는 법, 제철·손질법, 『동의보감』 등 옛 의서 기록, 최근 연구를 정리한 공개 사이트입니다.

- 사이트: https://nongmani.com/nongmani-yakcho/
- `docs/` : GitHub Pages로 공개되는 완성된 사이트 (직접 고치지 마세요. 생성기가 다시 만듭니다)
- `tools/build.py` : 사이트 생성기
- `tools/base.json` : 품목 사전(172가지)과 기본 고서 기록
- `tools/data/herbinfo/` : '농부와 심마니' 앱 약초 사전에서 내려받은 자료

다시 만들기: `cd tools && python3 build.py --base https://nongmani.com/nongmani-yakcho --out ../docs`

옛 의서의 기록과 연구를 소개할 뿐 효능을 보장하거나 치료를 권하지 않습니다.
