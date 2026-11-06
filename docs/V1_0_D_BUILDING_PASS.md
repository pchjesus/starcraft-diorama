# StarCraft Diorama — v1.0-D building pass

## 기준 (2026-11-06)
- 개발 브랜치: `v1.0-a-arclite-tank` / PR #1
- 미병합 기준 `main`: `d0a3fdb8fd87dad1bc335b030b6c2a24a53786d2`
- 작업 파일: `3d.html`, `docs/V1_0_D_BUILDING_PASS.md`
- 원본 게임 스프라이트/텍스처는 삽입하지 않음. 사용자가 보낸 그림은 외형·실루엣 비교에만 사용.
- 현재 브라우저 실행 환경에 WebGL2 컨텍스트가 없어 **실제 렌더링 및 육안 검증 전 main 병합 금지.**

## 변경 지오메트리
| 건물 | 설계 보완 | 본체 기하 정점 수 |
|---|---|---:|
| Factory | 두 개의 비스듬한 지붕 환기 하우징, 후면 굴뚝/냉각 구조, 저층 지지대, 전면 장갑, 문 테두리 확대 | 3,726 |
| Machine Shop | 팩토리 우측의 작은 부속 장치, 연결 커플러, 회전 환풍기 받침 링, 전면 초록 제어 패널 | 1,452 |
| Armory | 기존 상자형에서 열린 중앙 녹색 링·청동 톱니·적색 배관·복수의 수직 타워 구조로 변경 | 2,847 |
| Supply Depot | 중앙 지붕 환풍기, 전면 쌍원형 팬, 붉은 보급 모듈, 낮은 초록 도크, 황검 경고바 | 2,460 |
| Bunker frame | **미수정**. SCV가 영원히 완성하지 않는 구조 보존 | 540 |

원래 건물 중심 좌표: Factory (0.55,-2.95), Shop (3.43,-2.94), Armory (-3.52,-3.42), Depot (-3.48,-0.87).
**기존 카메라/배경/건물 상대 위치/팬 회전 좌표 변경 없음.**

## 출고문 간섭 수정
- 기존 2장 슬라이딩 문은 아크라이트의 양쪽 궤도를 통과시키기 어려울 정도로 폭이 좁았음.
- 2장 → **4장 겹침식 슬라이딩 패널(좌우 각 2개)**. 닫힐 때 중앙 빈틈 없이 문을 가리고, 열릴 때 양측으로 겹쳐 이동함.
- 장면 전체 배치·공장 외부 크기를 유지하며, 문틀 안쪽 간격 조정.
- 최대 개방 시 문 패널의 안쪽 경계는 `±1.230`, 탱크 모델 좌우 반폭은 `1.144`; 수치상 여유 `0.086` 장면 단위. 단, 실제 픽셀 단위 충돌은 미검증.
- 문 개방 `6.2–7.7s` (탱크 8초 출고 시작 전), 닫힘 `29.5–31.8s` (탱크 완전 복귀 뒤).
- 탱크 출고/마린 반응/포탑 회전/머쓱한 후진 `frame()` 보간식과 35초 루프는 그대로 보존.

## 검증 결과
| 검사 | 결과 | 방법/주의 |
|---|---|---|
| 전체 스크립트 JS 문법 | PASS | `new Function(script)` |
| 변경한 네 건물 메시 유한 좌표 | PASS | NaN/Infinity = 0 |
| 메시 변환 행렬 push/pop 균형 | PASS | 각 건물 1단계 회복 |
| 벙커 및 유닛 생성 유지 | PASS | 기하 생성 검사 |
| 출고문 개방 폭/탱크 좌우 폭 | PASS (수치) | 개방 여유 `0.086` |
| 출고문 7.7초 완전 개방 | PASS (수치) | 수치 애니메이션 메시 검사 |
| 0/6.2/7.7/8/14.8/16.7/18/19.8/23/29/29.5/31.8/34.9초 | PASS (모의) | 13시점의 mock GL draw 호출·버퍼 유한 좌표 |
| 모바일 세로 390×844 / 가로 844×390 | PASS (모의) | GPU 실제 화면 아님 |
| 재생·일시정지 | PASS (모의) | 시간 정지와 버튼 상태 |
| 본체 카메라/야간 환경/프레임 루프 | PASS (코드 보존) | 원본 설정 비교 |
| **실제 WebGL2 GPU 렌더링** | **미검증** | Chromium WebGL1/2 컨텍스트 생성 불가 |
| **모바일 실기기 가독성/간섭** | **미검증** | 실제 스마트폰/브라우저 필요 |
| **GitHub Pages 배포** | **미실시** | PR 상태 유지 |

## 병합 전 육안 체크리스트
1. 실제 브라우저에서 각 시점 `3d.html?phase=8&skin=0&assets=0`, `?phase=14.8`, `?phase=18`, `?phase=23`, `?phase=29`, `?phase=34.9` 등 확인.
2. 공장 지붕 환풍기·굴뚝·문짝 겹침, 탱크 포신과 문틀 사이 간섭, 마린과 탱크 주변 접근 확인.
3. 아머리 중앙 링이 한눈에 보이는지, 서플라이 디폿 전면 팬 2개와 상부 팬이 보이는지, 머신샵이 팩토리에 붙어 있는지 확인.
4. 조명·나무·절벽·연기·반딧불, SCV 용접, 마린 놀람, 탱크 출고-후진을 실제 35초 루프에서 확인.
5. PC와 모바일 세로/가로, 재생·일시정지 확인한 후 PR #1 병합 및 Pages 배포/확인.

## 다음 단계
- v1.0-E 실제 WebGL2 렌더링 회귀/스크린샷 비교, 필요 시 지오메트리의 간섭·명도 수정.
- GPU/모바일 화면 검증 없이 PASS로 표시하거나 본 저장소의 `main`에 병합하지 말 것.

## 참고문헌 (APA 7th)
Blizzard Entertainment. (1998). *StarCraft* [Video game]. Blizzard Entertainment.

Blizzard Entertainment. (1998). *StarCraft* [Game manual]. https://ftp.blizzard.com/pub/misc/StarCraft.PDF

Liquipedia contributors. (n.d.). *Factory*. Liquipedia StarCraft Brood War Wiki. https://liquipedia.net/starcraft/Factory

Liquipedia contributors. (n.d.). *Armory*. Liquipedia StarCraft Brood War Wiki. https://liquipedia.net/starcraft/Armory

Liquipedia contributors. (n.d.). *Supply Depot*. Liquipedia StarCraft Brood War Wiki. https://liquipedia.net/starcraft/Supply_Depot
