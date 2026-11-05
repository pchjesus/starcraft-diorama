# StarCraft Diorama — Factory After Hours

**StarCraft: Brood War**에서 영감을 받은 비상업적 팬 디오라마. 평화로운 밤의 테란 군수공장에서 탱크가 천천히 나오면 마린이 깜짝 놀라고, 전차는 포탑으로 마린을 슥 본 뒤 머쓱하게 후진한다. SCV는 완성되지 않는 시설을 끝없이 공사한다.

## 실행

- [v0.9 원본 스프라이트 불러오기](./original.html) — 개인이 보유한 게임 데이터에서 추출한 스프라이트를 로컬에서 선택한다. 파일 미선택 시 기존 3D가 나타난다.
- [v0.7 3D/CC0 그래픽 시험](./3d.html) — 기존 시험판 보존.
- [v0.3 Canvas 안정판](./index.html) — WebGL 없이 실행.
- 공개 Pages: https://pchjesus.github.io/starcraft-diorama/original.html

**원본 게임 파일은 GitHub에 포함하지 않는다.** 실제 원본 그래픽을 적용하려면 개인 게임 설치 데이터에서 추출한 `.grp` + 팔레트 또는 PNG/APNG가 필요하다. **StarCraft: Remastered의 고해상도 그래픽을 3D 텍스처로 직접 입힌 버전이 아니다.** 원본 2D 스프라이트를 3D 좌표에 맞춰 배치하는 2.5D 방식이다.

## v0.9 — 여러 프레임 지원

- 로컬의 번호가 붙은 PNG (`marine_0000.png`, `marine_0001.png`…)를 모두 그룹화해 읽는다.
- 클래식 `.grp` 파일에서 최대 **192개 프레임(기본값)**까지 추출해 PNG 시퀀스와 매니페스트를 만든다. `--max-frames`로 한도를 변경할 수 있다.
- 매니페스트에 **행동별 프레임 순서**(`idle`, `move`, `look`, `react`, `work`)와 FPS를 지정하면 장면 동작과 맞춰 재생된다. 일시정지 시 프레임도 멈춘다.
- 마린 2명, 탱크 등장·후진·포탑 회전, SCV 무한 공사 및 주변 자연환경은 기존과 동일하게 유지한다.
- 그래픽팩에 없는 오브젝트는 자동으로 기존 3D 모델을 보여준다.

**주의:** `.grp`의 17방향 회전 프레임을 단순히 순환하면 캐릭터가 제자리에서 회전하는 것처럼 보인다. 게임의 정확한 애니메이션 흐름에는 `iscript.bin`과 오버레이 데이터가 필요하다. v0.9는 자동 복원기가 아니라 **행동별 프레임 선택·재생 기능**까지 구현한 단계다. 기본 상태는 첫 묶음의 8번 방향(가능한 경우)을 유지한다.

## 내 게임에서 준비한 파일을 넣는 방법

1. 스스로 보유한 스타1 설치 데이터에서 `.grp`와 팔레트 파일을 추출하거나 PNG/APNG로 변환한다. 게임 아카이브 자체의 추출 도구는 포함하지 않는다.
2. 저장소 최상위에서 실행:

   ```bash
   python tools/prepare_original_assets.py original_sources --out local_assets
   python -m http.server 8000
   ```

3. 브라우저에서 `http://localhost:8000/original.html`을 연다. `local_assets/manifest.json`이 자동으로 로드된다. 또는 `original.html`의 **원본 스프라이트 선택** 버튼으로 이미지 폴더를 지정한다.
4. 수동으로 행동별 프레임을 정하려면 [애니메이션 설정 예시](docs/ANIMATION_MANIFEST.md)를 참고한다.

그래픽 팩을 GitHub에 커밋하지 않도록 `local_assets/`·`original_sources/` 등이 `.gitignore`에 지정되어 있다.

## 검증

- `python tests/test_v09.py`: 합성 클래식 GRP 17방향 변환·출력 개수 제한·PNG 시퀀스·기존 정적 PNG 호환.
- `python tests/browser_v09.py`: Chromium에서 PNG 시퀀스 불러오기·행동별 프레임 선택·로우폴리 전환·오류 시 복귀.
- `node --check`: 페이지 JavaScript 문법.
- 현재 테스트 컨테이너에서는 WebGL2가 차단되어 **v0.9 전체 장면의 GPU 시각 회귀 테스트는 미확인**. 기존 `index.html`과 `3d.html`은 수정하지 않았다.

## 저작권

StarCraft와 관련 이미지·그래픽은 Blizzard Entertainment의 저작물이다. 이 비공식·비상업 프로젝트에는 원본 게임 에셋을 포함하지 않는다. 공식 팬 영상 정책만으로 원본 스프라이트의 공개 GitHub 재배포 권한이 부여되는 것은 아니다. 음악 및 효과음은 포함하지 않는다.