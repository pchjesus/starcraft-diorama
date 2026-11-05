# 스타크래프트 1 원본 그래픽 가져오기

이 문서는 **사용자 본인의 게임에서 추출한 스프라이트를 로컬에서** 적용하기 위한 가이드다. 원본 게임 데이터는 GitHub에 포함하지 않는다.

## 원본 포맷

스타1/Brood War 그래픽은 대체로 `.grp` 프레임과 256색 팔레트로 구성된다. 원본 유닛의 방향 전환, 별도 포탑, 걷기/대기 애니메이션에는 게임의 `iscript.bin` 정보가 함께 쓰인다.

- 원본 StarCraft Remastered CASC나 Classic MPQ에서 추출하는 오픈소스 도구: [broodwar-live/assets-pipeline](https://github.com/broodwar-live/assets-pipeline)
- `.grp` 이미지 변환용 오픈소스 도구: [sjoblomj/irongrp](https://github.com/sjoblomj/irongrp)
- 전체 유닛/건물과 오버레이 관계: [scmJS 게임 데이터 문서](https://docs.scmjs.dev/game-data/how-units-are-drawn/)

`assets-pipeline`은 **유닛 PNG/APNG 추출**을 지원하나 건물 스프라이트 추출은 해당 도구의 현재 지원 범위 밖이므로 별도 추출이 필요하다.

## 준비할 파일

원본 게임에서 변환해 얻은 PNG/APNG를 **폴더 하나로** 선택하면 된다. `output/terran/marine/frames/marine_0000.png`처럼 하위 폴더여도 된다. 아래 그래픽 일부만 있어도 나머지는 기존 3D 모델로 표시한다.

| 대상 | 자동 인식 이름 예시 |
|---|---|
| 마린 | `marine.png`, `marine_0000.png`, `marine.apng` |
| 시즈탱크 차체 | `tank.png`, `siege_tank_0000.png` |
| 탱크 포탑 | `tankturr.png`, `tank_turret.png` (선택, 별도 포탑) |
| SCV | `scv.png`, `scv_0000.png`, `scv.apng` |
| 팩토리 | `factory.png` |
| 머신샵 | `machine_shop.png`, `machineshop.png` |
| 아머리 | `armory.png` |
| 서플라이 디폿 | `supply_depot.png`, `supply.png` |
| 공사 프레임 | `bunker_frame.png`, `bunker.png` |

마린 놀람 프레임을 `marine_react.png`로 추가하면 놀람 시 자동 전환한다.

## GRP를 직접 추출한 경우

1. 원본 `.grp` 파일과 해당 원본 게임의 `.wpe`, `.pal` 또는 `.pcx` 팔레트를 `original_sources/`로 복사한다.
2. 저장소 최상위에서 다음을 실행한다.

```powershell
py tools/prepare_original_assets.py original_sources --out local_assets
py -m http.server 8000
```

3. `http://localhost:8000/original.html`을 열면 `local_assets/manifest.json`이 자동 적용된다.

이 변환기는 `.grp`의 첫 프레임을 투명 PNG로 만들며 8~15의 팀 색상 영역은 식별을 위해 임시 청록색으로 표시한다. 추출된 파일이 실제 원본인지 여부는 각 사용자가 제공한 소스에 달려 있다. **게임 자체의 MPQ/CASC를 직접 여는 도구는 아니다.** 게임 데이터 아카이브에서는 먼저 GRP/팔레트를 추출해야 한다.

## 제한 사항

- 원본 2D 스프라이트를 세계 좌표에 맞춰 화면에 합성하는 방식으로, 완전한 3D 원본 모델이 아니다.
- 현재의 GRP 변환은 첫 프레임 기준. 스타1의 모든 방향/걷기/대기 동작을 그대로 재생하려면 프레임과 `iscript.bin` 맵핑을 추가 개발해야 한다.
- 별도 탱크 포탑 스프라이트가 없을 때는 3D 동작이 대체되거나 고정된 탱크 스프라이트가 보일 수 있다.
- 공개 Pages의 브라우저 보안 모델상 **사용자 로컬 게임 폴더는 자동으로 읽을 수 없다**. 폴더 선택으로 한 번 접근을 허용해야 한다.
- 음악·효과음은 이번 범위에서 제외한다.