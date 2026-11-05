# StarCraft Diorama — Original Sprites v0.8

평화로운 브루드워풍 야간 테란 군수공장 디오라마. **공장 밖으로 천천히 나오는 탱크 → 깜짝 놀라는 마린 → 탱크가 포탑을 슥 돌림 → 머쓱하게 후진**하는 35초 무한 루프. SCV는 영원히 완성되지 않는 벙커를 공사한다.

## 실행 버전

- [v0.8 원본 스프라이트 가져오기](./original.html) — 스타1 원본 파일을 **내 브라우저에서만** 적용하는 로더. 스프라이트가 없으면 기존 3D 모델 자동 표시.
- [v0.7 3D / CC0 혼합 실험](./3d.html) — 이전 버전 보존.
- [v0.3 2D 안정판](./index.html) — WebGL 필요 없음.

## 진짜 스타1 그래픽 적용 방법

**원본 스프라이트 데이터는 포함되어 있지 않습니다.** 직접 보유·설치한 스타크래프트 게임에서 꺼낸 원본 스프라이트를 쓰도록 준비되어 있습니다. 파일 하나하나 이름을 바꿀 필요는 없습니다.

### 빠른 방법 — 브라우저에서 폴더 선택

1. 본인 게임 설치 데이터에서 추출한 PNG/APNG 폴더를 준비합니다. 유닛 추출은 [broodwar-live/assets-pipeline](https://github.com/broodwar-live/assets-pipeline) 사용 가능. 건물은 별도 추출이 필요할 수 있습니다.
2. `original.html`을 실행합니다.
3. 왼쪽 아래 **원본 스프라이트 선택** → 추출 폴더 한 번 선택.
4. `marine_0000.png`, `scv.apng`, `siege_tank_0000.png`, `factory.png` 등의 이름을 자동으로 인식하여 해당 위치에 표시합니다. 버튼으로 원본/3D를 전환할 수 있습니다.

### 완전한 로컬팩 — `.grp` 직접 변환

스타1의 `.grp` 스프라이트 파일과 팔레트 파일을 게임 데이터에서 추출했다면, Python 표준 라이브러리만으로 로컬팩을 생성할 수 있습니다.

```bash
python tools/prepare_original_assets.py original_sources --palette original_sources/units.wpe --out local_assets
python -m http.server 8000
```

`http://localhost:8000/original.html`을 열면 `local_assets/manifest.json`을 자동으로 읽습니다. 추출 프로그램, 지원 파일 형식, 주의점은 [docs/ORIGINAL_ASSETS.md](docs/ORIGINAL_ASSETS.md)에 정리되어 있습니다.

## 현재 구현 범위

- 마린·SCV·시즈탱크·팩토리·머신샵·아머리·서플라이 디폿·미완성 벙커를 파일명/폴더명으로 인식.
- 원본 파일이 있으면 동일 위치의 로우폴리 모델을 숨기고 스프라이트를 렌더링.
- 포탑 스프라이트(`tankturr` 등)를 별도로 제공하면 탱크 차체 위에서 포탑 회전 적용.
- 해당 원본이 없는 구성 요소는 기존 3D 모델로 표시.
- 조용한 숲과 절벽, 건물 조명, 효과음 없는 35초 루프 유지.
- 화면과 원본 그래픽은 **2.5D 합성 방식**. 스타1 원본 그래픽이 실제 3D 모델로 변환되는 건 아님.
- 현재 GRP 변환기는 **첫 프레임**만 기본으로 출력. 전체 스타1 애니메이션(`iscript`) 동기화는 미구현.

## 저작권/공개 저장소

- 스타크래프트의 원본 스프라이트와 게임 데이터는 Blizzard Entertainment의 저작물입니다.
- 이 저장소에는 게임 데이터가 포함되지 않습니다. `local_assets/`, `original_sources/` 및 MPQ/CASC 등은 `.gitignore`로 제외합니다.
- 블리자드의 팬 **영상** 정책이 원본 그래픽 파일의 공개 재배포 권한까지 주는 건 아닙니다. 개인이 원본을 추출해 로컬에서 불러오는 방식으로 사용합니다.
- 이 프로젝트는 비공식 팬 제작물이며 음악·효과음은 포함하지 않습니다.

### 참고 문헌

Blizzard Entertainment. (n.d.). *Blizzard video policy*. https://www.blizzard.com/en-gb/legal/2068564f-f427-4c1c-8664-c107c90b34d5/blizzard-video-policy

broodwar-live. (n.d.). *BW asset extraction pipeline* [Computer software]. GitHub. https://github.com/broodwar-live/assets-pipeline

sjoblomj. (n.d.). *IronGRP* [Computer software]. GitHub. https://github.com/sjoblomj/irongrp